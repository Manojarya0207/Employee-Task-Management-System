from pydantic import BaseModel, Field, field_validator
from datetime import date
import re

class LoginRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class RegisterRequest(BaseModel):
    employee_name: str = Field(..., min_length=3)
    phone_number: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6)
    department: str | None = None

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        digits = re.sub(r'\D', '', v)
        if len(digits) != 10:
            raise ValueError('Phone number must have exactly 10 digits')
        return digits

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    status: str = Field(..., min_length=1)

class TaskUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    status: str = Field(..., min_length=1)

class EmployeeCreateRequest(BaseModel):
    employee_id: str = Field(..., min_length=1)
    employee_name: str = Field(..., min_length=3)
    phone_number: str = Field(..., min_length=10)
    password: str = Field(..., min_length=6)
    role: str = "employee"
    department: str | None = None
    joining_date: date | None = None

class EmployeeUpdateRequest(BaseModel):
    employee_name: str = Field(..., min_length=3)
    phone_number: str = Field(..., min_length=10)
    department: str | None = None
    status: str = Field(..., min_length=1)

class StatusCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    color: str = Field("#000000", min_length=4, max_length=7)
