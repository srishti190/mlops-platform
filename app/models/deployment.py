from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum

class DeploymentStatus(enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PREEMPTED = "preempted"

class DeploymentPriority(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Deployment(Base):
    __tablename__ = "deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    docker_image = Column(String, nullable=False)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Resource requirements
    required_ram_gb = Column(Float, nullable=False)
    required_cpu_cores = Column(Float, nullable=False)
    required_gpu_count = Column(Integer, nullable=False, default=0)
    
    # Priority and status
    priority = Column(Enum(DeploymentPriority), default=DeploymentPriority.MEDIUM)
    status = Column(Enum(DeploymentStatus), default=DeploymentStatus.PENDING)
    
    # Dependency management
    depends_on_deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    cluster = relationship("Cluster", back_populates="deployments")
    user = relationship("User", back_populates="deployments")
    depends_on = relationship("Deployment", remote_side=[id]) 