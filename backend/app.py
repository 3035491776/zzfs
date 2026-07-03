# -*- coding: utf-8 -*-
"""智慧图书馆管理系统 — Flask 应用入口
Flask + CORS + JWT + RESTful API

采用增量构建策略：
  每个 Step 完成后取消对应注释即可启用新蓝图。
"""

from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db
from utils.response import success


def _register_blueprints(app):
    """注册所有 API 蓝图 — 用 try/except 支持增量构建"""
    # ---- Step 3: 认证模块 ----
    try:
        from api.auth_api import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
    except ImportError:
        pass

    try:
        from api.captcha_api import captcha_bp
        app.register_blueprint(captcha_bp, url_prefix='/api/captcha')
    except ImportError:
        pass

    # ---- Step 4: 图书 + 分类 + Excel ----
    try:
        from api.category_api import category_bp
        app.register_blueprint(category_bp, url_prefix='/api/categories')
    except ImportError:
        pass

    try:
        from api.book_api import book_bp
        app.register_blueprint(book_bp, url_prefix='/api/books')
    except ImportError:
        pass

    try:
        from api.excel_api import excel_bp
        app.register_blueprint(excel_bp, url_prefix='/api/excel')
    except ImportError:
        pass

    # ---- Step 5: 借阅 + 通知 ----
    try:
        from api.borrow_api import borrow_bp
        app.register_blueprint(borrow_bp, url_prefix='/api/borrows')
    except ImportError:
        pass

    try:
        from api.notification_api import notification_bp
        app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    except ImportError:
        pass

    # ---- Step 6: 自习室预约 ----
    try:
        from api.seat_api import seat_bp
        app.register_blueprint(seat_bp, url_prefix='/api/seats')
    except ImportError:
        pass

    try:
        from api.reservation_api import reservation_bp
        app.register_blueprint(reservation_bp, url_prefix='/api/reservations')
    except ImportError:
        pass

    # ---- Step 7: AI + 地图 + 数据大屏 ----
    try:
        from api.ai_api import ai_bp
        app.register_blueprint(ai_bp, url_prefix='/api/ai')
    except ImportError:
        pass

    try:
        from api.map_api import map_bp
        app.register_blueprint(map_bp, url_prefix='/api/map')
    except ImportError:
        pass

    try:
        from api.dashboard_api import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    except ImportError:
        pass

    # ---- 用户管理 ----
    try:
        from api.user_api import user_bp
        app.register_blueprint(user_bp, url_prefix='/api/users')
    except ImportError:
        pass

    # ---- 图书荐购 ----
    try:
        from api.book_request_api import book_request_bp
        app.register_blueprint(book_request_bp, url_prefix='/api/book-requests')
    except ImportError:
        pass

    # ---- 座位报修 ----
    try:
        from api.seat_repair_api import seat_repair_bp
        app.register_blueprint(seat_repair_bp, url_prefix='/api/seat-repairs')
    except ImportError:
        pass

    # ---- 系统广播 ----
    try:
        from api.broadcast_api import broadcast_bp
        app.register_blueprint(broadcast_bp, url_prefix='/api/broadcast')
    except ImportError:
        pass

    # ---- 管理员待处理统计 ----
    try:
        from api.admin_counts_api import admin_counts_bp
        app.register_blueprint(admin_counts_bp, url_prefix='/api/admin')
    except ImportError:
        pass


def _create_tables(app):
    """创建数据库表 — 仅导入已存在的模型"""
    with app.app_context():
        import models
        db.create_all()


def create_app():
    """应用工厂"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 启用 CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    _register_blueprints(app)

    # 健康检查
    @app.route('/api/health')
    def health():
        return success({'status': 'ok', 'version': '2.0.0'}, '智慧图书馆管理系统运行正常')

    # 创建数据表
    _create_tables(app)

    return app


if __name__ == '__main__':
    app = create_app()
    print('=' * 60)
    print('  智慧图书馆管理系统 V2.0')
    print('  API 地址: http://127.0.0.1:5000')
    print('  健康检查: http://127.0.0.1:5000/api/health')
    print('=' * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
