from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.user import User
from ..models.cluster import Cluster
from ..schemas.cluster import ClusterCreate, Cluster as ClusterSchema, ClusterResources
from .auth import get_current_user

router = APIRouter()

def check_admin_access(current_user: User):
    if current_user.role not in ["admin", "developer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

@router.post("/", response_model=ClusterSchema)
async def create_cluster(
    cluster_data: ClusterCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin_access(current_user)
    
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    cluster = Cluster(
        **cluster_data.dict(),
        organization_id=current_user.organization_id
    )
    
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    
    return cluster

@router.get("/", response_model=List[ClusterSchema])
async def list_clusters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    clusters = db.query(Cluster).filter(
        Cluster.organization_id == current_user.organization_id
    ).all()
    
    return clusters

@router.get("/{cluster_id}", response_model=ClusterSchema)
async def get_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cluster = db.query(Cluster).filter(
        Cluster.id == cluster_id,
        Cluster.organization_id == current_user.organization_id
    ).first()
    
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    return cluster

@router.get("/{cluster_id}/resources", response_model=ClusterResources)
async def get_cluster_resources(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cluster = db.query(Cluster).filter(
        Cluster.id == cluster_id,
        Cluster.organization_id == current_user.organization_id
    ).first()
    
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    utilization = 0
    if cluster.total_ram_gb > 0:
        utilization = ((cluster.total_ram_gb - cluster.available_ram_gb) / cluster.total_ram_gb) * 100
    
    return ClusterResources(
        total_ram_gb=cluster.total_ram_gb,
        total_cpu_cores=cluster.total_cpu_cores,
        total_gpu_count=cluster.total_gpu_count,
        available_ram_gb=cluster.available_ram_gb,
        available_cpu_cores=cluster.available_cpu_cores,
        available_gpu_count=cluster.available_gpu_count,
        utilization_percentage=utilization
    )

@router.delete("/{cluster_id}")
async def delete_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_admin_access(current_user)
    
    cluster = db.query(Cluster).filter(
        Cluster.id == cluster_id,
        Cluster.organization_id == current_user.organization_id
    ).first()
    
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    db.delete(cluster)
    db.commit()
    
    return {"message": "Cluster deleted successfully"} 