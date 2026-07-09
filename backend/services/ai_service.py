# -*- coding: utf-8 -*-
"""DeepSeek AI 服务 — 图书推荐 + 智能问答"""

import json
import logging
from flask import current_app
from models.book import Book
from models.ai_conversation import AiConversation
from extensions import db

logger = logging.getLogger(__name__)

# AI 系统提示词
SYSTEM_PROMPT = """你是智慧图书馆的AI助手"小智"，请用中文友好、专业地回答用户问题。

你可以帮助用户：
1. 推荐图书（根据用户的兴趣、学习需求推荐）
2. 解答图书馆使用相关问题（借阅规则、预约流程等）
3. 学习辅导（解答学术问题）
4. 闲聊交流

请保持回答简洁、有帮助。如果不知道答案，请诚实告知。
"""

RECOMMEND_PROMPT_TEMPLATE = """根据用户的阅读偏好和历史借阅记录，从以下图书数据库中推荐5本最合适的图书。

**重要**：只能从下面的图书数据库中选择，必须使用其中准确的book_id和书名。

图书数据库（本馆全部在架图书）：
{books_json}

用户借阅历史：
{borrow_history}

请返回纯JSON（不要包含markdown代码块标记）：
{{
  "recommendations": [
    {{
      "book_id": 1,
      "title": "书名",
      "author": "作者名",
      "reason": "推荐理由（20字以内）"
    }}
  ],
  "summary": "总体推荐说明（50字以内）"
}}
"""

MONTHLY_REPORT_ANALYSIS_SYSTEM_PROMPT = """你是智慧图书馆运营分析助手。

请基于用户提供的月度运营数据生成一份专业、简洁、可执行的运营分析报告。
必须遵守：
1. 不要编造数据。
2. 只能引用输入数据中存在的统计结果。
3. 如果数据不足，请明确说明“本月数据不足”，并给出通用运营建议。
4. 输出中文纯文本，结构清晰，语气专业。
5. 按以下五个部分输出：
   1. 本月运营概览
   2. 图书资源分析
   3. 座位空间分析
   4. 用户服务分析
   5. 下月优化建议
"""


def _call_deepseek(messages, stream=False):
    """调用 DeepSeek API (OpenAI 兼容模式)

    Args:
        messages: 消息列表
        stream: 是否流式

    Returns:
        str: AI 回复内容
    """
    import openai

    api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-v4-flash')

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    if stream:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        return response  # 返回流对象
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content


def _compact_monthly_report_data(report_data):
    """压缩月报统计数据，只保留 AI 分析需要的字段。"""
    core_stats = report_data.get('core_stats') or {}
    book_analysis = report_data.get('book_analysis') or {}
    seat_analysis = report_data.get('seat_analysis') or {}
    user_behavior = report_data.get('user_behavior') or {}

    return {
        'month': report_data.get('month'),
        'range': report_data.get('range'),
        'core_stats': {
            'borrow_count': core_stats.get('borrow_count', 0),
            'active_user_count': core_stats.get('active_user_count', 0),
            'reservation_count': core_stats.get('reservation_count', 0),
            'overdue_count': core_stats.get('overdue_count', 0),
            'book_request_count': core_stats.get('book_request_count', 0),
        },
        'book_analysis': {
            'popular_books': (book_analysis.get('popular_books') or [])[:10],
            'categories': (book_analysis.get('categories') or [])[:8],
            'stock_risk_books': (book_analysis.get('stock_risk_books') or [])[:5],
        },
        'seat_analysis': {
            'popular_seats': (seat_analysis.get('popular_seats') or [])[:5],
            'popular_rooms': (seat_analysis.get('popular_rooms') or [])[:5],
            'peak_hours': (seat_analysis.get('peak_hours') or [])[:8],
            'feature_preference': seat_analysis.get('feature_preference') or {},
        },
        'user_behavior': {
            'role_distribution': user_behavior.get('role_distribution') or [],
            'renew_count': user_behavior.get('renew_count', 0),
            'book_request_count': user_behavior.get('book_request_count', 0),
            'overdue_count': user_behavior.get('overdue_count', 0),
        },
    }


def _is_monthly_report_data_empty(compact_data):
    """判断月报统计是否基本为空，用于兜底提示数据不足。"""
    core_stats = compact_data.get('core_stats') or {}
    book_analysis = compact_data.get('book_analysis') or {}
    seat_analysis = compact_data.get('seat_analysis') or {}
    user_behavior = compact_data.get('user_behavior') or {}
    feature_preference = seat_analysis.get('feature_preference') or {}

    core_empty = all(int(value or 0) == 0 for value in core_stats.values())
    books_empty = not book_analysis.get('popular_books') and not book_analysis.get('categories')
    seats_empty = not seat_analysis.get('popular_seats') and not seat_analysis.get('popular_rooms') and not seat_analysis.get('peak_hours')
    preference_empty = all(float(value or 0) == 0 for value in feature_preference.values())
    behavior_empty = int(user_behavior.get('renew_count') or 0) == 0 and int(user_behavior.get('book_request_count') or 0) == 0

    return core_empty and books_empty and seats_empty and preference_empty and behavior_empty


