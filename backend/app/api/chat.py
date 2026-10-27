import asyncio
import json
import os

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.agent_service import agent_service

import sqlite3
router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


@router.post("/chat")
async def chat(req: ChatRequest):
    try:
        reply = await asyncio.to_thread(agent_service.chat, req.query)
        return {"reply": reply, "success": True}
    except Exception as e:
        return {"reply": f"出错了：{str(e)}", "success": False}


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def generate():
        yield ": connected\n\n"
        queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def producer():
            try:
                # 重点：传入 req.session_id
                for event in agent_service.stream_with_phase(req.query, session_id=req.session_id):
                    asyncio.run_coroutine_threadsafe(queue.put(("event", event)), loop)
                asyncio.run_coroutine_threadsafe(queue.put(("done", None)), loop)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(queue.put(("error", str(e))), loop)

        import threading
        threading.Thread(target=producer, daemon=True).start()

        while True:
            kind, data = await queue.get()
            if kind == "event":
                phase, content = data
                payload = json.dumps({"phase": phase, "content": content}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            elif kind == "done":
                yield "data: [DONE]\n\n"
                break
            elif kind == "error":
                yield f"data: [ERROR] {data}\n\n"
                break

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/chat/history")
async def get_chat_history():
    """获取有记录的日期列表"""
    db_path = "data/memory.db"
    if not os.path.exists(db_path):
        return {"history": []}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
        if not cursor.fetchone():
            return {"history": []}

        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        rows = cursor.fetchall()
        conn.close()

        history = [row[0] for row in rows if row[0] and row[0] != "default"]
        history.sort(reverse=True)
        return {"history": history}
    except Exception:
        return {"history": []}


# 新增：获取某一天的历史消息
@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str):
    """获取指定日期的完整聊天记录"""
    # 直接调用 agent_service 暴露的方法，拒绝底层扒表
    messages = agent_service.get_history(session_id)
    return {"messages": messages}