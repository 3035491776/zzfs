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


def _call_deepseek(messages, stream=False):
    """调用 DeepSeek API (OpenAI 兼容模式)

    Args:
        messages: 消息列表
        stream: 是否流式

    Returns:
        str: AI 回复内容
    """
    import openai

    api_key = current_app.config.get('DEEPSEEK_API_KEY', 'your-deepseek-api-key')
    base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    if stream:
        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=messages,
            stream=True,
        )
        return response  # 返回流对象
    else:
        response = client.chat.completions.create(
            model='deepseek-chat',
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content


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
