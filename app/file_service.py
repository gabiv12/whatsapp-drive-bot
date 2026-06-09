def process_received_files(media_count: int, media_names: list = None) -> list:
    if media_names and len(media_names) > 0:
        return list(media_names)

    return [f"archivo_{str(index).zfill(3)}.pdf" for index in range(1, media_count + 1)]
