import json
import os
from app.models import IncomingMessageRequest, ChannelEnum
from app.router_service import process_and_route_message
from app.database import init_db

def run_evaluation():
    init_db()
    dataset_path = os.path.join("tests", "eval_dataset.json")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    total = len(cases)
    intent_correct = 0
    action_correct = 0
    
    print("\n" + "="*60)
    print("🚀 INICIANDO BENCHMARK / AVALIAÇÃO DO SMART ROUTER AGENT")
    print("="*60)
    
    for i, c in enumerate(cases, 1):
        payload = IncomingMessageRequest(
            user_id=f"test_user_{i}",
            channel=ChannelEnum.WHATSAPP,
            text=c["text"]
        )
        
        result = process_and_route_message(payload)
        
        is_intent_ok = result.intent.value == c["expected_intent"]
        is_action_ok = result.action.value == c["expected_action"]
        
        if is_intent_ok:
            intent_correct += 1
        if is_action_ok:
            action_correct += 1
            
        status = "✅ PASS" if (is_intent_ok and is_action_ok) else "❌ FAIL"
        print(f"[{i:02d}/{total}] {status} | Texto: \"{c['text'][:35]}...\"")
        print(f"       -> Intent: {result.intent.value} (Esperado: {c['expected_intent']})")
        print(f"       -> Ação:   {result.action.value} (Esperado: {c['expected_action']})\n")
        
    intent_acc = (intent_correct / total) * 100
    action_acc = (action_correct / total) * 100
    
    print("="*60)
    print("📊 RESULTADO FINAL DA AVALIAÇÃO DE IA")
    print(f"Total de Amostras: {total}")
    print(f"Acurácia de Classificação de Intenção: {intent_acc:.1f}%")
    print(f"Acurácia de Decisão de Roteamento/Handoff: {action_acc:.1f}%")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_evaluation()
