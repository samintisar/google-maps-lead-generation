"""
Test workflow creation and webhook functionality.
"""
import asyncio
import json
import logging
from datetime import datetime

from n8n_client import N8nClient, LEAD_NURTURING_WORKFLOW_TEMPLATE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_create_and_test_workflow():
    """Create a workflow and test its webhook."""
    logger.info("Creating and testing n8n workflow...")
    
    async with N8nClient(base_url="http://localhost:5678/rest") as client:
        try:
            # Create workflow from template
            workflow_name = f"LMA Test Workflow {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            created_workflow = await client.create_workflow(
                name=workflow_name,
                nodes=LEAD_NURTURING_WORKFLOW_TEMPLATE["nodes"],
                connections=LEAD_NURTURING_WORKFLOW_TEMPLATE.get("connections", {}),
                settings=LEAD_NURTURING_WORKFLOW_TEMPLATE.get("settings", {}),
                tags=["lma", "test", "lead-nurturing"]
            )
            
            logger.info(f"✅ Created workflow: {created_workflow.id} - {created_workflow.name}")
            
            # Activate the workflow
            await client.activate_workflow(created_workflow.id)
            logger.info(f"✅ Activated workflow: {created_workflow.id}")
            
            # Get workflow statistics
            stats = await client.get_workflow_statistics()
            logger.info(f"✅ Workflow stats: {stats}")
            
            # List all workflows
            workflows = await client.get_workflows()
            logger.info(f"✅ Total workflows in n8n: {len(workflows)}")
            for wf in workflows:
                logger.info(f"  - {wf.id}: {wf.name} (active: {wf.active})")
            
            # Clean up - delete the test workflow
            await client.delete_workflow(created_workflow.id)
            logger.info(f"✅ Deleted test workflow: {created_workflow.id}")
            
            logger.info("🎉 Workflow creation and management test completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(test_create_and_test_workflow()) 