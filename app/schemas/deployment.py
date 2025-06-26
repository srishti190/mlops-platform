from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.deployment import DeploymentStatus, DeploymentPriority

class DeploymentBase(BaseModel):
    name: str
    docker_image: str
    required_ram_gb: float
    required_cpu_cores: float
    required_gpu_count: int = 0
    priority: DeploymentPriority = DeploymentPriority.MEDIUM

class DeploymentCreate(DeploymentBase):
    cluster_id: int
    depends_on_deployment_id: Optional[int] = None

class DeploymentUpdate(BaseModel):
    priority: Optional[DeploymentPriority] = None
    status: Optional[DeploymentStatus] = None

class Deployment(DeploymentBase):
    id: int
    cluster_id: int
    user_id: int
    status: DeploymentStatus
    depends_on_deployment_id: Optional[int]
    created_at: datetime
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True 