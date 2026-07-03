# -*- coding: utf-8 -*-
"""AI 助手 API — 对话 + 推荐"""

from flask import Blueprint, request, g, Response, stream_with_context
from utils.response import success, error
from utils.jwt_utils import login_required
from services.ai_service import chat_with_ai, recommend_books, chat_stream

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    """AI 对话

    Request Body:
        message: 用户消息
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()

    if not message:
        return error('请输入消息')

    reply = chat_with_ai(g.current_user['user_id'], message)

    return success({
        'reply': reply,
    }, '对话完成')


@ai_bp.route('/chat/stream', methods=['POST'])
@login_required
def chat_stream_api():
    """AI 对话（流式）

    Response: text/event-stream
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()

    if not message:
        return error('请输入消息')

    def generate():
        for chunk in chat_stream(g.current_user['user_id'], message):
            yield f'data: {chunk}\n\n'
        yield 'data: [DONE]\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@ai_bp.route('/recommend', methods=['GET'])
@login_required
def recommend():
    """AI 图书推荐"""
    result = recommend_books(g.current_user['user_id'])
    return success(result, '推荐完成')


@ai_bp.route('/conversations', methods=['GET'])
@login_required
def conversations():
    """获取历史对话"""
    from models.ai_conversation import AiConversation

    convos = AiConversation.query.filter_by(
        user_id=g.current_user['user_id']
    ).order_by(
        AiConversation.create_time.asc()
    ).limit(50).all()

    return success({
        'list': [c.to_dict() for c in convos],
    })
