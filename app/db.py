from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.mongo_uri,
            serverSelectionTimeoutMS=20000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            retryWrites=True,
            w="majority",
        )
    return _client


def get_db():
    if settings.db_backend == "sqlite":
        return "sqlite"
    return get_client()[settings.mongo_db]


async def ping_mongo() -> None:
    client = get_client()
    await client.admin.command("ping")


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
