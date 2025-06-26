from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ..models.deployment import Deployment, DeploymentStatus, DeploymentPriority
from ..models.cluster import Cluster
import redis
import json
from ..core.config import settings

class DeploymentScheduler:
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = redis.from_url(settings.REDIS_URL)
    
    def can_schedule_deployment(self, deployment: Deployment, cluster: Cluster) -> bool:
        """Check if deployment can be scheduled on cluster based on resources"""
        return (
            cluster.available_ram_gb >= deployment.required_ram_gb and
            cluster.available_cpu_cores >= deployment.required_cpu_cores and
            cluster.available_gpu_count >= deployment.required_gpu_count
        )
    
    def check_dependencies(self, deployment: Deployment) -> bool:
        """Check if deployment dependencies are satisfied"""
        if not deployment.depends_on_deployment_id:
            return True
        
        dependency = self.db.query(Deployment).filter(
            Deployment.id == deployment.depends_on_deployment_id
        ).first()
        
        return dependency and dependency.status == DeploymentStatus.COMPLETED
    
    def get_priority_score(self, deployment: Deployment) -> int:
        """Calculate priority score for deployment"""
        base_score = deployment.priority.value * 1000
        
        # Add time-based urgency (older deployments get higher priority)
        import time
        age_hours = (time.time() - deployment.created_at.timestamp()) / 3600
        urgency_bonus = min(age_hours * 10, 100)  # Max 100 bonus points
        
        return base_score + urgency_bonus
    
    def find_preemptable_deployments(self, cluster: Cluster, required_resources: dict) -> List[Deployment]:
        """Find running deployments that can be preempted to free resources"""
        running_deployments = self.db.query(Deployment).filter(
            and_(
                Deployment.cluster_id == cluster.id,
                Deployment.status == DeploymentStatus.RUNNING
            )
        ).all()
        
        # Sort by priority (lowest first) and start time (newest first)
        running_deployments.sort(
            key=lambda d: (d.priority.value, -d.started_at.timestamp() if d.started_at else 0)
        )
        
        preemptable = []
        freed_ram = 0
        freed_cpu = 0
        freed_gpu = 0
        
        for deployment in running_deployments:
            preemptable.append(deployment)
            freed_ram += deployment.required_ram_gb
            freed_cpu += deployment.required_cpu_cores
            freed_gpu += deployment.required_gpu_count
            
            # Check if we have enough resources now
            if (
                cluster.available_ram_gb + freed_ram >= required_resources['ram'] and
                cluster.available_cpu_cores + freed_cpu >= required_resources['cpu'] and
                cluster.available_gpu_count + freed_gpu >= required_resources['gpu']
            ):
                break
        
        return preemptable
    
    def preempt_deployments(self, deployments: List[Deployment]):
        """Preempt running deployments"""
        for deployment in deployments:
            deployment.status = DeploymentStatus.PREEMPTED
            deployment.completed_at = None
            
            # Free up resources
            cluster = deployment.cluster
            cluster.available_ram_gb += deployment.required_ram_gb
            cluster.available_cpu_cores += deployment.required_cpu_cores
            cluster.available_gpu_count += deployment.required_gpu_count
            
            # Add back to queue
            self.add_to_queue(deployment)
        
        self.db.commit()
    
    def allocate_resources(self, deployment: Deployment, cluster: Cluster):
        """Allocate resources for deployment"""
        cluster.available_ram_gb -= deployment.required_ram_gb
        cluster.available_cpu_cores -= deployment.required_cpu_cores
        cluster.available_gpu_count -= deployment.required_gpu_count
        
        deployment.status = DeploymentStatus.RUNNING
        deployment.scheduled_at = func.now()
        deployment.started_at = func.now()
        
        self.db.commit()
    
    def add_to_queue(self, deployment: Deployment):
        """Add deployment to Redis queue with priority"""
        queue_data = {
            'deployment_id': deployment.id,
            'priority_score': self.get_priority_score(deployment),
            'cluster_id': deployment.cluster_id
        }
        
        # Use sorted set for priority queue
        self.redis_client.zadd(
            f"deployment_queue_{deployment.cluster_id}",
            {json.dumps(queue_data): queue_data['priority_score']}
        )
    
    def schedule_deployment(self, deployment: Deployment) -> bool:
        """Attempt to schedule a deployment"""
        cluster = self.db.query(Cluster).filter(Cluster.id == deployment.cluster_id).first()
        if not cluster:
            return False
        
        # Check dependencies
        if not self.check_dependencies(deployment):
            return False
        
        # Check if resources are available
        if self.can_schedule_deployment(deployment, cluster):
            self.allocate_resources(deployment, cluster)
            return True
        
        # Try preemption for high-priority deployments
        if deployment.priority.value >= DeploymentPriority.HIGH.value:
            required_resources = {
                'ram': deployment.required_ram_gb,
                'cpu': deployment.required_cpu_cores,
                'gpu': deployment.required_gpu_count
            }
            
            preemptable = self.find_preemptable_deployments(cluster, required_resources)
            if preemptable:
                # Check if preemption would help
                total_freed_ram = sum(d.required_ram_gb for d in preemptable)
                total_freed_cpu = sum(d.required_cpu_cores for d in preemptable)
                total_freed_gpu = sum(d.required_gpu_count for d in preemptable)
                
                if (
                    cluster.available_ram_gb + total_freed_ram >= deployment.required_ram_gb and
                    cluster.available_cpu_cores + total_freed_cpu >= deployment.required_cpu_cores and
                    cluster.available_gpu_count + total_freed_gpu >= deployment.required_gpu_count
                ):
                    self.preempt_deployments(preemptable)
                    self.allocate_resources(deployment, cluster)
                    return True
        
        # Add to queue if cannot schedule immediately
        deployment.status = DeploymentStatus.QUEUED
        self.add_to_queue(deployment)
        self.db.commit()
        return False
    
    def process_queue(self, cluster_id: int):
        """Process the deployment queue for a cluster"""
        queue_key = f"deployment_queue_{cluster_id}"
        
        # Get highest priority deployments
        queue_items = self.redis_client.zrevrange(queue_key, 0, -1, withscores=True)
        
        for item_data, score in queue_items:
            queue_data = json.loads(item_data)
            deployment_id = queue_data['deployment_id']
            
            deployment = self.db.query(Deployment).filter(
                Deployment.id == deployment_id
            ).first()
            
            if not deployment or deployment.status != DeploymentStatus.QUEUED:
                # Remove from queue if deployment no longer exists or status changed
                self.redis_client.zrem(queue_key, item_data)
                continue
            
            # Try to schedule
            if self.schedule_deployment(deployment):
                # Remove from queue if successfully scheduled
                self.redis_client.zrem(queue_key, item_data) 