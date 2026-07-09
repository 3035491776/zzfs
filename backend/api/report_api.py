# -*- coding: utf-8 -*-
"""管理员月度报告 API。"""

from datetime import datetime

from flask import Blueprint, request

from services.report_service import get_monthly_report
from utils.jwt_utils import admin_required
from utils.response import error, success

report_bp = Blueprint('report', __name__)


@report_bp.route('/monthly', methods=['GET'])
@admin_required
def monthly_report():
    """获取管理员月度运营报告统计。"""
    month = (request.args.get('month') or datetime.now().strftime('%Y-%m')).strip()

    try:
        report = get_monthly_report(month)
    except ValueError as exc:
        return error(str(exc), code=400)

    return success(report)
