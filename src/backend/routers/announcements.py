"""
Announcements router voor CRUD acties
"""
from fastapi import APIRouter, Depends, HTTPException
from ..database import announcements_collection
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from .auth import get_current_user

class Announcement(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    message: str
    expiration_date: str
    start_date: Optional[str] = None

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

@router.get("/", response_model=List[Announcement])
def get_announcements():
    now = datetime.now().strftime("%Y-%m-%d")
    announcements = list(announcements_collection.find({
        "expiration_date": {"$gte": now}
    }))
    return announcements

@router.post("/", response_model=Announcement)
def create_announcement(announcement: Announcement, user=Depends(get_current_user)):
    if not announcement.expiration_date:
        raise HTTPException(status_code=400, detail="Expiration date is required.")
    doc = announcement.dict(by_alias=True, exclude_unset=True, exclude={"id"})
    # Ensure that the database controls the _id field
    doc.pop("_id", None)
    result = announcements_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc

@router.put("/{announcement_id}", response_model=Announcement)
def update_announcement(announcement_id: str, announcement: Announcement, user=Depends(get_current_user)):
    doc = announcement.dict(by_alias=True, exclude_unset=True, exclude={"id"})
    # Do not attempt to update the MongoDB _id field
    doc.pop("_id", None)
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": doc})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    doc["_id"] = announcement_id
    return doc

@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, user=Depends(get_current_user)):
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return {"success": True}
