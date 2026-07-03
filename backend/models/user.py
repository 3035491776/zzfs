# -*- coding: utf-8 -*-
"""用户表模型 — 扩展字段：phone, email, face_image; 角色：student/teacher/admin"""

from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """用户表"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(100), unique=True, nullable=False, comment='用户名')
    password = db.Column(db.String(255), nullable=False, comment='登录密码(哈希)')
    real_name = db.Column(db.String(255), nullable=False, comment='真实姓名')
    phone = db.Column(db.String(20), comment='手机号（短信登录用）')
    email = db.Column(db.String(100), comment='邮箱')
    role = db.Column(db.String(20), nullable=False, default='student',
                     comment='角色: student/teacher/admin')
    status = db.Column(db.String(20), nullable=False, default='active',
                       comment='状态: active/disabled')
    face_image = db.Column(db.String(500), comment='人脸图片路径（预留）')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='注册时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                            comment='更新时间')

    # 关系 — 使用字符串名延迟绑定，避免跨文件导入问题
    borrows = db.relationship('Borrow', backref='student', lazy='dynamic',
                              primaryjoin='User.id == Borrow.user_id')
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    ai_conversations = db.relationship('AiConversation', backref='user', lazy='dynamic')
    access_logs = db.relationship('AccessLog', backref='user', lazy='dynamic')

    def set_password(self, raw):
        """加密存储密码"""
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        """校验密码"""
        return check_password_hash(self.password, raw)

    def is_admin(self):
        return self.role == 'admin'

    def is_active(self):
        return self.status == 'active'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'phone': self.phone or '',
            'email': self.email or '',
            'role': self.role,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M') if self.create_time else '',
        }
