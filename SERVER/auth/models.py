from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Literal, Optional

class SignUpRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, example="Ahmed Khanzada")
    email: EmailStr = Field(..., example="ahmed@example.com")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_]+$",
        example="ahmed_k"
    )
    password: str = Field(..., min_length=6, max_length=128, example="StrongPassword123!")
    role: Literal["Employee", "Team Lead", "HR Executive", "HR Manager"] = Field(..., example="Employee")
    
    team_lead_username: Optional[str] = Field(
        None,
        description="Required only when role is 'Employee' — username of the Team Lead"
    )

    @model_validator(mode='after')
    def validate_team_lead(self):
        if self.role == "Employee" and not self.team_lead_username:
            raise ValueError("When role is 'Employee', team_lead_username is required")
        return self


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., example="ahmed@example.com")


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    @model_validator(mode='after')
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewStrongPass123!",
                "confirm_password": "NewStrongPass123!"
            }
        }

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Ahmed Khanzada",
                "email": "ahmed@example.com",
                "username": "ahmed_k",
                "password": "StrongPassword123!",
                "role": "employee"
            }
        }