"""
Celery 异步任务队列

用于处理长任务：文档解析、批量审核、法规索引更新。
"""

from celery import Celery

from backend.core.config import settings

celery_app = Celery(
    "finguard",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分钟超时
    task_soft_time_limit=25 * 60,  # 25 分钟软超时
    worker_max_tasks_per_child=50,  # 防止内存泄漏
)
