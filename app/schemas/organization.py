from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: int
    invite_code: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrganizationWithUsers(Organization):
    users: List['User'] = [] 