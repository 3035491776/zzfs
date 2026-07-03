# -*- coding: utf-8 -*-
"""图书馆地图 API — 位置信息 + 附近搜索"""

from flask import Blueprint, request, current_app
from utils.response import success, error

map_bp = Blueprint('map', __name__)


@map_bp.route('/library-info', methods=['GET'])
def library_info():
    """获取图书馆位置信息"""
    return success({
        'name': current_app.config.get('LIBRARY_NAME', '智慧图书馆'),
        'address': current_app.config.get('LIBRARY_ADDRESS', ''),
        'lat': current_app.config.get('LIBRARY_LAT', 39.9042),
        'lng': current_app.config.get('LIBRARY_LNG', 116.4074),
        'baidu_map_ak': current_app.config.get('BAIDU_MAP_AK', ''),
    })


@map_bp.route('/nearby', methods=['GET'])
def nearby():
    """附近点位搜索（静态数据示例）

    Query Params:
        keyword: 搜索关键词
    """
    keyword = request.args.get('keyword', '').strip()

    # 静态点位数据（后续可接百度地图 Place API）
    points = [
        {'name': '智慧图书馆', 'lat': 39.9042, 'lng': 116.4074, 'type': '图书馆'},
        {'name': '第一教学楼', 'lat': 39.9050, 'lng': 116.4060, 'type': '教学楼'},
        {'name': '第二教学楼', 'lat': 39.9035, 'lng': 116.4080, 'type': '教学楼'},
        {'name': '学生食堂', 'lat': 39.9055, 'lng': 116.4050, 'type': '餐饮'},
        {'name': '体育馆', 'lat': 39.9030, 'lng': 116.4065, 'type': '体育'},
        {'name': '学生宿舍1号楼', 'lat': 39.9060, 'lng': 116.4055, 'type': '宿舍'},
        {'name': '行政楼', 'lat': 39.9045, 'lng': 116.4085, 'type': '办公'},
    ]

    if keyword:
        points = [p for p in points if keyword in p['name'] or keyword in p['type']]

    return success({
        'list': points,
        'total': len(points),
    })
