import os, mimetypes


def read_files_in_folder(folder_path):
    files_info = []
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                # Get file size
                file_size = os.path.getsize(file_path)
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or "unknown"
                files_info.append(
                    {"filename": filename, "size": file_size, "mime_type": mime_type}
                )
    except Exception as e:
        print(f"An error occurred: {e}")

    return files_info


def check_files_in_folder(folder_path, file_list):
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        if not os.path.isfile(file_path):
            return file_name
    return None


def generate_unique_filename(directory, filename):
    """
    Generate a unique filename by adding a numeric suffix if the file already exists.

    :param directory: Directory where the file will be checked.
    :param filename: Original filename.
    :return: Unique filename.
    """
    base, extension = os.path.splitext(filename)
    new_filename = filename
    counter = 1

    # Check if the file already exists
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base}({counter}){extension}"
        counter += 1

    return new_filename
