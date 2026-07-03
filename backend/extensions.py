# -*- coding: utf-8 -*-
"""Flask 扩展初始化"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

# CORS 和 SocketIO 在 app.py 中初始化
# 此处仅声明 db，其他扩展实例在 app 工厂中创建
