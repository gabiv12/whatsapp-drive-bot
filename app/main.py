import json
from typing import List, Optional
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.twiml.messaging_response import MessagingResponse

from app.config import Config
from app.conversation import process_message
from app.folder_catalog import (
    create_folder,
    format_folder_label,
    get_folders_by_person,
    get_persons_catalog,
    rename_folder,
)
from app.storage import get_conversation, read_json, write_json


app = FastAPI(title="WhatsApp Drive Bot - Simulacion")


class WhatsAppWebhook(BaseModel):
    user_id: str
    text: Optional[str] = ""
    media_count: Optional[int] = 0
    media_names: Optional[List[str]] = []


class FolderCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


def get_extension_from_content_type(content_type):
    content_type = (content_type or "").lower().split(";")[0].strip()
    extensions = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "audio/mpeg": ".mp3",
        "video/mp4": ".mp4",
        "text/plain": ".txt",
    }
    return extensions.get(content_type, ".bin")


async def parse_json_payload(request):
    data = await parse_json_body(request)
    media_count = int(data.get("media_count") or 0)
    media_names = data.get("media_names") or []
    return {
        "source": "json",
        "user_id": data.get("user_id"),
        "text": data.get("text") or "",
        "media_count": media_count,
        "media_names": media_names,
    }


async def parse_twilio_form_payload(request):
    content_type = request.headers.get("content-type", "").lower()
    if "application/x-www-form-urlencoded" in content_type:
        body = await request.body()
        parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
        form = {key: values[0] if values else "" for key, values in parsed.items()}
    else:
        form_data = await request.form()
        form = {key: value for key, value in form_data.items()}

    media_count = int(form.get("NumMedia") or 0)
    media_names = []

    for index in range(media_count):
        content_type = form.get(f"MediaContentType{index}") or ""
        extension = get_extension_from_content_type(content_type)
        media_names.append(f"twilio_media_{str(index + 1).zfill(3)}{extension}")

    return {
        "source": "twilio",
        "user_id": form.get("From"),
        "text": form.get("Body") or "",
        "media_count": media_count,
        "media_names": media_names,
    }


async def parse_payload(request):
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        return await parse_json_payload(request)
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        return await parse_twilio_form_payload(request)
    raise HTTPException(status_code=415, detail="Unsupported content type")


async def parse_json_body(request):
    body = await request.body()
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return json.loads(body.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise HTTPException(status_code=400, detail="Invalid JSON body")


def handle_incoming_message(user_id, text, media_count, media_names):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    bot_message = process_message(
        user_id=user_id,
        text=text or "",
        media_count=media_count or 0,
        media_names=media_names or [],
    )
    state = get_conversation(user_id)
    return bot_message, state


@app.get("/")
async def root():
    return {"status": "online", "message": "WhatsApp Drive Bot Simulado"}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    payload = await parse_payload(request)
    bot_message, state = handle_incoming_message(
        payload["user_id"],
        payload["text"],
        payload["media_count"],
        payload["media_names"],
    )
    return {
        "status": "processed",
        "user_id": payload["user_id"],
        "bot_message": bot_message,
        "state": state.get("state"),
    }


@app.post("/webhook/twilio-debug")
async def twilio_debug_webhook(request: Request):
    payload = await parse_twilio_form_payload(request)
    bot_message, _state = handle_incoming_message(
        payload["user_id"],
        payload["text"],
        payload["media_count"],
        payload["media_names"],
    )

    twiml_response = MessagingResponse()
    twiml_response.message(bot_message)
    return Response(content=str(twiml_response), media_type="application/xml")


@app.post("/webhook/twilio-json-debug")
async def twilio_json_debug_webhook(request: Request):
    payload = await parse_twilio_form_payload(request)
    bot_message, state = handle_incoming_message(
        payload["user_id"],
        payload["text"],
        payload["media_count"],
        payload["media_names"],
    )
    return {
        "status": "processed",
        "source": "twilio",
        "user_id": payload["user_id"],
        "media_names": payload["media_names"],
        "bot_message": bot_message,
        "state": state.get("state"),
    }


@app.get("/persons")
async def get_persons():
    return [{"key": key, "name": name} for key, name in get_persons_catalog().items()]


@app.get("/folders/{person_key}")
async def get_folders(person_key: str):
    folders = get_folders_by_person(person_key)
    if person_key not in get_persons_catalog():
        raise HTTPException(status_code=404, detail="Person not found")
    return [{**folder, "label": format_folder_label(folder)} for folder in folders]


@app.post("/folders/{person_key}")
async def api_create_folder(person_key: str, request: Request):
    data = await parse_json_body(request)
    folder = create_folder(person_key, data.get("name"), data.get("description"))
    if not folder:
        raise HTTPException(status_code=404, detail="Person not found")
    return folder


@app.put("/folders/{person_key}/{folder_input}/rename")
async def api_rename_folder(person_key: str, folder_input: str, request: Request):
    data = await parse_json_body(request)
    if not data.get("name"):
        raise HTTPException(status_code=400, detail="name is required")
    result = rename_folder(person_key, folder_input, data.get("name"), data.get("description"))
    if result["status"] == "ambiguous":
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Encontré más de una carpeta con ese nombre. Elegí una opción específica.",
                "matches": [
                    {**folder, "label": format_folder_label(folder)}
                    for folder in result["matches"]
                ],
            },
        )
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Folder not found")
    return {
        "status": "updated",
        "warning": result["warning"],
        "folder": result["folder"],
    }


@app.get("/debug/conversations")
async def debug_conversations():
    return read_json(Config.CONVERSATIONS_FILE)


@app.get("/debug/pending")
async def debug_pending():
    return read_json(Config.PENDING_FILE)


@app.get("/debug/folders")
async def debug_folders():
    return read_json(Config.FOLDERS_FILE)


@app.post("/debug/reset")
async def debug_reset():
    write_json(Config.CONVERSATIONS_FILE, {})
    write_json(Config.PENDING_FILE, {})
    return {"message": "Conversations and pending uploads reset successful"}
