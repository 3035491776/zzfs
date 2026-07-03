# -*- coding: utf-8 -*-
"""图形验证码生成工具 — 基于 Pillow"""

import random
import string
import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def generate_captcha(code=None):
    """生成图形验证码

    Args:
        code: 验证码文本，4位数字+字母，不传则自动生成

    Returns:
        dict: { 'code': 'A3B8', 'image_base64': 'data:image/png;base64,...' }
    """
    if code is None:
        # 生成4位验证码（排除容易混淆的字符）
        chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
        code = ''.join(random.choices(chars, k=4))

    # 创建画布 120x50
    width, height = 120, 50
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # 添加噪点
    for _ in range(100):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        draw.point((x, y), fill=(random.randint(0, 200), random.randint(0, 200),
                                  random.randint(0, 200)))

    # 添加干扰线
    for _ in range(3):
        x1 = random.randint(0, width // 3)
        y1 = random.randint(0, height)
        x2 = random.randint(2 * width // 3, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)],
                  fill=(random.randint(0, 180), random.randint(0, 180), random.randint(0, 180)),
                  width=1)

    # 绘制文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype('arial.ttf', 28)
    except Exception:
        try:
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 28)
        except Exception:
            font = ImageFont.load_default()

    for i, char in enumerate(code):
        x = 15 + i * 23 + random.randint(-3, 3)
        y = random.randint(5, 12)
        color = (random.randint(0, 120), random.randint(0, 120), random.randint(0, 180))
        draw.text((x, y), char, font=font, fill=color)

    # 模糊处理
    image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

    # 转 Base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_base64 = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('utf-8')

    return {
        'code': code,
        'image_base64': img_base64,
    }
