from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.audio import TTSRequest, ASRResponse
from app.schemas.common import BaseResponse
from app.services.ai_scheduler import get_scheduler, AIScheduler
import io

router = APIRouter(prefix="/audio", tags=["语音TTS/ASR"])


@router.post("/tts")
async def text_to_speech(
    req: TTSRequest,
    db: AsyncSession = Depends(get_db),
    scheduler: AIScheduler = Depends(get_scheduler),
):
    client = await scheduler.get_audio_client(db, req.model_id)
    model = await scheduler._get_model(db, req.model_id)

    audio_bytes = await client.tts(
        text=req.text,
        model_name=model.model_name,
        voice=req.voice,
        speed=req.speed,
        response_format=req.response_format,
    )

    media_type_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "aac": "audio/aac",
        "flac": "audio/flac",
    }
    media_type = media_type_map.get(req.response_format, "audio/mpeg")

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=tts_output.{req.response_format}"},
    )


@router.post("/asr", response_model=BaseResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    model_id: int = None,
    language: str = None,
    db: AsyncSession = Depends(get_db),
    scheduler: AIScheduler = Depends(get_scheduler),
):
    if model_id is None:
        raise HTTPException(status_code=400, detail="model_id is required")

    client = await scheduler.get_audio_client(db, model_id)
    model = await scheduler._get_model(db, model_id)

    audio_bytes = await file.read()

    result = await client.asr(
        audio_bytes=audio_bytes,
        model_name=model.model_name,
        language=language,
    )

    return BaseResponse(data=ASRResponse(
        text=result.get("text", ""),
        language=result.get("language"),
        duration=result.get("duration"),
    ))