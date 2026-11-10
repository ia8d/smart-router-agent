from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime

class ChannelEnum(str, Enum):
    WHATSAPP = "whatsapp"
    WEB = "web"
    INSTAGRAM = "instagram"

class IntentEnum(str, Enum):
    SUPORTE_TECNICO = "SUPORTE_TECNICO"
    VENDAS = "VENDAS"
    CANCELAMENTO = "CANCELAMENTO"
    FINANCEIRO = "FINANCEIRO"
    OUTROS = "OUTROS"

class SentimentEnum(str, Enum):
    POSITIVO = "POSITIVO"
    NEUTRO = "NEUTRO"
    FRUSTRADO = "FRUSTRADO"

class ActionEnum(str, Enum):
    AUTO_REPLY = "AUTO_REPLY"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"

# Payload recebido pelo webhook da API
class IncomingMessageRequest(BaseModel):
    user_id: str = Field(..., description="Identificador do usuário (ex: telefone WhatsApp)", example="5511999998888")
    channel: ChannelEnum = Field(default=ChannelEnum.WHATSAPP, description="Canal de entrada")
    text: str = Field(..., min_length=1, description="Texto da mensagem enviada pelo cliente", example="Quero cancelar meu plano!")

# Saída estruturada esperada do LLM
class LLMClassification(BaseModel):
    intent: IntentEnum
    sentiment: SentimentEnum
    urgency_score: int = Field(..., ge=1, le=5, description="Nível de urgência de 1 a 5")
    summary: str = Field(..., description="Resumo em 1 frase da necessidade do cliente")

# Resposta final do microsserviço
class RouterDecisionResponse(BaseModel):
    user_id: str
    action: ActionEnum
    queue: str = Field(..., description="Fila de atendimento ou setor de roteamento")
    intent: IntentEnum
    sentiment: SentimentEnum
    urgency_score: int
    suggested_reply: str
    sla_seconds: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
