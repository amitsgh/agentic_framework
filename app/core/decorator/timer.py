"""Time Decorator"""

import time
from functools import wraps

from app.core.logger import setuplog

logger = setuplog(__name__)


def timer(func):
    """Time Decorator"""

    @wraps(func)
    def wrapper(*args, **kwargs):
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

    return wrapper
