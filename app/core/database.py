from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 获取数据库连接串 (如果没有则使用本地 SQLite 作为 fallback)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./geo_system.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AuditLog(Base):
    """
    审计日志表：记录每一次品牌查询
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String, index=True)
    industry = Column(String)
    geo_score = Column(Integer)
    model_breakdown = Column(JSON) # 存储各模型的详细得分
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
