from app.config import Config
from app.storage import read_json, write_json


PERSONS_CATALOG = {
    "fernando_gutman": "Fernando Gutman",
    "pablo_sanchez": "Pablo Sanchez",
}

DUPLICATE_NAME_WARNING = "Ya existe otra carpeta con un nombre similar para esta persona."


def get_persons_catalog():
    return PERSONS_CATALOG.copy()


def resolve_person(user_input):
    clean_input = str(user_input).lower().strip()
    if clean_input in ["1", "fernando", "fernando gutman", "gutman"]:
        return "fernando_gutman"
    if clean_input in ["2", "pablo", "pablo sanchez", "sanchez"]:
        return "pablo_sanchez"
    return None


def get_person_display_name(person_key):
    return PERSONS_CATALOG.get(person_key)


def get_folders_by_person(person_key):
    data = read_json(Config.FOLDERS_FILE)
    return data.get(person_key, [])


def format_folder_label(folder):
    code = folder["code"]
    name = folder.get("name") or code
    if name.strip().lower() == code.strip().lower():
        return code
    return f"{code} - {name}"


def _normalize_text(value):
    return " ".join(str(value).strip().lower().split())


def _normalize_folder_code(value):
    return str(value).strip().lower().replace("c", "").replace(" ", "")


def _find_matches_by_number_or_code(folders, user_input):
    clean_input = _normalize_folder_code(user_input)
    original_input = str(user_input).strip()
    matches = []

    for folder in folders:
        option = str(folder["option"]).strip()
        option_padded = option.zfill(2)
        code_num = _normalize_folder_code(folder["code"])
        if option in [original_input, original_input.lstrip("0")]:
            matches.append(folder)
        elif option_padded == original_input:
            matches.append(folder)
        elif code_num == clean_input:
            matches.append(folder)
        elif code_num.lstrip("0") == clean_input.lstrip("0"):
            matches.append(folder)

    return matches


def _find_matches_by_visible_name(folders, user_input):
    clean_input = _normalize_text(user_input)
    if not clean_input:
        return []

    exact_matches = []
    partial_matches = []
    for folder in folders:
        name = _normalize_text(folder.get("name") or "")
        if not name:
            continue
        if name == clean_input:
            exact_matches.append(folder)
        elif clean_input in name:
            partial_matches.append(folder)

    return exact_matches or partial_matches


def resolve_folder_input(person_key, user_input):
    folders = get_folders_by_person(person_key)
    code_matches = _find_matches_by_number_or_code(folders, user_input)
    if len(code_matches) == 1:
        return {"status": "found", "folder": code_matches[0], "matches": code_matches}
    if len(code_matches) > 1:
        return {"status": "ambiguous", "folder": None, "matches": code_matches}

    name_matches = _find_matches_by_visible_name(folders, user_input)
    if len(name_matches) == 1:
        return {"status": "found", "folder": name_matches[0], "matches": name_matches}
    if len(name_matches) > 1:
        return {"status": "ambiguous", "folder": None, "matches": name_matches}

    return {"status": "not_found", "folder": None, "matches": []}


def find_folder_by_input(person_key, user_input):
    result = resolve_folder_input(person_key, user_input)
    if result["status"] == "found":
        return result["folder"]
    return None


def get_next_folder_code(person_key):
    folders = get_folders_by_person(person_key)
    if not folders:
        return "C 001", "1"

    numbers = []
    for folder in folders:
        try:
            numbers.append(int(folder["code"].replace("C", "").strip()))
        except (KeyError, ValueError):
            continue

    next_num = max(numbers) + 1 if numbers else 1
    return f"C {str(next_num).zfill(3)}", str(next_num)


def create_folder(person_key, name=None, description=None):
    display_name = get_person_display_name(person_key)
    if not display_name:
        return None

    data = read_json(Config.FOLDERS_FILE)
    if person_key not in data:
        data[person_key] = []

    code, option = get_next_folder_code(person_key)

    new_folder = {
        "code": code,
        "option": option,
        "name": name if name else code,
        "description": description if description else f"Carpeta {option} de {display_name}",
        "drive_folder_id": "",
    }

    data[person_key].append(new_folder)
    write_json(Config.FOLDERS_FILE, data)
    return new_folder


def _has_similar_name(folders, new_name, current_code):
    clean_new_name = _normalize_text(new_name)
    for folder in folders:
        if folder["code"] == current_code:
            continue
        if _normalize_text(folder.get("name") or "") == clean_new_name:
            return True
    return False


def rename_folder(person_key, folder_input, new_name, new_description=None):
    if person_key not in PERSONS_CATALOG:
        return {"status": "not_found", "folder": None, "matches": [], "warning": None}

    data = read_json(Config.FOLDERS_FILE)
    if person_key not in data:
        return {"status": "not_found", "folder": None, "matches": [], "warning": None}

    result = resolve_folder_input(person_key, folder_input)
    if result["status"] != "found":
        return {**result, "warning": None}

    selected_folder = result["folder"]
    warning = None
    if _has_similar_name(data[person_key], new_name, selected_folder["code"]):
        warning = DUPLICATE_NAME_WARNING

    for stored_folder in data[person_key]:
        if stored_folder["code"] == selected_folder["code"]:
            # Cuando se conecte Google Drive real, drive_folder_id será el identificador
            # principal para actualizar la carpeta real. Renombrar deberá cambiar el
            # nombre en Drive, pero manteniendo el mismo ID.
            stored_folder["name"] = new_name
            if new_description is not None:
                stored_folder["description"] = new_description
            selected_folder = stored_folder
            break

    write_json(Config.FOLDERS_FILE, data)
    return {
        "status": "updated",
        "warning": warning,
        "folder": selected_folder,
        "matches": [selected_folder],
    }
