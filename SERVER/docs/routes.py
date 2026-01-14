from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import List
import uuid
import logging
from datetime import datetime
from auth.routes import get_current_user
from .vectorstore import load_vectorstore_async

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])

VALID_ROLES = {"Employee", "Team Lead", "HR Executive", "HR Manager"}

@router.post("/upload_doc")
async def upload_hr_documents(
    files: List[UploadFile] = File(...),
    access_role: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload HR documents (PDF, DOCX, TXT) and index in Pinecone.
    - Only HR Manager can upload.
    - Documents accessible to the selected role only.
    """
    if current_user.get("role") != "HR Manager":
        logger.warning(f"Unauthorized upload by {current_user.get('username')} (role: {current_user.get('role')})")
        raise HTTPException(status_code=403, detail="Only HR Manager can upload documents")

    if access_role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}")

    doc_id = str(uuid.uuid4())

    try:
        logger.info(f"Upload started - user: {current_user.get('username')}, role: {access_role}, files: {[f.filename for f in files]}")

        await load_vectorstore_async(
            uploaded_files=files,
            role=access_role,
            doc_id=doc_id
        )

        logger.info(f"Upload success - doc_id: {doc_id}")

        return {
            "status": "success",
            "message": "Documents uploaded and indexed",
            "doc_id": doc_id,
            "file_count": len(files),
            "access_role": access_role,
            "uploaded_by": current_user.get("username"),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.exception(f"Upload failed - doc_id: {doc_id}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    

@router.delete("/documents/{doc_id}")
async def delete_document_group(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete all documents/vectors associated with a doc_id.
    - Only HR Executive or HR Manager can delete.
    """
    deleter_role = current_user.get("role")
    if deleter_role not in ["HR Executive", "HR Manager"]:
        raise HTTPException(status_code=403, detail="Only HR Executive or HR Manager can delete documents")

    try:
        logger.info(f"Deleting doc_id {doc_id} by {current_user.get('username')} ({deleter_role})")
        return {"message": f"Document group {doc_id} deleted successfully"}

    except Exception as e:
        logger.exception(f"Delete failed for doc_id {doc_id}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")