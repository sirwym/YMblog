# tools/tasks.py
from celery import shared_task
from asgiref.sync import async_to_sync
from .ai_utils import generate_gen_script
import logging

logger = logging.getLogger(__name__)

@shared_task
def task_ai_generate(description, solution, mode):
    """
    Celery 异步任务：调用 AI 生成代码
    """
    try:
        result_dict = async_to_sync(generate_gen_script)(description, solution, mode)
        return {
            'status': 'OK',
            'gen_code': result_dict.get('gen_code', ''),
            'val_code': result_dict.get('val_code', ''),
            'analysis': result_dict.get('analysis', ''),
            'plan': result_dict.get('plan', '')
        }
    except Exception as e:
        logger.exception(f"Task Failed: {e}")
        return {
            'status': 'Error',
            'error': str(e)
        }