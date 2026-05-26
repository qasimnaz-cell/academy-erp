"""
utils/drive_upload.py
Upload files to a Google Drive folder using a service account.
Returns the shareable link.
"""
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials
from io import BytesIO
import streamlit as st

from modules.config import SERVICE_ACCOUNT_FILE, DRIVE_RECEIPTS_FOLDER

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


@st.cache_resource
def _drive_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def upload_receipt(file_obj, filename: str) -> str:
    """
    Upload a Streamlit UploadedFile to Google Drive.
    Returns the file's webViewLink (shareable URL).
    """
    service = _drive_service()

    mime_types = {
        "pdf":  "application/pdf",
        "png":  "image/png",
        "jpg":  "image/jpeg",
        "jpeg": "image/jpeg",
    }
    ext      = file_obj.name.split(".")[-1].lower()
    mimetype = mime_types.get(ext, "application/octet-stream")

    file_metadata = {
        "name":    f"{filename}.{ext}",
        "parents": [DRIVE_RECEIPTS_FOLDER] if DRIVE_RECEIPTS_FOLDER else [],
    }

    buf   = BytesIO(file_obj.read())
    media = MediaIoBaseUpload(buf, mimetype=mimetype)

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
    ).execute()

    # Make it readable by anyone with the link
    service.permissions().create(
        fileId=uploaded["id"],
        body={"role": "reader", "type": "anyone"},
    ).execute()

    return uploaded.get("webViewLink", "")
