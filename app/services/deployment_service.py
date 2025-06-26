from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ..models.deployment import Deployment, DeploymentStatus
from ..models.cluster import Cluster
from ..schemas.deployment import DeploymentCreate
from .scheduler import DeploymentScheduler

class DeploymentService:
    def __init__(self, db: Session):
        self.db = db
        self.scheduler = DeploymentScheduler(db)
    
    def create_deployment(self, deployment_data: DeploymentCreate, user_id: int) -> Deployment:
        """Create a new deployment"""
        # Validate cluster exists and user has access
        cluster = self.db.query(Cluster).filter(
            Cluster.id == deployment_data.cluster_id
        ).first()
        
        if not cluster:
            raise ValueError("Cluster not found")
        
        # Create deployment
        deployment = Deployment(
            **deployment_data.dict(),
            user_id=user_id,
            status=DeploymentStatus.PENDING
        )
        
        self.db.add(deployment)
        self.db.commit()
        self.db.refresh(deployment)
        
        # Try to schedule immediately
        self.scheduler.schedule_deployment(deployment)
        
        return deployment
    
    def get_deployments_by_user(self, user_id: int) -> List[Deployment]:
        """Get all deployments for a user"""
        return self.db.query(Deployment).filter(
            Deployment.user_id == user_id
        ).all()
    
    def get_deployments_by_cluster(self, cluster_id: int) -> List[Deployment]:
        """Get all deployments for a cluster"""
        return self.db.query(Deployment).filter(
            Deployment.cluster_id == cluster_id
        ).all()
    
    def update_deployment_status(self, deployment_id: int, status: DeploymentStatus) -> Optional[Deployment]:
        """Update deployment status"""
        deployment = self.db.query(Deployment).filter(
            Deployment.id == deployment_id
        ).first()
        
        if not deployment:
            return None
        
        old_status = deployment.status
        deployment.status = status
        
        # Handle resource cleanup on completion/failure
        if status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED] and old_status == DeploymentStatus.RUNNING:
            cluster = deployment.cluster
            cluster.available_ram_gb += deployment.required_ram_gb
            cluster.available_cpu_cores += deployment.required_cpu_cores
            cluster.available_gpu_count += deployment.required_gpu_count
            
            deployment.completed_at = func.now()
            
            # Process queue to schedule waiting deployments
            self.scheduler.process_queue(cluster.id)
        
        self.db.commit()
        self.db.refresh(deployment)
        
        return deployment
    
    def cancel_deployment(self, deployment_id: int, user_id: int) -> bool:
        """Cancel a deployment"""
        deployment = self.db.query(Deployment).filter(
            and_(
                Deployment.id == deployment_id,
                Deployment.user_id == user_id
            )
        ).first()
        
        if not deployment:
            return False
        
        if deployment.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]:
            return False
        
        return self.update_deployment_status(deployment_id, DeploymentStatus.FAILED) is not None 