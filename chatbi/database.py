"""自包含数据库会话模块。

从 `src/infra/database.py` 抽取，仅依赖本包的 `chatbi.config`。
"""
from chatbi.config import get_settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

settings = get_settings()

# 1. 创建引擎（连接池）
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_DEBUG,  # 调试模式下打印所有 SQL 语句
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=60 * 5,
    pool_pre_ping=True,
)

# 2. 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 3. 定义异步获取数据库会话连接
async def get_db() -> AsyncSession:
    """FastAPI 依赖注入，获取数据库会话连接 Depends(get_db)。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
