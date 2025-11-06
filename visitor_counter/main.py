from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from visitor_service import VisitorService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="访客计数服务",
    description="基于FastAPI的独立访客计数服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建访客计数服务实例
visitor_service = VisitorService()

@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "message": "访客计数服务正在运行",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/visitor")
async def get_visitor_count():
    """获取当前访客计数"""
    try:
        count = visitor_service.get_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"获取访客计数失败: {e}")
        raise HTTPException(status_code=500, detail="获取访客计数失败")

@app.post("/api/visitor")
async def increment_visitor_count():
    """增加访客计数"""
    try:
        count = visitor_service.increment_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"增加访客计数失败: {e}")
        raise HTTPException(status_code=500, detail="增加访客计数失败")

@app.get("/api/visitor/stats")
async def get_visitor_stats():
    """获取详细统计信息"""
    try:
        stats = visitor_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

@app.get("/api/visitor/health")
async def health_check():
    """健康检查"""
    try:
        count = visitor_service.get_count()
        return {
            "status": "healthy",
            "visitor_count": count,
            "service": "visitor_counter"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "service": "visitor_counter"
            }
        )

@app.post("/api/visitor/reset")
async def reset_visitor_count():
    """重置访客计数（管理员功能）"""
    try:
        count = visitor_service.reset_count()
        return {"message": "访客计数已重置", "count": count}
    except Exception as e:
        logger.error(f"重置访客计数失败: {e}")
        raise HTTPException(status_code=500, detail="重置访客计数失败")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )
