# -*- coding: utf-8 -*-
"""验证码接口 — 图形验证码生成"""

from flask import Blueprint, session
from utils.response import success, error
from utils.captcha_utils import generate_captcha

captcha_bp = Blueprint('captcha', __name__)


@captcha_bp.route('/image', methods=['GET'])
def get_captcha_image():
    """获取图形验证码"""
    result = generate_captcha()

    # 验证码文本存入 session（5分钟有效）
    session['captcha_code'] = result['code']
    session.permanent = True

    return success({
        'captcha_key': 'session',
        'image_base64': result['image_base64'],
    }, '验证码已生成')
