from app.config import Config
from app.drive_service import upload_to_drive
from app.file_service import process_received_files
from app.folder_catalog import (
    format_folder_label,
    get_folders_by_person,
    get_person_display_name,
    resolve_folder_input,
    resolve_person,
)
from app.storage import get_conversation, read_json, save_conversation, write_json
from app.twilio_service import send_whatsapp_message


PERSON_OPTIONS_MESSAGE = "1. Fernando Gutman\n2. Pablo Sanchez"
START_MESSAGE = "Hola. Enviame uno o varios archivos para empezar a organizarlos."

PERSON_ALIASES = [
    ("fernando_gutman", "fernando gutman"),
    ("pablo_sanchez", "pablo sanchez"),
    ("fernando_gutman", "fernando"),
    ("fernando_gutman", "gutman"),
    ("pablo_sanchez", "pablo"),
    ("pablo_sanchez", "sanchez"),
    ("fernando_gutman", "1"),
    ("pablo_sanchez", "2"),
]


def _format_folder_options(folders):
    return "\n".join(f"{folder['option']}. {format_folder_label(folder)}" for folder in folders)


def _format_ambiguous_folder_message(matches):
    folder_list = _format_folder_options(matches)
    return f"Encontré más de una carpeta con ese nombre. Elegí una opción:\n\n{folder_list}"


def _format_folder_question(person_display_name, folders):
    folder_list = _format_folder_options(folders)
    return f"¿En qué carpeta de {person_display_name} querés guardarlos?\n\n{folder_list}"


def _format_person_question(file_count):
    return f"Recibí {file_count} archivo/s. ¿Para quién son?\n\n{PERSON_OPTIONS_MESSAGE}"


def _save_pending_files(user_id, files):
    pending = read_json(Config.PENDING_FILE)
    pending[user_id] = files
    write_json(Config.PENDING_FILE, pending)


def _clear_pending_files(user_id):
    pending = read_json(Config.PENDING_FILE)
    pending.pop(user_id, None)
    write_json(Config.PENDING_FILE, pending)


def _finish_upload(user_id, person_key, folder_data, files):
    person_display_name = get_person_display_name(person_key)
    upload_to_drive(person_key, person_display_name, folder_data, files)

    state_data = {
        "state": "finished",
        "selected_person": person_key,
    }
    save_conversation(user_id, state_data)
    _clear_pending_files(user_id)

    return (
        f"Listo. Guardé {len(files)} archivo/s en "
        f"{person_display_name} / {folder_data['name']}."
    )


def parse_quick_command(text):
    clean_text = " ".join((text or "").strip().split())
    if not clean_text:
        return {"person_key": None, "folder_input": ""}

    full_person_key = resolve_person(clean_text)
    if full_person_key:
        return {"person_key": full_person_key, "folder_input": ""}

    lower_text = clean_text.lower()
    for person_key, alias in PERSON_ALIASES:
        if lower_text == alias:
            return {"person_key": person_key, "folder_input": ""}
        if lower_text.startswith(f"{alias} "):
            folder_input = clean_text[len(alias):].strip()
            return {"person_key": person_key, "folder_input": folder_input}

    return {"person_key": None, "folder_input": clean_text}


def _handle_folder_result(user_id, person_key, folder_result, files, invalid_intro=None):
    person_display_name = get_person_display_name(person_key)
    folders = get_folders_by_person(person_key)

    if folder_result["status"] == "found":
        return _finish_upload(user_id, person_key, folder_result["folder"], files)

    state_data = {
        "state": "waiting_folder",
        "selected_person": person_key,
    }
    save_conversation(user_id, state_data)

    if folder_result["status"] == "ambiguous":
        return _format_ambiguous_folder_message(folder_result["matches"])

    folder_list = _format_folder_options(folders)
    intro = invalid_intro or f"No encontré esa carpeta para {person_display_name}."
    return f"{intro} Elegí una opción:\n\n{folder_list}"


