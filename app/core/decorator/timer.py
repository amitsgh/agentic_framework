"""Time Decorator"""

import time
import asyncio
from functools import wraps

from app.core.logger import setuplog

logger = setuplog(__name__)


def timer(func):
    """Time Decorator supporting both sync and async functions"""

    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time < 60:
                    logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
                else:
                    minutes = execution_time / 60
                    logger.info(f"{func.__name__} executed in {minutes:.2f} minutes")

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                if execution_time < 60:
                    logger.error(
                        f"{func.__name__} executed in {execution_time:.2f} seconds"
                    )
                else:
                    minutes = execution_time / 60
                    logger.error(f"{func.__name__} executed in {minutes:.2f} minutes")
                raise

        return async_wrapper

    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time < 60:
                    logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
                else:
                    minutes = execution_time / 60
                    logger.info(f"{func.__name__} executed in {minutes:.2f} minutes")

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                if execution_time < 60:
                    logger.error(
                        f"{func.__name__} executed in {execution_time:.2f} seconds"
                    )
                else:
                    minutes = execution_time / 60
                    logger.error(f"{func.__name__} executed in {minutes:.2f} minutes")
                raise e

        return sync_wrapper
