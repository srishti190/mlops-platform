from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.organization import Organization
from ..schemas.organization import OrganizationCreate, Organization as OrganizationSchema
from .auth import get_current_user

router = APIRouter()

def check_admin_access(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

@router.post("/", response_model=OrganizationSchema)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only allow creating org if user is not in one or is admin
    if current_user.organization_id and current_user.role != "admin":
        raise HTTPException(status_code=400, detail="User already belongs to an organization")
    
    organization = Organization(**org_data.dict())
    db.add(organization)
    db.commit()
    db.refresh(organization)
    
    # Add creator to organization as admin
    if not current_user.organization_id:
        current_user.organization_id = organization.id
        current_user.role = "admin"
        db.commit()
    
    return organization

@router.get("/my", response_model=OrganizationSchema)
async def get_my_organization(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=404, detail="User is not part of any organization")
    
    organization = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return organization

@router.get("/{org_id}/invite-code")
async def get_invite_code(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    check_admin_access(current_user)
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {"invite_code": organization.invite_code}

@router.post("/{org_id}/regenerate-invite-code")
async def regenerate_invite_code(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.organization_id != org_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    check_admin_access(current_user)
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    import secrets
    organization.invite_code = secrets.token_urlsafe(16)
    db.commit()
    
    return {"invite_code": organization.invite_code} 