from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClusterBase(BaseModel):
    name: str
    total_ram_gb: float
    total_cpu_cores: float
    total_gpu_count: int = 0

class ClusterCreate(ClusterBase):
    pass

class ClusterUpdate(BaseModel):
    name: Optional[str] = None

class Cluster(ClusterBase):
    id: int
    organization_id: int
    available_ram_gb: float
    available_cpu_cores: float
    available_gpu_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClusterResources(BaseModel):
    total_ram_gb: float
    total_cpu_cores: float
    total_gpu_count: int
    available_ram_gb: float
    available_cpu_cores: float
    available_gpu_count: int
    utilization_percentage: float 