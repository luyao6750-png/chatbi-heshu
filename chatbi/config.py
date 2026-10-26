"""自包含配置模块。

从 `src/core/config.py` 抽取，仅保留 ChatBI 运行所需的配置项：
数据库连接 + LLM 模型。其余（Redis/Milvus/Neo4j/MinIO）与本模块无关，已剔除。

敏感项（数据库密码、API Key）不写默认值，统一从 `.env` 读取。
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "chatbi"
    APP_ENV: str = "dev"
    APP_DEBUG: bool = True

    # PostgreSQL（默认使用独立的 chatbi_db 库，避免与主项目的 medical_db 冲突）
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "medical"
    DB_PASSWORD: str = "medical123"
    DB_NAME: str = "chatbi_db"

    # LLM（兼容 OpenAI 协议，默认走阿里 DashScope 兼容模式）
    DASHSCOPE_API_KEY: str = ""
    BASE_URL_CHAT: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    CHAT_MODEL: str = "qwen-max"

    LOG_LEVEL: str = "DEBUG"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # 指定环境变量文件
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
