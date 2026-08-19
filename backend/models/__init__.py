# -*- coding: utf-8 -*-
"""数据模型包 — 按依赖顺序导入所有模型，确保 SQLAlchemy 能解析跨文件关系

导入顺序很重要：
  1. 先导入无外键依赖的基础模型
  2. 再导入有外键的关联模型
"""

# Level 1: 无外键依赖
from models.user import User
from models.category import Category
from models.seat import Seat
from models.sms_log import SmsLog

# Level 2: 依赖 Level 1
from models.book import Book
from models.borrow import Borrow
from models.reservation import Reservation
from models.notification import Notification
from models.ai_conversation import AiConversation
from models.access_log import AccessLog
from models.book_request import BookRequest
from models.seat_repair import SeatRepair

# Level 3: V2 分析任务、快照与历史事实
from models.metric_job_run import MetricJobRun
from models.metric_snapshot import MetricSnapshot
from models.seat_capacity_snapshot import SeatCapacitySnapshot
from models.borrow_due_change import BorrowDueChange

__all__ = [
    'User',
    'Category',
    'Book',
    'Borrow',
    'Seat',
    'Reservation',
    'Notification',
    'AiConversation',
    'AccessLog',
    'SmsLog',
    'BookRequest',
    'SeatRepair',
    'MetricJobRun',
    'MetricSnapshot',
    'SeatCapacitySnapshot',
    'BorrowDueChange',
]
