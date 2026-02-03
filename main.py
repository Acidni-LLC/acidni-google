"""
Acidni Google Services Manager
Centralized Google API management for all Acidni applications
"""
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

from services.analytics import AnalyticsManager
from services.tagmanager import TagManager
from services.adsense import AdSenseManager
from services.ads import AdsManager
from services.service_mgmt import ServiceManager
from models.config import ProductGoogleConfig, AnalyticsEvent, APIEnableRequest
from models.responses import HealthResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service managers (initialized in lifespan)
analytics_mgr: AnalyticsManager = None
tag_mgr: TagManager = None
adsense_mgr: AdSenseManager = None
ads_mgr: AdsManager = None
service_mgr: ServiceManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown"""
    global analytics_mgr, tag_mgr, adsense_mgr, ads_mgr, service_mgr
    
    logger.info("Initializing Acidni Google Services...")
    
    try:
        # Initialize service managers
        analytics_mgr = AnalyticsManager()
        tag_mgr = TagManager()
        adsense_mgr = AdSenseManager()
        ads_mgr = AdsManager()
        service_mgr = ServiceManager()
        
        logger.info("✅ All services initialized successfully")
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    finally:
        logger.info("Shutting down Acidni Google Services...")


# Create FastAPI app
app = FastAPI(
    title="Acidni Google Services Manager",
    description="Centralized Google API management for all Acidni applications",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # APIM handles actual CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for APIM subscription key validation (placeholder)
async def verify_subscription_key(
    ocp_apim_subscription_key: str = Header(alias="Ocp-Apim-Subscription-Key")
):
    """Verify APIM subscription key (APIM handles this, but we validate presence)"""
    if not ocp_apim_subscription_key:
        raise HTTPException(status_code=401, detail="Missing subscription key")
    return ocp_apim_subscription_key


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="acidni-google",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Acidni Google Services Manager",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analytics": "/analytics/*",
            "tags": "/tags/*",
            "adsense": "/adsense/*",
            "ads": "/ads/*",
            "apis": "/apis/*"
        },
        "documentation": "/docs"
    }


# ============================================================================
# GOOGLE ANALYTICS 4 ENDPOINTS
# ============================================================================

@app.get("/analytics/properties")
async def list_analytics_properties(key: str = Depends(verify_subscription_key)):
    """List all Google Analytics 4 properties"""
    try:
        properties = await analytics_mgr.list_properties()
        return {"success": True, "data": properties}
    except Exception as e:
        logger.error(f"Error listing properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/properties/{property_id}")
async def get_analytics_property(
    property_id: str,
    key: str = Depends(verify_subscription_key)
):
    """Get details for a specific GA4 property"""
    try:
        property_data = await analytics_mgr.get_property(property_id)
        return {"success": True, "data": property_data}
    except Exception as e:
        logger.error(f"Error getting property {property_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analytics/events")
async def send_analytics_event(
    event: AnalyticsEvent,
    key: str = Depends(verify_subscription_key)
):
    """Send custom event to Google Analytics 4"""
    try:
        result = await analytics_mgr.send_event(
            property_id=event.propertyId,
            event_name=event.eventName,
            params=event.params
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error sending event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/reports")
async def run_analytics_report(
    property_id: str,
    start_date: str,
    end_date: str,
    dimensions: str = None,
    metrics: str = None,
    key: str = Depends(verify_subscription_key)
):
    """Run custom GA4 report"""
    try:
        # Parse comma-separated dimensions and metrics
        dim_list = dimensions.split(",") if dimensions else []
        metric_list = metrics.split(",") if metrics else ["activeUsers"]
        
        report = await analytics_mgr.run_report(
            property_id=property_id,
            dimensions=dim_list,
            metrics=metric_list,
            date_range={"startDate": start_date, "endDate": end_date}
        )
        return {"success": True, "data": report}
    except Exception as e:
        logger.error(f"Error running report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GOOGLE TAG MANAGER ENDPOINTS
# ============================================================================

@app.get("/tags/containers")
async def list_tag_containers(key: str = Depends(verify_subscription_key)):
    """List all Google Tag Manager containers"""
    try:
        containers = await tag_mgr.list_containers()
        return {"success": True, "data": containers}
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tags/containers/{container_id}")
async def get_tag_container(
    container_id: str,
    key: str = Depends(verify_subscription_key)
):
    """Get details for a specific GTM container"""
    try:
        container = await tag_mgr.get_container(container_id)
        return {"success": True, "data": container}
    except Exception as e:
        logger.error(f"Error getting container {container_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GOOGLE ADSENSE ENDPOINTS
# ============================================================================

@app.get("/adsense/reports/revenue")
async def get_adsense_revenue(
    start_date: str,
    end_date: str,
    product: str = None,
    key: str = Depends(verify_subscription_key)
):
    """Get AdSense revenue report"""
    try:
        revenue = await adsense_mgr.get_revenue_report(
            start_date=start_date,
            end_date=end_date,
            product=product
        )
        return {"success": True, "data": revenue}
    except Exception as e:
        logger.error(f"Error getting revenue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GOOGLE ADS ENDPOINTS
# ============================================================================

@app.get("/ads/campaigns")
async def list_ad_campaigns(key: str = Depends(verify_subscription_key)):
    """List all Google Ads campaigns"""
    try:
        campaigns = await ads_mgr.list_campaigns()
        return {"success": True, "data": campaigns}
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# API MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/apis/enable")
async def enable_google_apis(
    request: APIEnableRequest,
    key: str = Depends(verify_subscription_key)
):
    """Enable Google APIs for a product"""
    try:
        result = await service_mgr.enable_apis(
            product_code=request.productCode,
            services=request.services,
            config=request.config
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error enabling APIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/apis/status/{product_code}")
async def get_api_status(
    product_code: str,
    key: str = Depends(verify_subscription_key)
):
    """Get API enablement status for a product"""
    try:
        status = await service_mgr.get_status(product_code)
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return ErrorResponse(
        success=False,
        error=str(exc),
        timestamp=datetime.utcnow()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
