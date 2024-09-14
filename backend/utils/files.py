import os


def read_files_in_folder(folder_path):
    filenames = []  # List to store filenames
    try:
        # List all files and directories in the given folder
        for filename in os.listdir(folder_path):
            # Construct full file path
            file_path = os.path.join(folder_path, filename)

            # Check if it's a file
            if os.path.isfile(file_path):
                filenames.append(filename)  # Collect the filename
    except Exception as e:
        print(f"An error occurred: {e}")

    return filenames  # Return the list of filenames


def check_files_in_folder(folder_path, file_list):
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        if not os.path.isfile(file_path):
            return file_name
    return None
