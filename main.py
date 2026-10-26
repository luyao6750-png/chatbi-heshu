"""
ChatBI FastAPI 入口
挂载 ChatBI 路由，暴露 /api/v1/bi/query 等接口。
启动：uvicorn main:app --host 0.0.0.0 --port 8081 --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbi.router import router as bi_router

app = FastAPI(
    title="ChatBI 数据可视化服务",
    description="自然语言 → SQL → 图表（ECharts option）",
    version="1.0.0",
)

# 前后端分离，允许跨域（前端直接调用 setOption 渲染）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bi_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "chatbi"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8081, reload=True)
