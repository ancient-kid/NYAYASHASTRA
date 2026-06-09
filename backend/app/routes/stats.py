
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Statute, CaseLaw, ChatSession

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """Get real-time statistics for the dashboard."""
    try:
        statutes_count = db.query(Statute).count()
        cases_count = db.query(CaseLaw).count()
        chats_count = db.query(ChatSession).count()
        
        return {
            "savedStatutes": statutes_count,
            "casesAnalyzed": cases_count,
            "activeSessions": chats_count
        }
    except Exception as e:
        import logging
        logging.error(f"Error fetching stats: {e}")
        return {
            "savedStatutes": 0,
            "casesAnalyzed": 0,
            "activeSessions": 0
        }
