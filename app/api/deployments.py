from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.deployment import Deployment, DeploymentStatus
from ..schemas.deployment import DeploymentCreate, Deployment as DeploymentSchema, DeploymentUpdate
from ..services.deployment_service import DeploymentService
from .auth import get_current_user

router = APIRouter()

@router.post("/", response_model=DeploymentSchema)
async def create_deployment(
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    service = DeploymentService(db)
    
    try:
        deployment = service.create_deployment(deployment_data, current_user.id)
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[DeploymentSchema])
async def list_deployments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DeploymentService(db)
    
    if current_user.role == "admin":
        # Admin can see all deployments in organization
        deployments = db.query(Deployment).join(Deployment.cluster).filter(
            Deployment.cluster.has(organization_id=current_user.organization_id)
        ).all()
    else:
        # Regular users see only their deployments
        deployments = service.get_deployments_by_user(current_user.id)
    
    return deployments

@router.get("/{deployment_id}", response_model=DeploymentSchema)
async def get_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check access permissions
    if current_user.role != "admin" and deployment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return deployment

@router.patch("/{deployment_id}", response_model=DeploymentSchema)
async def update_deployment(
    deployment_id: int,
    deployment_update: DeploymentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Check permissions
    if current_user.role != "admin" and deployment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Update fields
    for field, value in deployment_update.dict(exclude_unset=True).items():
        setattr(deployment, field, value)
    
    db.commit()
    db.refresh(deployment)
    
    return deployment

@router.post("/{deployment_id}/cancel")
async def cancel_deployment(
    deployment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DeploymentService(db)
    
    if service.cancel_deployment(deployment_id, current_user.id):
        return {"message": "Deployment cancelled successfully"}
    else:
        raise HTTPException(status_code=404, detail="Deployment not found or cannot be cancelled")

@router.get("/cluster/{cluster_id}", response_model=List[DeploymentSchema])
async def list_cluster_deployments(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DeploymentService(db)
    deployments = service.get_deployments_by_cluster(cluster_id)
    
    # Filter based on user permissions
    if current_user.role != "admin":
        deployments = [d for d in deployments if d.user_id == current_user.id]
    
    return deployments 