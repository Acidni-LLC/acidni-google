"""
Response models
"""
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")
