# -*- coding: utf-8 -*-
"""短信发送工具 — mock 模式 + 真实SDK预留"""

import random
import logging

logger = logging.getLogger(__name__)


def send_sms(phone, code):
    """发送短信验证码

    Args:
        phone: 手机号
        code: 验证码

    Returns:
        dict: { 'success': True/False, 'message': '...' }
    """
    # Mock 模式：控制台打印验证码
    logger.info(f'[SMS] 向 {phone} 发送验证码: {code}')
    print(f'\n  [SMS Mock] 手机号: {phone}  验证码: {code}\n')

    # TODO: 接入真实短信服务
    # from tencentcloud.sms.v20210111 import sms_client, models
    # ...

    return {
        'success': True,
        'message': f'验证码已发送至 {phone}（Mock模式，验证码见控制台）',
    }


def generate_sms_code(length=6):
    """生成数字验证码"""
    return ''.join(random.choices('0123456789', k=length))
