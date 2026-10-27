from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# MySQL 连接串
DATABASE_URL = "mysql+aiomysql://root:1234@localhost:3306/schedwise?charset=utf8mb4"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # 调试时改成 True，可以看到 SQL 日志
    pool_size=10,
    max_overflow=20,
)

# 会话工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


async def get_db():
    """FastAPI 依赖：每个请求一个数据库会话"""
    async with async_session() as session:
        yield session