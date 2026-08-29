import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.models import AIChatSession, AIChatMessage, User
from app.schemas.chat import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChoice,
    ChatMessage, ChatUsage, ChatSessionResponse, ChatSessionListResponse,
    ChatMessageResponse,
)
from app.schemas.common import BaseResponse
from app.services.ai_scheduler import get_scheduler, AIScheduler
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/chat", tags=["Chat对话"])


@router.post("/completions")
async def chat_completions(
    req: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    scheduler: AIScheduler = Depends(get_scheduler),
    current_user: User = Depends(get_current_user),
):
    client = await scheduler.get_chat_client(db, req.model_id)
    model = await scheduler._get_model(db, req.model_id)

    if req.stream:
        return StreamingResponse(
            _stream_chat(client, model.model_name, req.messages, db, req.session_id, req.model_id, current_user.id),
            media_type="text/event-stream",
        )

    result = await client.chat_completion(
        messages=[m.model_dump() for m in req.messages],
        model_name=model.model_name,
        stream=False,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )

    session_id = await _ensure_session(db, req.session_id, current_user.id, req.model_id)
    token_count = (result.get("usage") or {}).get("total_tokens", 0)
    await _save_chat_history(db, req.messages, session_id, result, token_count)
    return BaseResponse(data=result)


async def _stream_chat(client, model_name, messages, db, session_id, model_id, user_id):
    history_messages = [m.model_dump() for m in messages]
    full_content = ""
    token_count = 0
    request_id = uuid.uuid4().hex[:16]

    try:
        stream_iter = await client.chat_completion(
            messages=history_messages,
            model_name=model_name,
            stream=True,
        )
        async for chunk in stream_iter:
            if chunk.get("usage"):
                usage = chunk.get("usage") or {}
                token_count = usage.get("total_tokens", 0)
            if "choices" in chunk and chunk["choices"]:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    full_content += content
                    yield f"data: {json.dumps({'id': request_id, 'choices': [{'delta': {'content': content}}]})}\n\n"

        yield "data: [DONE]\n\n"

        if full_content:
            session_id = await _ensure_session(db, session_id, user_id, model_id)
            await _save_stream_history(db, messages, full_content, session_id, token_count)
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def _ensure_session(db, session_id, user_id, model_id):
    """确保会话存在，返回有效会话ID。前端在首个请求提供的就是新建会话ID。"""
    if session_id:
        result = await db.execute(select(AIChatSession).where(AIChatSession.id == session_id))
        if result.scalar_one_or_none():
            return session_id
    new_id = session_id or uuid.uuid4().hex[:16]
    db.add(AIChatSession(id=new_id, user_id=user_id, model_id=model_id))
    return new_id


def _last_user_message(messages):
    if not messages:
        return None
    for msg in reversed(messages):
        if msg.role == "user":
            return msg
    return None


async def _save_chat_history(db, messages, session_id, result, token_count=0):
    # 历史消息已在之前请求中入库，这里只追加本轮新增的用户消息与助手回复，避免重复
    new_user = _last_user_message(messages)
    if new_user:
        db.add(AIChatMessage(session_id=session_id, role=new_user.role, content=new_user.content))

    if "choices" in result and result["choices"]:
        assistant_content = result["choices"][0].get("message", {}).get("content", "")
        if assistant_content:
            db.add(AIChatMessage(
                session_id=session_id, role="assistant", content=assistant_content,
                token_count=token_count,
            ))


async def _save_stream_history(db, messages, full_content, session_id, token_count=0):
    new_user = _last_user_message(messages)
    if new_user:
        db.add(AIChatMessage(session_id=session_id, role=new_user.role, content=new_user.content))
    db.add(AIChatMessage(
        session_id=session_id, role="assistant", content=full_content,
        token_count=token_count,
    ))


@router.get("/sessions")
async def list_sessions(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AIChatSession)
        .where(AIChatSession.user_id == current_user.id)
        .order_by(AIChatSession.update_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    sessions = result.scalars().all()

    count_result = await db.execute(
        select(AIChatSession).where(AIChatSession.user_id == current_user.id)
    )
    total = len(count_result.scalars().all())

    return BaseResponse(data={
        "sessions": [ChatSessionResponse.model_validate(s) for s in sessions],
        "total": total,
    })


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AIChatMessage).where(AIChatMessage.session_id == session_id))
    messages = result.scalars().all()
    if not messages:
        raise HTTPException(status_code=404, detail="会话不存在")
    return BaseResponse(data=[ChatMessageResponse.model_validate(m) for m in messages])


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AIChatSession).where(AIChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    await db.delete(session)
    return BaseResponse(msg="会话已删除")


@router.get("/usage")
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_session_ids = select(AIChatSession.id).where(AIChatSession.user_id == current_user.id)
    total = (await db.execute(
        select(func.coalesce(func.sum(AIChatMessage.token_count), 0))
        .where(AIChatMessage.session_id.in_(user_session_ids))
    )).scalar() or 0
    return BaseResponse(data={"total_tokens": int(total)})