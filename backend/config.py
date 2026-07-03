# -*- coding: utf-8 -*-
"""智慧图书馆管理系统 - 配置文件"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    DEBUG = True

    # MySQL 数据库配置
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASS = os.environ.get('DB_PASS', '')
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'smart_library')

    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        '?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'change-me-in-production')
    JWT_EXPIRATION_HOURS = 24

    # CORS - 允许的前端域名
    CORS_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']

    # 借阅天数
    BORROW_DAYS = 30
    # 最大续借次数
    MAX_RENEW_COUNT = 2
    # 每本图书最大借阅数
    MAX_BORROW_BOOKS = 5

    # 分页每页条数
    PAGE_SIZE = 10

    # 自习室预约规则
    SEAT_RESERVE_DAYS = 7        # 可提前预约天数
    SEAT_CHECKIN_MINUTES = 30    # 签到迟到宽限时间(分钟)
    SEAT_NO_SHOW_LIMIT = 3       # 未签到上限(次/月)

    # 验证码
    CAPTCHA_EXPIRE_SECONDS = 300  # 5分钟

    # 短信 (mock 模式)
    SMS_MOCK = True

    # DeepSeek AI
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = 'https://api.deepseek.com'

    # 百度地图
    BAIDU_MAP_AK = os.environ.get('BAIDU_MAP_AK', 'your-baidu-map-ak')

    # 图书馆位置 (示例: 某大学图书馆)
    LIBRARY_LAT = 39.9042
    LIBRARY_LNG = 116.4074
    LIBRARY_NAME = '智慧图书馆'
    LIBRARY_ADDRESS = '北京市海淀区'
