import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.getenv("DATABASE_PATH", "smart_router.db")

def get_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn

def init_db():
    """Inicializa as tabelas do banco de dados relacional via SQL puro."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS message_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        channel TEXT NOT NULL,
        user_text TEXT NOT NULL,
        intent TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        urgency_score INTEGER NOT NULL,
        action TEXT NOT NULL,
        queue TEXT NOT NULL,
        suggested_reply TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Criar índices para consultas analíticas rápidas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON message_logs(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment ON message_logs(sentiment);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_intent ON message_logs(intent);")
    
    conn.commit()
    conn.close()

def save_message_log(log_data: Dict[str, Any]) -> int:
    """Insere o registro completo da decisão de roteamento no banco SQL."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO message_logs (
        user_id, channel, user_text, intent, sentiment, 
        urgency_score, action, queue, suggested_reply
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        log_data["user_id"],
        log_data["channel"],
        log_data["user_text"],
        log_data["intent"],
        log_data["sentiment"],
        log_data["urgency_score"],
        log_data["action"],
        log_data["queue"],
        log_data["suggested_reply"]
    ))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_analytics_summary() -> Dict[str, Any]:
    """Retorna métricas consolidadas via queries SQL com agregação."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de mensagens
    cursor.execute("SELECT COUNT(*) as total FROM message_logs;")
    total = cursor.fetchone()["total"]
    
    # Distribuição de sentimentos
    cursor.execute("""
    SELECT sentiment, COUNT(*) as count 
    FROM message_logs 
    GROUP BY sentiment;
    """)
    sentiments = {row["sentiment"]: row["count"] for row in cursor.fetchall()}
    
    # Distribuição de ações (Handoff vs Auto Reply)
    cursor.execute("""
    SELECT action, COUNT(*) as count 
    FROM message_logs 
    GROUP BY action;
    """)
    actions = {row["action"]: row["count"] for row in cursor.fetchall()}
    
    conn.close()
    return {
        "total_messages": total,
        "sentiments": sentiments,
        "actions": actions
    }
