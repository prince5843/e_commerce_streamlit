from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

# Authenticate and return a GoogleDrive object
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Will prompt in browser on first run
    drive = GoogleDrive(gauth)
    return drive

# Get or create a folder in Google Drive, optionally under a parent folder
def get_or_create_folder(drive, folder_name, parent_id=None):
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    file_list = drive.ListFile({'q': query}).GetList()
    if file_list:
        return file_list[0]['id']
    # Create folder if not found
    folder_metadata = {'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        folder_metadata['parents'] = [{'id': parent_id}]
    folder = drive.CreateFile(folder_metadata)
    folder.Upload()
    return folder['id']

# Upload an image to a specific folder in Google Drive and return its public link
def upload_image_to_drive(drive, local_path, folder_id):
    file_name = os.path.basename(local_path)
    gfile = drive.CreateFile({'parents': [{'id': folder_id}], 'title': file_name})
    gfile.SetContentFile(local_path)
    gfile.Upload()
    # Make file shareable
    gfile.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
    return f"https://drive.google.com/uc?id={gfile['id']}"