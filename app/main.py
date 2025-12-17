from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.analyzer import GEOEngine
from app.core.database import SessionLocal, AuditLog, init_db
from sqlalchemy.orm import Session
import uvicorn
import os
import stripe
from fastapi.responses import Response

app = FastAPI(title="GEO System API", version="4.1.1")

@app.get("/api/version")
def get_version():
    return {"version": "v4.1.1", "lang": "zh-CN"}

# Load Stripe Key
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
stripe.api_key = STRIPE_API_KEY

# Cache Control Middleware
@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    # Prevent caching for HTML and JSON to ensure users see updates
    if request.url.path == "/" or request.url.path.endswith(".html") or request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# 启动时初始化数据库
@app.on_event("startup")
def on_startup():
    init_db()

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化核心引擎
engine = GEOEngine()

@app.get("/api/health")
def health_check():
    return {"status": "active", "system": "GEO Core v1.0"}

@app.get("/api/analyze")
def analyze_brand(brand: str, industry: str = "general", db: Session = Depends(get_db)):
    """
    核心端点：分析品牌在 AI 世界的排名 (并将结果存入数据库)
    """
    report = engine.analyze_brand(brand, industry)
    
    # 持久化存储
    log = AuditLog(
        brand_name=brand,
        industry=industry,
        geo_score=report['geo_score'],
        model_breakdown=report['model_breakdown']
    )
    db.add(log)
    db.commit()
    
    return report

# 挂载静态文件 (前端 Dashboard)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    """
    获取最近的审计历史
    """
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    return logs

@app.post("/api/create-checkout-session")
def create_checkout_session():
    """
    创建 Stripe 支付会话
    """
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=400, detail="Payment system not configured (Missing STRIPE_API_KEY)")
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cny',
                    'product_data': {
                        'name': 'GEO System Pro (Enterprise)',
                    },
                    'unit_amount': 9900, # ¥99.00
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://geo-system.onrender.com/?success=true',
            cancel_url='https://geo-system.onrender.com/?canceled=true',
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 GEO System (Generative Engine Optimization) 启动中...")
    # 适配云平台端口 (Render/Heroku 会注入 PORT 环境变量)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
