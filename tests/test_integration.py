"""
Integration tests for Acidni Google Services
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "acidni-google"
    assert data["version"] == "1.0.0"


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Acidni Google Services Manager"
    assert "endpoints" in data


def test_missing_subscription_key():
    """Test that endpoints require subscription key"""
    response = client.get("/analytics/properties")
    assert response.status_code == 422  # Validation error for missing header


def test_analytics_properties_with_key():
    """Test analytics properties endpoint with subscription key"""
    response = client.get(
        "/analytics/properties",
        headers={"Ocp-Apim-Subscription-Key": "test-key"}
    )
    # Should return 200 with sample data (actual implementation will vary)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data


def test_analytics_event():
    """Test sending analytics event"""
    response = client.post(
        "/analytics/events",
        headers={"Ocp-Apim-Subscription-Key": "test-key"},
        json={
            "propertyId": "G-TEST123",
            "eventName": "test_event",
            "params": {"test": "value"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True


def test_tag_containers():
    """Test listing tag containers"""
    response = client.get(
        "/tags/containers",
        headers={"Ocp-Apim-Subscription-Key": "test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data


def test_adsense_revenue():
    """Test AdSense revenue report"""
    response = client.get(
        "/adsense/reports/revenue?startDate=2026-01-01&endDate=2026-01-31",
        headers={"Ocp-Apim-Subscription-Key": "test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data


def test_enable_apis():
    """Test enabling APIs for a product"""
    response = client.post(
        "/apis/enable",
        headers={"Ocp-Apim-Subscription-Key": "test-key"},
        json={
            "productCode": "TEST",
            "services": ["analytics"],
            "config": {
                "productName": "Test Product",
                "analytics": {
                    "propertyId": "G-TEST123",
                    "measurementId": "G-TEST123",
                    "enabled": True
                }
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True


def test_api_status():
    """Test getting API status"""
    response = client.get(
        "/apis/status/TEST",
        headers={"Ocp-Apim-Subscription-Key": "test-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
