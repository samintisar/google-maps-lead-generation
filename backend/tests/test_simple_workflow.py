"""
Test simple workflow creation with basic nodes.
"""
import asyncio
import json
import logging
from datetime import datetime

from n8n_client import N8nClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_workflow():
    """Create a simple workflow to test basic functionality."""
    logger.info("Creating simple test workflow...")
    
    async with N8nClient(base_url="http://localhost:5678/rest") as client:
        try:
            # Create a very simple workflow with just a manual trigger and start node
            simple_nodes = [
                {
                    "parameters": {},
                    "name": "Manual Trigger",
                    "type": "n8n-nodes-base.manualTrigger",
                    "typeVersion": 1,
                    "position": [740, 240],
                    "id": "start-node"
                }
            ]
            
            simple_connections = {}
            
            workflow_name = f"Simple Test {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            created_workflow = await client.create_workflow(
                name=workflow_name,
                nodes=simple_nodes,
                connections=simple_connections,
                tags=["test", "simple"]
            )
            
            logger.info(f"✅ Created simple workflow: {created_workflow.id} - {created_workflow.name}")
            logger.info(f"   Nodes: {len(created_workflow.nodes)}")
            logger.info(f"   Active: {created_workflow.active}")
            
            # Clean up
            await client.delete_workflow(created_workflow.id)
            logger.info(f"✅ Deleted test workflow: {created_workflow.id}")
            
            logger.info("🎉 Simple workflow test completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    asyncio.run(test_simple_workflow()) 