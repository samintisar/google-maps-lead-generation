"""
Live integration test for n8n connectivity.
Tests actual connectivity with running n8n instance.
"""
import asyncio
import json
import logging
from datetime import datetime

from n8n_client import N8nClient, LEAD_NURTURING_WORKFLOW_TEMPLATE
from services.n8n_service import N8nService
from config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_n8n_live_connectivity():
    """Test live connectivity with n8n instance."""
    logger.info("Starting live n8n integration test...")
    
    settings = Settings()
    # Use localhost for external testing (not Docker hostname)
    localhost_base_url = "http://localhost:5678/rest"
    logger.info(f"n8n API URL: {localhost_base_url}")
    logger.info(f"Using credentials: {settings.n8n_email}")
    
    try:
        # Test 1: Basic connectivity and health check
        logger.info("Test 1: Testing basic connectivity...")
        async with N8nClient(
            base_url=localhost_base_url,
            email=settings.n8n_email,
            password=settings.n8n_password
        ) as client:
            health_status = await client.health_check()
            logger.info(f"Health check result: {health_status}")
            assert health_status, "n8n health check failed"
            
            # Test 2: Authentication
            logger.info("Test 2: Testing authentication...")
            auth_status = await client.authenticate()
            logger.info(f"Authentication result: {auth_status}")
            assert auth_status, "n8n authentication failed"
            
            # Test 3: Get workflows (should now work with authentication)
            logger.info("Test 3: Testing authenticated API access...")
            workflows = await client.get_workflows()
            logger.info(f"Retrieved {len(workflows)} workflows")
            
            # Test 4: Test workflow template validation
            logger.info("Test 4: Testing workflow template...")
            template = LEAD_NURTURING_WORKFLOW_TEMPLATE
            logger.info(f"Template has {len(template['nodes'])} nodes")
            assert len(template['nodes']) > 0, "Template should have nodes"
        
        logger.info("✅ All n8n integration tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

async def test_service_layer_connectivity():
    """Test the service layer with live n8n instance."""
    logger.info("Starting service layer connectivity test...")
    
    try:
        from unittest.mock import AsyncMock
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Test N8nService with localhost override
        class TestN8nService(N8nService):
            async def get_n8n_client(self):
                """Override to use localhost for testing."""
                if self._n8n_client is None:
                    self._n8n_client = N8nClient(base_url="http://localhost:5678/rest")
                return self._n8n_client
        
        n8n_service = TestN8nService(mock_db)
        
        # Test health check through service layer
        health_status = await n8n_service.health_check()
        logger.info(f"Service layer health check: {health_status}")
        assert health_status, "Service layer health check failed"
        
        await n8n_service.close()
        
        logger.info("✅ Service layer connectivity test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service layer test failed: {e}")
        raise

async def test_workflow_template_creation():
    """Test creating workflow from template."""
    logger.info("Starting workflow template creation test...")
    
    try:
        async with N8nClient(base_url="http://localhost:5678/rest") as client:
            # Create workflow from lead nurturing template
            template_name = f"Lead Nurturing Template Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get template configuration
            template_config = LEAD_NURTURING_WORKFLOW_TEMPLATE
            
            created_workflow = await client.create_workflow(
                name=template_name,
                nodes=template_config["nodes"],
                connections=template_config.get("connections", {}),
                settings=template_config.get("settings", {}),
                tags=["lead_nurturing", "template", "test"]
            )
            
            logger.info(f"Created workflow from template: {created_workflow.id} - {created_workflow.name}")
            
            # Verify the workflow has the expected nodes
            assert len(created_workflow.nodes) > 0, "Template workflow should have nodes"
            
            # Clean up
            delete_result = await client.delete_workflow(created_workflow.id)
            assert delete_result, "Failed to delete template workflow"
            logger.info("Template workflow deleted successfully")
            
        logger.info("✅ Workflow template creation test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Workflow template test failed: {e}")
        raise

async def main():
    """Main test runner."""
    await test_n8n_live_connectivity()

if __name__ == "__main__":
    asyncio.run(main()) 