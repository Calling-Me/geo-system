from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 获取数据库连接串 (如果没有则使用本地 SQLite 作为 fallback)
# 默认使用 SQLite，防止无配置时报错
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./geo_system.db")

try:
    if "sqlite" in DATABASE_URL:
        # SQLite 配置
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        # PostgreSQL 配置 (Supabase/Neon)
        # 增加 pool_pre_ping 防止连接断开
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # 🟢 CRITICAL: Test connection immediately to trigger fallback if failed
        with engine.connect() as connection:
            pass
        
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(f"✅ Database connected: {'SQLite' if 'sqlite' in DATABASE_URL else 'PostgreSQL'}")

except Exception as e:
    print(f"⚠️ Database connection failed: {e}")
    print("🔄 Falling back to in-memory SQLite for resilience.")
    # Fallback to local file db so data persists slightly better than memory, or just memory
    engine = create_engine("sqlite:///./fallback.db", connect_args={"check_same_thread": False})
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
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created.")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
