# -*- coding: utf-8 -*-
"""Flask 扩展初始化"""

from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# CORS 和 SocketIO 在 app.py 中初始化
# 扩展实例在 app 工厂中绑定
