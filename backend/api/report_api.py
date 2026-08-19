# -*- coding: utf-8 -*-
"""管理员月度报告 API。"""

from datetime import datetime

from flask import Blueprint, request

from services.ai_service import generate_monthly_report_analysis
from services.snapshot_view_service import build_monthly_snapshot_report
from utils.jwt_utils import admin_required
from utils.response import error, success

report_bp = Blueprint('report', __name__)


@report_bp.route('/monthly', methods=['GET'])
@admin_required
def monthly_report():
    """获取管理员月度运营报告统计。"""
    month = (request.args.get('month') or datetime.now().strftime('%Y-%m')).strip()

    try:
        report = build_monthly_snapshot_report(month)
    except ValueError as exc:
        return error(str(exc), code=400)

    if report is None:
        return error(
            '该月份 Snapshot 尚未发布',
            code=404,
            data={'source': 'snapshot_unavailable', 'month': month},
        )

    return success(report)


@report_bp.route('/monthly/ai-analysis', methods=['POST'])
@admin_required
def monthly_ai_analysis():
    """基于月度真实统计数据生成 AI 运营分析。"""
    data = request.get_json(silent=True) or {}
    month = (data.get('month') or datetime.now().strftime('%Y-%m')).strip()

    try:
        report = build_monthly_snapshot_report(month)
        if report is None:
            return error(
                '该月份 Snapshot 尚未发布',
                code=404,
                data={'source': 'snapshot_unavailable', 'month': month},
            )
        analysis = generate_monthly_report_analysis(report)
    except ValueError as exc:
        return error(str(exc), code=400)
    except RuntimeError as exc:
        return error(str(exc), code=503)

    return success({
        'month': month,
        'analysis': analysis,
        'data_source': 'snapshot',
        'source': 'snapshot',
        'calculation_version': report.get('calculation_version'),
        'generated_time': report.get('generated_time'),
        'job_run_id': report.get('job_run_id'),
        'is_mock': False,
    })
