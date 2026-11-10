import os
import json
from typing import Dict, Any
from app.models import (
    IncomingMessageRequest, 
    RouterDecisionResponse, 
    LLMClassification,
    IntentEnum,
    SentimentEnum,
    ActionEnum
)
from app.database import save_message_log

# Tenta carregar SDK do Gemini se a chave existir
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def call_llm_classification(user_text: str) -> LLMClassification:
    """
    Classifica a mensagem do cliente usando LLM com saída estruturada.
    Caso a chave da API não esteja configurada ou haja erro de rede,
    utiliza um fallback robusto baseado em heurísticas semânticas.
    """
    if GEMINI_API_KEY and GEMINI_API_KEY != "sua_chave_do_google_ai_studio_aqui":
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            prompt = f"""
            Você é o classificador central de mensageria da Blip.
            Analise a mensagem abaixo e classifique:
            1. intent: SUPORTE_TECNICO, VENDAS, CANCELAMENTO, FINANCEIRO ou OUTROS.
            2. sentiment: POSITIVO, NEUTRO ou FRUSTRADO.
            3. urgency_score: de 1 a 5 (5 sendo altíssima urgência/fúria).
            4. summary: resumo de 1 frase.

            Responda EXCLUSIVAMENTE em formato JSON com essas 4 chaves exatas:
            Mensagem: "{user_text}"
            """
            
            response = model.generate_content(prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            return LLMClassification(
                intent=IntentEnum(data["intent"]),
                sentiment=SentimentEnum(data["sentiment"]),
                urgency_score=int(data["urgency_score"]),
                summary=str(data["summary"])
            )
        except Exception as e:
            # Em caso de falha de conexão/API, ativa o motor de fallback
            pass

    # Motor de Fallback determinístico (ideal para testes locais e resiliência offline)
    text_lower = user_text.lower()
    
    if any(k in text_lower for k in ["cancelar", "cancelamento", "reembolso", "estorno", "procon"]):
        return LLMClassification(
            intent=IntentEnum.CANCELAMENTO,
            sentiment=SentimentEnum.FRUSTRADO,
            urgency_score=5,
            summary="Solicitação crítica de cancelamento ou estorno"
        )
    elif any(k in text_lower for k in ["preco", "preço", "comprar", "planos", "quanto custa", "contratar"]):
        return LLMClassification(
            intent=IntentEnum.VENDAS,
            sentiment=SentimentEnum.POSITIVO if "adorei" in text_lower else SentimentEnum.NEUTRO,
            urgency_score=3,
            summary="Interesse comercial em contratação ou tabela de preços"
        )
    elif any(k in text_lower for k in ["erro", "bug", "fora do ar", "não funciona", "nao funciona", "caiu"]):
        return LLMClassification(
            intent=IntentEnum.SUPORTE_TECNICO,
            sentiment=SentimentEnum.FRUSTRADO if "horrível" in text_lower or "urgente" in text_lower else SentimentEnum.NEUTRO,
            urgency_score=4,
            summary="Problema de indisponibilidade técnica reportado"
        )
    else:
        return LLMClassification(
            intent=IntentEnum.OUTROS,
            sentiment=SentimentEnum.NEUTRO,
            urgency_score=2,
            summary="Dúvida geral ou contato inicial"
        )

def process_and_route_message(payload: IncomingMessageRequest) -> RouterDecisionResponse:
    """
    Aplica o motor de regras de negócio sobre a classificação da IA:
    - Sentimento Frustrado OU Cancelamento -> Transbordo Humano prioritário
    - Vendas / Outros -> Atendimento automatizado com bot
    """
    # 1. Executa a análise semântica
    analysis = call_llm_classification(payload.text)
    
    # 2. Regras de Roteamento Corporativo
    if analysis.sentiment == SentimentEnum.FRUSTRADO or analysis.intent == IntentEnum.CANCELAMENTO or analysis.urgency_score >= 4:
        action = ActionEnum.HUMAN_HANDOFF
        queue = "RETENCAO_E_SUPORTE_PRIORITARIO"
        suggested_reply = (
            "Compreendo perfeitamente sua urgência e peço desculpas pelo transtorno. "
            "Estou transferindo seu atendimento agora mesmo para um especialista humano da nossa equipe."
        )
        sla_seconds = 60  # Atendimento em até 1 minuto
    elif analysis.intent == IntentEnum.VENDAS:
        action = ActionEnum.AUTO_REPLY
        queue = "SDR_IA_VENDAS"
        suggested_reply = (
            "Olá! Ficamos muito felizes com seu interesse. Nosso catálogo completo e condições especiais "
            "estão disponíveis. Gostaria de agendar uma demonstração rápida?"
        )
        sla_seconds = 0
    else:
        action = ActionEnum.AUTO_REPLY
        queue = "TRIAGEM_GERAL_BOT"
        suggested_reply = "Olá! Como posso ajudar você hoje com a nossa plataforma?"
        sla_seconds = 0

    # 3. Persistência dos dados via SQL
    save_message_log({
        "user_id": payload.user_id,
        "channel": payload.channel.value,
        "user_text": payload.text,
        "intent": analysis.intent.value,
        "sentiment": analysis.sentiment.value,
        "urgency_score": analysis.urgency_score,
        "action": action.value,
        "queue": queue,
        "suggested_reply": suggested_reply
    })

    # 4. Retorna resposta estruturada
    return RouterDecisionResponse(
        user_id=payload.user_id,
        action=action,
        queue=queue,
        intent=analysis.intent,
        sentiment=analysis.sentiment,
        urgency_score=analysis.urgency_score,
        suggested_reply=suggested_reply,
        sla_seconds=sla_seconds
    )
