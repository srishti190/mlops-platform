import pytest
from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)

def get_auth_token():
    # Register and login a user
    client.post(
        "/auth/register",
        json={
            "username": "clustertest",
            "email": "cluster@example.com",
            "password": "testpassword",
            "role": "admin"
        }
    )
    
    # Create organization
    login_response = client.post(
        "/auth/login",
        data={"username": "clustertest", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    client.post(
        "/organizations/",
        json={"name": "Test Org"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    return token

def test_create_cluster():
    token = get_auth_token()
    
    response = client.post(
        "/clusters/",
        json={
            "name": "Test Cluster",
            "total_ram_gb": 32.0,
            "total_cpu_cores": 8.0,
            "total_gpu_count": 2
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Cluster"
    assert data["total_ram_gb"] == 32.0

def test_list_clusters():
    token = get_auth_token()
    
    # Create a cluster first
    client.post(
        "/clusters/",
        json={
            "name": "List Test Cluster",
            "total_ram_gb": 16.0,
            "total_cpu_cores": 4.0,
            "total_gpu_count": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # List clusters
    response = client.get(
        "/clusters/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0 