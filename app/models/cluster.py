from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Cluster(Base):
    __tablename__ = "clusters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Total resources
    total_ram_gb = Column(Float, nullable=False)
    total_cpu_cores = Column(Float, nullable=False)
    total_gpu_count = Column(Integer, nullable=False, default=0)
    
    # Available resources (updated dynamically)
    available_ram_gb = Column(Float, nullable=False)
    available_cpu_cores = Column(Float, nullable=False)
    available_gpu_count = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    organization = relationship("Organization", back_populates="clusters")
    deployments = relationship("Deployment", back_populates="cluster")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize available resources to total resources
        if hasattr(self, 'total_ram_gb'):
            self.available_ram_gb = self.total_ram_gb
        if hasattr(self, 'total_cpu_cores'):
            self.available_cpu_cores = self.total_cpu_cores
        if hasattr(self, 'total_gpu_count'):
            self.available_gpu_count = self.total_gpu_count 