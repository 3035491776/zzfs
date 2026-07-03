# -*- coding: utf-8 -*-
"""统一 JSON 响应格式

所有 API 返回结构:
{
    "code": 200,        // 业务状态码
    "message": "成功",   // 提示信息
    "data": {}          // 数据载荷
}
"""

from flask import jsonify


def success(data=None, message='操作成功', code=200):
    """成功响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data if data is not None else {}
    })


def error(message='操作失败', code=400, data=None):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data if data is not None else {}
    }), code if code >= 200 else 400


def paginate(pagination, data_list):
    """分页响应"""
    return {
        'list': data_list,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
    }
