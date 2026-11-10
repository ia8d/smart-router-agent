from fastapi import FastAPI, HTTPException
from app.models import IncomingMessageRequest, RouterDecisionResponse
from app.router_service import process_and_route_message
from app.database import init_db, get_analytics_summary

app = FastAPI(
    title="Smart Router Agent — Blip Technical Case",
    description="Microsserviço de Roteamento Inteligente com Análise de Sentimento, Hand-off e Métricas SQL",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    """Inicializa as tabelas do banco de dados na inicialização da API."""
    init_db()

@app.get("/")
def root():
    return {
        "service": "Smart Router Agent",
        "status": "online",
        "docs": "/docs"
    }

@app.post("/api/v1/message", response_model=RouterDecisionResponse)
def handle_message(payload: IncomingMessageRequest):
    """
    Endpoint principal para interceptar mensagens de mensageria (WhatsApp/Web).
    Aplica classificação via LLM, regras de hand-off e grava no banco SQL.
    """
    try:
        decision = process_and_route_message(payload)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento: {str(e)}")

@app.get("/api/v1/analytics")
def get_analytics():
    """
    Retorna métricas consolidadas diretamente de consultas analíticas SQL.
    """
    return get_analytics_summary()
