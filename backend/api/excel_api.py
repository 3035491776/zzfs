# -*- coding: utf-8 -*-
"""Excel 导入导出 API"""

from flask import Blueprint, request, send_file
from utils.response import success, error
from utils.jwt_utils import login_required, admin_required
from services.excel_service import (
    generate_book_template,
    parse_book_excel,
    export_books_excel,
    export_borrows_excel,
)
import io

excel_bp = Blueprint('excel', __name__)


@excel_bp.route('/import/books', methods=['POST'])
@admin_required
def import_books():
    """批量导入图书 Excel"""
    if 'file' not in request.files:
        return error('请上传Excel文件')

    file = request.files['file']
    if not file.filename.endswith(('.xlsx', '.xls')):
        return error('仅支持 .xlsx 或 .xls 格式')

    success_count, fail_list = parse_book_excel(file)

    return success({
        'success_count': success_count,
        'fail_count': len(fail_list),
        'fail_list': fail_list[:20],  # 最多返回20条失败记录
    }, f'成功导入 {success_count} 本图书')


@excel_bp.route('/export/books', methods=['GET'])
@admin_required
def export_books():
    """导出图书数据 Excel"""
    data = export_books_excel()
    return send_file(
        io.BytesIO(data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='图书数据.xlsx',
    )


@excel_bp.route('/export/borrows', methods=['GET'])
@admin_required
def export_borrows():
    """导出借阅记录 Excel"""
    data = export_borrows_excel()
    return send_file(
        io.BytesIO(data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='借阅记录.xlsx',
    )


@excel_bp.route('/template/books', methods=['GET'])
@admin_required
def download_template():
    """下载图书导入模板"""
    data = generate_book_template()
    return send_file(
        io.BytesIO(data),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='图书导入模板.xlsx',
    )
