"""
Service Management
Handles API enablement and product configuration
"""
import logging
from typing import List, Dict, Any
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manager for API enablement and product configuration"""
    
    def __init__(self):
        """Initialize Service Manager with Cosmos DB access"""
        self.cosmos_client = None
        self.container = None
        self._initialize_cosmos()
    
    def _initialize_cosmos(self):
        """Initialize Cosmos DB client"""
        try:
            cosmos_endpoint = os.environ.get(
                "COSMOS_ENDPOINT",
                "https://cosmos-terprint-dev.documents.azure.com:443/"
            )
            database_name = os.environ.get("COSMOS_DATABASE", "TerprintAI")
            
            credential = DefaultAzureCredential()
            self.cosmos_client = CosmosClient(cosmos_endpoint, credential)
            db = self.cosmos_client.get_database_client(database_name)
            self.container = db.get_container_client("google_configs")
            
            logger.info("✅ Cosmos DB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            # Don't raise - allow app to start in degraded mode
    
    async def enable_apis(
        self,
        product_code: str,
        services: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enable Google APIs for a product"""
        try:
            logger.info(f"Enabling APIs for product {product_code}: {services}")
            
            if not self.container:
                raise Exception("Cosmos DB not initialized")
            
            # Create or update product configuration
            config_id = f"{product_code.lower()}-google-config"
            
            product_config = {
                "id": config_id,
                "productCode": product_code,
                "productName": config.get("productName", product_code),
                "apis": {
                    "enabled": services
                },
                "updatedAt": datetime.utcnow().isoformat()
            }
            
            # Add service-specific configs
            if "analytics" in services:
                product_config["analytics"] = config.get("analytics", {})
            if "tags" in services:
                product_config["tags"] = config.get("tags", {})
            if "adsense" in services:
                product_config["adsense"] = config.get("adsense", {})
            if "ads" in services:
                product_config["ads"] = config.get("ads", {})
            
            # Upsert to Cosmos DB
            self.container.upsert_item(product_config)
            
            return {
                "success": True,
                "productCode": product_code,
                "enabledServices": services,
                "configId": config_id
            }
            
        except Exception as e:
            logger.error(f"Error enabling APIs: {e}")
            raise
    
    async def disable_apis(
        self,
        product_code: str,
        services: List[str]
    ) -> Dict[str, Any]:
        """Disable Google APIs for a product"""
        try:
            logger.info(f"Disabling APIs for product {product_code}: {services}")
            
            if not self.container:
                raise Exception("Cosmos DB not initialized")
            
            config_id = f"{product_code.lower()}-google-config"
            
            # Read existing config
            config = self.container.read_item(config_id, partition_key=product_code)
            
            # Update enabled services
            enabled = config.get("apis", {}).get("enabled", [])
            enabled = [s for s in enabled if s not in services]
            config["apis"]["enabled"] = enabled
            config["updatedAt"] = datetime.utcnow().isoformat()
            
            # Update in Cosmos DB
            self.container.upsert_item(config)
            
            return {
                "success": True,
                "productCode": product_code,
                "disabledServices": services,
                "remainingServices": enabled
            }
            
        except Exception as e:
            logger.error(f"Error disabling APIs: {e}")
            raise
    
    async def get_status(self, product_code: str) -> Dict[str, Any]:
        """Get API enablement status for a product"""
        try:
            logger.info(f"Getting status for product {product_code}")
            
            if not self.container:
                raise Exception("Cosmos DB not initialized")
            
            config_id = f"{product_code.lower()}-google-config"
            
            try:
                config = self.container.read_item(config_id, partition_key=product_code)
                
                return {
                    "productCode": product_code,
                    "productName": config.get("productName"),
                    "enabledServices": config.get("apis", {}).get("enabled", []),
                    "analytics": config.get("analytics", {}).get("enabled", False),
                    "tags": config.get("tags", {}).get("enabled", False),
                    "adsense": config.get("adsense", {}).get("enabled", False),
                    "ads": config.get("ads", {}).get("enabled", False),
                    "updatedAt": config.get("updatedAt")
                }
                
            except Exception:
                # Configuration doesn't exist
                return {
                    "productCode": product_code,
                    "enabledServices": [],
                    "analytics": False,
                    "tags": False,
                    "adsense": False,
                    "ads": False
                }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            raise
