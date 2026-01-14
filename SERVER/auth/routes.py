from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .models import SignUpRequest, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from .hash_utils import hash_password, verify_password
from config.db import users_collection
from utils.email_utils import generate_token, verify_token, send_email, SALT_EMAIL, SALT_RESET
from typing import Dict, Any
from datetime import datetime

router = APIRouter()
security = HTTPBasic()

async def authenticate(username: str, password: str) -> Dict[str, Any]:
    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(password, user.get("password", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.get("is_verified", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return {
        "username": user["username"],
        "role": user.get("role", "Employee")
    }

async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    return await authenticate(credentials.username, credentials.password)

def get_verification_link(email: str):
    token = generate_token(email, SALT_EMAIL)
    return f"http://localhost:8501/?action=verify-email&token={token}"

def get_reset_link(email: str):
    token = generate_token(email, SALT_RESET)
    return f"http://localhost:8501/?action=reset-password&token={token}"

@router.post("/login")
async def login(req: LoginRequest):
    user = await authenticate(req.username, req.password)
    return {"message": f"Welcome {user['username']}", "role": user["role"]}

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(req: SignUpRequest, background_tasks: BackgroundTasks):
    existing_user = await users_collection.find_one(
        {"$or": [{"username": req.username}, {"email": req.email}]}
    )
    if existing_user:
        if existing_user.get("username") == req.username:
            raise HTTPException(status_code=400, detail=f'Username "{req.username}" already exists')
        else:
            raise HTTPException(status_code=400, detail=f'Email "{req.email}" already exists')

    if req.role == "HR Manager":
        if await users_collection.find_one({"role": "HR Manager"}):
            raise HTTPException(status_code=400, detail="Only one HR Manager is allowed")

    if req.role == "Team Lead":
        count = await users_collection.count_documents({"role": "Team Lead"})
        if count >= 4:
            raise HTTPException(status_code=400, detail="Maximum 4 Team Leads allowed")

    hashed_pwd = hash_password(req.password)
    user_data = {
        "email": req.email,
        "username": req.username,
        "full_name": req.full_name,
        "password": hashed_pwd,
        "role": req.role,
        "is_verified": False,
        "created_at": datetime.utcnow()
    }

    if req.role == "Employee":
        if not req.team_lead_username:
            raise HTTPException(status_code=400, detail="Employee must have a team_lead_username")
        
        team_lead = await users_collection.find_one({
            "username": req.team_lead_username,
            "role": "Team Lead"
        })
        if not team_lead:
            raise HTTPException(status_code=400, detail="Invalid or non-existent Team Lead username")
        
        user_data["team_lead"] = req.team_lead_username

    await users_collection.insert_one(user_data)

    background_tasks.add_task(
        send_email,
        req.email,
        "Email Verification - HR System",
        f"Click here to verify your email: {get_verification_link(req.email)}"
    )

    return {"message": "User created. Please check your email to verify."}

@router.get("/verify-email")
async def verify_email(token: str):
    email = verify_token(token, SALT_EMAIL)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get("is_verified"):
        return {"message": "Email already verified."}
    
    await users_collection.update_one({"email": email}, {"$set": {"is_verified": True}})
    return {"message": "Email verified successfully"}

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    user = await users_collection.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    background_tasks.add_task(
        send_email,
        req.email,
        "Reset Password - HR System",
        f"Click here to reset your password: {get_reset_link(req.email)}"
    )

    return {"message": "Password reset email sent"}

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    email = verify_token(req.token, SALT_RESET)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    hashed_pwd = hash_password(req.new_password)
    result = await users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_pwd}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Password updated successfully"}

@router.delete("/users/{username}")
async def delete_user(
    username: str,
    current_user: dict = Depends(get_current_user)
):
    deleter_role = current_user.get("role")
    deleter_name = current_user.get("username")

    if deleter_role != "HR Executive":
        raise HTTPException(403, "Only HR Executive can delete users")

    if username == deleter_name:
        raise HTTPException(400, "Cannot delete your own account")

    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await users_collection.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Delete failed")

    return {"message": f"User '{username}' deleted successfully"}