"""Database Factor"""

from typing import Type

from app.services.db.base import BaseDB
from app.services.db.redis_db import RedisDB
from app.core.config import config
from app.core.logger import setuplog

logger = setuplog(__name__)

DATABASE_REGISTRY: dict[str, Type[BaseDB]] = {
    "redis": RedisDB,
    # add more dbs
}


def get_db_instance() -> BaseDB:
    """Get database instance"""

    db_class = DATABASE_REGISTRY.get(config.DATABASE_TYPE.lower())

    if db_class is None:
        logger.warning(
            "Database type %s not found, falling back to default", config.DATABASE_TYPE
        )
        db_class = RedisDB

    return db_class()
