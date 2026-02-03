"""
Pydantic models for configuration and requests
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnalyticsConfig(BaseModel):
    """Google Analytics configuration"""
    propertyId: str = Field(..., description="GA4 Property ID")
    measurementId: str = Field(..., description="GA4 Measurement ID")
    enabled: bool = Field(default=True, description="Whether Analytics is enabled")
    customEvents: List[str] = Field(default_factory=list, description="List of custom event names")


class TagsConfig(BaseModel):
    """Google Tag Manager configuration"""
    containerId: str = Field(..., description="GTM Container ID")
    enabled: bool = Field(default=True, description="Whether GTM is enabled")


class AdSenseConfig(BaseModel):
    """Google AdSense configuration"""
    clientId: str = Field(..., description="AdSense Client ID")
    adUnits: List[str] = Field(default_factory=list, description="List of ad unit IDs")
    enabled: bool = Field(default=True, description="Whether AdSense is enabled")


class AdsConfig(BaseModel):
    """Google Ads configuration"""
    customerId: str = Field(..., description="Google Ads Customer ID")
    campaigns: List[str] = Field(default_factory=list, description="List of campaign IDs")
    enabled: bool = Field(default=False, description="Whether Google Ads is enabled")


class ProductGoogleConfig(BaseModel):
    """Complete Google services configuration for a product"""
    id: str = Field(..., description="Configuration ID")
    productCode: str = Field(..., description="Product code (e.g., TERP, GRID)")
    productName: str = Field(..., description="Product display name")
    analytics: Optional[AnalyticsConfig] = None
    tags: Optional[TagsConfig] = None
    adsense: Optional[AdSenseConfig] = None
    ads: Optional[AdsConfig] = None
    apis: Dict[str, Any] = Field(default_factory=dict, description="Enabled APIs")
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class AnalyticsEvent(BaseModel):
    """Google Analytics event"""
    propertyId: str = Field(..., description="GA4 Property ID")
    eventName: str = Field(..., description="Event name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Event parameters")
    userId: Optional[str] = Field(None, description="User ID (optional)")


class APIEnableRequest(BaseModel):
    """Request to enable Google APIs for a product"""
    productCode: str = Field(..., description="Product code")
    services: List[str] = Field(..., description="Services to enable (analytics, tags, adsense, ads)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Service-specific configuration")
