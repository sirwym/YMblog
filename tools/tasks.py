# tools/tasks.py
from celery import shared_task
from asgiref.sync import async_to_sync
from .ai_utils import generate_gen_script
import logging

logger = logging.getLogger(__name__)

@shared_task
def task_ai_generate(description, solution):
    """
    Celery 异步任务：调用 AI 生成代码
    """
    try:
        # 将异步函数转换为同步调用
        gen_code, val_code = async_to_sync(generate_gen_script)(description, solution)
        return {
            'status': 'OK',
            'gen_code': gen_code,
            'val_code': val_code
        }
    except Exception as e:
        logger.error(f"Task Failed: {e}")
        return {
            'status': 'Error',
            'error': str(e)
        }