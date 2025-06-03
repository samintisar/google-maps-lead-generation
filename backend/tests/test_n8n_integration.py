"""
Integration tests for n8n service layer.
Tests basic connectivity and workflow operations.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session

from services.n8n_service import N8nService
from services.workflow_service import WorkflowService
from models import Workflow, Organization, User
from n8n_client import N8nWorkflow
from datetime import datetime


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=Session)


@pytest.fixture
def n8n_service(mock_db):
    """Create N8nService instance with mocked database."""
    return N8nService(mock_db)


@pytest.fixture
def workflow_service(mock_db):
    """Create WorkflowService instance with mocked database."""
    return WorkflowService(mock_db)


class TestN8nServiceIntegration:
    """Test n8n service layer integration."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, n8n_service):
        """Test n8n health check."""
        with patch.object(n8n_service, 'get_n8n_client') as mock_client:
            mock_n8n = AsyncMock()
            mock_n8n.health_check.return_value = True
            mock_client.return_value = mock_n8n
            
            result = await n8n_service.health_check()
            assert result is True
            mock_n8n.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, n8n_service):
        """Test n8n health check failure."""
        with patch.object(n8n_service, 'get_n8n_client') as mock_client:
            mock_n8n = AsyncMock()
            mock_n8n.health_check.side_effect = Exception("Connection failed")
            mock_client.return_value = mock_n8n
            
            result = await n8n_service.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_sync_workflows_from_n8n(self, n8n_service, mock_db):
        """Test syncing workflows from n8n."""
        # Mock n8n workflows
        mock_n8n_workflows = [
            N8nWorkflow(
                id="workflow-1",
                name="Test Workflow",
                active=True,
                nodes=[],
                connections={},
                settings={},
                tags=["test"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        with patch.object(n8n_service, 'get_n8n_client') as mock_client:
            mock_n8n = AsyncMock()
            mock_n8n.get_workflows.return_value = mock_n8n_workflows
            mock_client.return_value = mock_n8n
            
            # Mock database query to return no existing workflows
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            result = await n8n_service.sync_workflows_from_n8n(1)
            
            assert result["total_n8n_workflows"] == 1
            assert result["synced"] == 1
            assert result["created"] == 1
            assert result["updated"] == 0
            assert len(result["errors"]) == 0
            
            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_workflow_configuration(self, n8n_service, mock_db):
        """Test workflow configuration validation."""
        # Mock workflow from database
        mock_workflow = Workflow(
            id=1,
            n8n_workflow_id="workflow-1",
            is_active=True
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_workflow
        
        # Mock n8n workflow
        mock_n8n_workflow = N8nWorkflow(
            id="workflow-1",
            name="Test Workflow",
            active=True,
            nodes=[{"type": "test"}],
            connections={},
            settings={},
            tags=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with patch.object(n8n_service, 'get_n8n_client') as mock_client:
            mock_n8n = AsyncMock()
            mock_n8n.get_workflow.return_value = mock_n8n_workflow
            mock_client.return_value = mock_n8n
            
            result = await n8n_service.validate_workflow_configuration(1)
            
            assert result["workflow_exists_in_n8n"] is True
            assert result["configuration_valid"] is True
            assert result["n8n_active_status"] is True
            assert result["database_active_status"] is True
            assert result["sync_status"] == "synced"
            assert len(result["errors"]) == 0


class TestWorkflowServiceIntegration:
    """Test workflow service layer integration."""
    
    @pytest.mark.asyncio
    async def test_auto_assign_workflows_to_lead(self, workflow_service, mock_db):
        """Test auto-assignment of workflows to leads."""
        from models import Lead, LeadStatus
        
        # Mock lead
        mock_lead = Lead(
            id=1,
            organization_id=1,
            status=LeadStatus.NEW
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_lead
        
        # Mock workflows
        mock_workflows = [
            Workflow(
                id=1,
                organization_id=1,
                name="Lead Nurturing",
                category="lead_nurturing",
                trigger_type="lead_status_change",
                is_active=True
            ),
            Workflow(
                id=2,
                organization_id=1,
                name="Manual Follow-up",
                category="follow_up",
                trigger_type="manual",
                is_active=True
            )
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_workflows
        
        result = await workflow_service.auto_assign_workflows_to_lead(1)
        
        assert len(result) == 1  # Only nurturing workflow should be assigned
        assert result[0]["workflow_id"] == 1
        assert result[0]["category"] == "lead_nurturing"
    
    @pytest.mark.asyncio
    async def test_validate_and_sync_all_workflows(self, workflow_service, mock_db):
        """Test validation and sync of all workflows."""
        # Mock workflows in database
        mock_workflows = [
            Workflow(id=1, name="Test Workflow 1"),
            Workflow(id=2, name="Test Workflow 2")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_workflows
        
        # Mock validation results
        mock_validation = {
            "workflow_exists_in_n8n": True,
            "sync_status": "synced",
            "errors": []
        }
        
        with patch.object(workflow_service.n8n_service, 'validate_workflow_configuration') as mock_validate:
            mock_validate.return_value = mock_validation
            
            with patch.object(workflow_service.n8n_service, 'sync_workflows_from_n8n') as mock_sync:
                mock_sync.return_value = {"synced": 2, "created": 0, "updated": 0}
                
                result = await workflow_service.validate_and_sync_all_workflows(1)
                
                assert len(result["validation_results"]) == 2
                assert result["total_workflows"] == 2
                assert "sync_result" in result


class TestIntegrationEndToEnd:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_workflow_creation_and_execution_flow(self, n8n_service, mock_db):
        """Test complete workflow creation and execution flow."""
        # Mock template and n8n workflow creation
        mock_n8n_workflow = N8nWorkflow(
            id="new-workflow-1",
            name="Test Lead Nurturing",
            active=False,
            nodes=[],
            connections={},
            settings={},
            tags=["lead_nurturing"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with patch.object(n8n_service, 'get_n8n_client') as mock_client:
            mock_n8n = AsyncMock()
            mock_n8n.create_workflow.return_value = mock_n8n_workflow
            mock_client.return_value = mock_n8n
            
            # Test workflow creation from template
            db_workflow, n8n_workflow = await n8n_service.create_workflow_from_template(
                organization_id=1,
                template_name="lead_nurturing",
                workflow_name="Test Lead Nurturing",
                created_by=1
            )
            
            # Verify workflow was created
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called()
            assert n8n_workflow.name == "Test Lead Nurturing"


def test_service_layer_imports():
    """Test that all service layer components can be imported successfully."""
    from services.n8n_service import N8nService
    from services.workflow_service import WorkflowService
    from services import N8nService as ImportedN8nService, WorkflowService as ImportedWorkflowService
    
    assert N8nService is not None
    assert WorkflowService is not None
    assert ImportedN8nService is N8nService
    assert ImportedWorkflowService is WorkflowService


if __name__ == "__main__":
    # Simple connectivity test when run directly
    async def test_connectivity():
        """Test basic n8n connectivity."""
        from database import get_db
        from services.n8n_service import N8nService
        
        db = next(get_db())
        service = N8nService(db)
        
        try:
            health = await service.health_check()
            print(f"n8n Health Check: {'✅ PASS' if health else '❌ FAIL'}")
            
            stats = await service.get_workflow_statistics(1)
            print(f"n8n Statistics: ✅ Retrieved")
            print(f"  Database stats: {stats.get('database_stats', {})}")
            
        except Exception as e:
            print(f"❌ FAIL: {e}")
        finally:
            await service.close()
    
    print("Running basic n8n connectivity test...")
    asyncio.run(test_connectivity()) 