def generate_monthly_report_analysis(report_data):
    """基于真实月报统计数据生成 AI 运营分析。

    Args:
        report_data: report_service.get_monthly_report 返回的数据

    Returns:
        str: AI 运营分析文本

    Raises:
        RuntimeError: AI 服务调用失败
    """
    compact_data = _compact_monthly_report_data(report_data)
    prompt = """请基于以下月度运营数据生成运营分析报告。

月度运营数据 JSON：
{report_json}

再次强调：不要编造数据；如果数组为空或核心指标为 0，请明确说明本月数据不足。""".format(
        report_json=json.dumps(compact_data, ensure_ascii=False, indent=2)
    )

    messages = [
        {'role': 'system', 'content': MONTHLY_REPORT_ANALYSIS_SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt},
    ]

    try:
        analysis = _call_deepseek(messages)
        if _is_monthly_report_data_empty(compact_data) and '本月数据不足' not in analysis:
            analysis = f'本月数据不足。\n\n{analysis}'
        return analysis
    except Exception as e:
        logger.error(f'月度报告 AI 分析失败: {e}')
        raise RuntimeError('AI 分析服务暂时不可用，请稍后重试') from e


def chat_with_ai(user_id, user_message):
    """AI 对话

    Args:
        user_id: 用户ID
        user_message: 用户输入

    Returns:
        str: AI 回复
    """
    # 保存用户消息
    user_msg = AiConversation(user_id=user_id, role='user', content=user_message)
    db.session.add(user_msg)

    # 获取历史对话（最近10条）
    history = AiConversation.query.filter_by(user_id=user_id).order_by(
        AiConversation.create_time.desc()
    ).limit(10).all()

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    for h in reversed(history):
        messages.append({'role': h.role, 'content': h.content})
    messages.append({'role': 'user', 'content': user_message})

    # 调用 DeepSeek API
    try:
        reply = _call_deepseek(messages)
    except Exception as e:
        logger.error(f'DeepSeek API 调用失败: {e}')
        reply = f'抱歉，AI服务暂时不可用（{str(e)}）。请稍后重试或联系管理员。'

    # 保存 AI 回复
    ai_msg = AiConversation(user_id=user_id, role='assistant', content=reply)
    db.session.add(ai_msg)
    db.session.commit()

    return reply


def recommend_books(user_id):
    """AI 图书推荐

    Args:
        user_id: 用户ID

    Returns:
        dict: 推荐结果 { recommendations: [...], summary: '...' }
    """
    # 获取所有在架图书
    books = Book.query.filter_by(is_deleted=False).all()
    books_data = [{
        'id': b.id,
        'title': b.title,
        'author': b.author,
        'category': b.category.name if b.category else '',
        'description': b.description or '',
        'stock': b.stock,
    } for b in books]

    # 获取用户借阅历史
    from models.borrow import Borrow
    borrows = Borrow.query.filter_by(user_id=user_id).order_by(
        Borrow.create_time.desc()
    ).limit(10).all()
    borrow_history = [{
        'title': b.book.title if b.book else '',
        'author': b.book.author if b.book else '',
        'category': b.book.category.name if b.book and b.book.category else '',
    } for b in borrows]

    # 构造 prompt
    prompt = RECOMMEND_PROMPT_TEMPLATE.format(
        books_json=json.dumps(books_data, ensure_ascii=False),
        borrow_history=json.dumps(borrow_history, ensure_ascii=False),
    )

    messages = [
        {'role': 'system', 'content': '你是一个专业的图书推荐助手。请严格按JSON格式回复。'},
        {'role': 'user', 'content': prompt},
    ]

    try:
        reply = _call_deepseek(messages)
        # 尝试解析 JSON
        result = json.loads(reply)
    except Exception as e:
        logger.error(f'AI推荐解析失败: {e}')
        # 降级方案：按借阅量推荐
        from sqlalchemy import func
        top_books = db.session.query(
            Book.id, Book.title, Book.author, func.count(Borrow.id).label('cnt')
        ).join(Borrow, Book.id == Borrow.book_id).filter(
            Book.is_deleted == False
        ).group_by(Book.id).order_by(func.count(Borrow.id).desc()).limit(5).all()

        recommendations = [{
            'book_id': b.id,
            'title': b.title,
            'author': b.author,
            'reason': '热门图书',
        } for b in top_books]

        result = {
            'recommendations': recommendations,
            'summary': '根据图书馆热门借阅数据推荐',
        }

    return result


def chat_stream(user_id, user_message):
    """AI 对话（流式）

    生成器函数，逐块返回 AI 回复内容
    """
    # 保存用户消息
    user_msg = AiConversation(user_id=user_id, role='user', content=user_message)
    db.session.add(user_msg)
    db.session.commit()

    # 获取历史对话
    history = AiConversation.query.filter_by(user_id=user_id).order_by(
        AiConversation.create_time.desc()
    ).limit(10).all()

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    for h in reversed(history):
        messages.append({'role': h.role, 'content': h.content})
    messages.append({'role': 'user', 'content': user_message})

    full_reply = ''

    try:
        stream = _call_deepseek(messages, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_reply += content
                yield content
    except Exception as e:
        error_msg = f'抱歉，AI服务暂时不可用。错误：{str(e)}'
        full_reply = error_msg
        yield error_msg

    # 保存 AI 回复
    ai_msg = AiConversation(user_id=user_id, role='assistant', content=full_reply)
    db.session.add(ai_msg)
    db.session.commit()
