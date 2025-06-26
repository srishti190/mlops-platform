import pytest
from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)

def get_auth_token_and_cluster():
    # Register and login a user
    client.post(
        "/auth/register",
        json={
            "username": "deploymenttest",
            "email": "deployment@example.com",
            "password": "testpassword",
            "role": "developer"
        }
    )
    
    # Create organization and cluster
    login_response = client.post(
        "/auth/login",
        data={"username": "deploymenttest", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    client.post(
        "/organizations/",
        json={"name": "Test Org"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    cluster_response = client.post(
        "/clusters/",
        json={
            "name": "Test Cluster",
            "total_ram_gb": 32.0,
            "total_cpu_cores": 8.0,
            "total_gpu_count": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    cluster_id = cluster_response.json()["id"]
    return token, cluster_id

def test_create_deployment():
    token, cluster_id = get_auth_token_and_cluster()
    
    response = client.post(
        "/deployments/",
        json={
            "name": "Test Deployment",
            "docker_image": "test/model:latest",
            "cluster_id": cluster_id,
            "required_ram_gb": 4.0,
            "required_cpu_cores": 2.0,
            "required_gpu_count": 1,
            "priority": "MEDIUM"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Deployment"
    assert data["docker_image"] == "test/model:latest"

def test_list_deployments():
    token, cluster_id = get_auth_token_and_cluster()
    
    # Create a deployment first
    client.post(
        "/deployments/",
        json={
            "name": "List Test Deployment",
            "docker_image": "test/model:latest",
            "cluster_id": cluster_id,
            "required_ram_gb": 2.0,
            "required_cpu_cores": 1.0,
            "required_gpu_count": 0,
            "priority": "LOW"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # List deployments
    response = client.get(
        "/deployments/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0 