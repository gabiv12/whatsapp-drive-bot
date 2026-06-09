def upload_to_drive(person_key, person_display_name, folder_data, files):
    # Etapa futura:
    # - Subir cada archivo real a Google Drive usando folder_data["drive_folder_id"].
    # - El nombre visible de la carpeta puede cambiar, pero folder_data["code"] y
    #   folder_data["drive_folder_id"] deben permanecer estables.
    # - Si una carpeta se renombra, se deberá actualizar su nombre en Drive
    #   manteniendo el mismo drive_folder_id para no crear una carpeta nueva.
    print(f"[DRIVE SERVICE] Subiendo {len(files)} archivo/s...")
    for file_name in files:
        print(f" - Guardando '{file_name}' en {person_display_name} / {folder_data['name']}")

    return {
        "status": "success",
        "person_key": person_key,
        "person_display_name": person_display_name,
        "folder_code": folder_data["code"],
        "folder_name": folder_data["name"],
        "file_count": len(files),
        "files": files,
        "simulated_path": f"{person_display_name} / {folder_data['name']}",
    }