def process_files_with_optional_command(user_id, text, media_count, media_names=None):
    files = process_received_files(media_count, media_names)
    clean_text = (text or "").strip()

    if not clean_text:
        _save_pending_files(user_id, files)
        state_data = {"state": "waiting_person"}
        save_conversation(user_id, state_data)
        return _format_person_question(len(files))

    command = parse_quick_command(clean_text)
    person_key = command["person_key"]
    folder_input = command["folder_input"]

    if person_key and folder_input:
        _save_pending_files(user_id, files)
        folder_result = resolve_folder_input(person_key, folder_input)
        return _handle_folder_result(user_id, person_key, folder_result, files)

    if person_key:
        _save_pending_files(user_id, files)
        state_data = {
            "state": "waiting_folder",
            "selected_person": person_key,
        }
        save_conversation(user_id, state_data)

        person_display_name = get_person_display_name(person_key)
        folders = get_folders_by_person(person_key)
        return _format_folder_question(person_display_name, folders)

    _save_pending_files(user_id, files)
    state_data = {
        "state": "waiting_person",
        "pending_folder_input": folder_input,
    }
    save_conversation(user_id, state_data)
    return _format_person_question(len(files))


def process_message(user_id, text, media_count=0, media_names=None):
    state_data = get_conversation(user_id)
    current_state = state_data.get("state", "waiting_files")
    text = text or ""

    if media_count > 0:
        msg = process_files_with_optional_command(user_id, text, media_count, media_names)
        return send_whatsapp_message(user_id, msg)

    if current_state == "waiting_person":
        person_key = resolve_person(text)
        if not person_key:
            return send_whatsapp_message(
                user_id,
                f"No entendí la persona. Elegí una opción:\n{PERSON_OPTIONS_MESSAGE}",
            )

        pending = read_json(Config.PENDING_FILE)
        files_to_upload = pending.get(user_id, [])
        pending_folder_input = state_data.get("pending_folder_input")

        if pending_folder_input:
            folder_result = resolve_folder_input(person_key, pending_folder_input)
            if folder_result["status"] == "found":
                msg = _finish_upload(user_id, person_key, folder_result["folder"], files_to_upload)
                return send_whatsapp_message(user_id, msg)

            invalid_intro = f"No encontré esa carpeta para {get_person_display_name(person_key)}."
            msg = _handle_folder_result(
                user_id,
                person_key,
                folder_result,
                files_to_upload,
                invalid_intro=invalid_intro,
            )
            return send_whatsapp_message(user_id, msg)

        person_display_name = get_person_display_name(person_key)
        state_data["state"] = "waiting_folder"
        state_data["selected_person"] = person_key
        state_data.pop("pending_folder_input", None)
        save_conversation(user_id, state_data)

        folders = get_folders_by_person(person_key)
        msg = _format_folder_question(person_display_name, folders)
        return send_whatsapp_message(user_id, msg)

    if current_state == "waiting_folder":
        person_key = state_data.get("selected_person")
        person_display_name = get_person_display_name(person_key)
        folder_result = resolve_folder_input(person_key, text)

        if folder_result["status"] == "ambiguous":
            return send_whatsapp_message(user_id, _format_ambiguous_folder_message(folder_result["matches"]))

        selected_folder = folder_result["folder"]
        if not person_display_name or not selected_folder:
            return send_whatsapp_message(
                user_id,
                "Carpeta no válida. Por favor elegí un número, el código o el nombre visible.",
            )

        pending = read_json(Config.PENDING_FILE)
        files_to_upload = pending.get(user_id, [])
        msg = _finish_upload(user_id, person_key, selected_folder, files_to_upload)
        return send_whatsapp_message(user_id, msg)

    state_data["state"] = "waiting_files"
    save_conversation(user_id, state_data)
    return send_whatsapp_message(user_id, START_MESSAGE)
