"""
Comprehensive n8n Integration Test Suite for Task 5.5
Tests functionality, performance, and reliability of the n8n integration across various scenarios.
"""
import asyncio
import time
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Core testing imports
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# n8n integration imports
from n8n_client import N8nClient, N8nWorkflow, WorkflowExecutionResult
from services.n8n_service import N8nService
from config import Settings

# Error handling and logging
from utils.logging_config import LoggingConfig, get_n8n_logger
from utils.error_handling import (
    N8nConnectionError, N8nAuthenticationError, N8nApiError, N8nTimeoutError,
    N8nValidationError, N8nWorkflowExecutionError
)

# Setup logging
LoggingConfig.setup_logging(log_level="INFO", enable_console=True, enable_file=True)
logger = get_n8n_logger("integration_test")

class N8nIntegrationTestSuite:
    """Comprehensive integration test suite for n8n."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.settings = Settings()
        self.test_results = {}
        self.performance_metrics = {}
        self.test_data = {}
        self.created_workflows = []  # Track created workflows for cleanup
        
    def setup_test_environment(self):
        """Set up the test environment."""
        logger.info("Setting up n8n integration test environment...")
        
        # Verify environment requirements
        requirements = {
            "n8n_running": self._check_n8n_running(),
            "database_accessible": self._check_database(),
            "api_credentials": self._check_credentials()
        }
        
        for requirement, status in requirements.items():
            if not status:
                raise Exception(f"Test environment requirement failed: {requirement}")
                
        logger.info("✅ Test environment setup complete")
        return requirements
    
    def _check_n8n_running(self) -> bool:
        """Check if n8n is running and accessible."""
        try:
            import httpx
            response = httpx.get("http://localhost:5678/healthz", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"n8n not accessible: {e}")
            return False
    
    def _check_database(self) -> bool:
        """Check if database is accessible."""
        try:
            from database import get_db
            db = next(get_db())
            # Simple query to test connection
            return db is not None
        except Exception as e:
            logger.error(f"Database not accessible: {e}")
            return False
    
    def _check_credentials(self) -> bool:
        """Check if n8n credentials are available."""
        return bool(self.settings.n8n_email and self.settings.n8n_password)
    
    async def test_basic_connectivity(self) -> Dict[str, Any]:
        """Test 1: Basic connectivity and authentication."""
        logger.info("🧪 Test 1: Basic Connectivity and Authentication")
        
        test_start = time.time()
        results = {
            "test_name": "Basic Connectivity",
            "passed": False,
            "details": {},
            "duration": 0,
            "errors": []
        }
        
        try:
            async with N8nClient() as client:
                # Test health check
                health_start = time.time()
                health_status = await client.health_check()
                health_duration = time.time() - health_start
                
                results["details"]["health_check"] = {
                    "status": health_status,
                    "duration": health_duration
                }
                
                # Test authentication
                auth_start = time.time()
                auth_status = await client.authenticate()
                auth_duration = time.time() - auth_start
                
                results["details"]["authentication"] = {
                    "status": auth_status,
                    "duration": auth_duration
                }
                
                # Test API access
                api_start = time.time()
                workflows = await client.get_workflows()
                api_duration = time.time() - api_start
                
                results["details"]["api_access"] = {
                    "workflow_count": len(workflows),
                    "duration": api_duration
                }
                
                results["passed"] = health_status and auth_status
                
                if results["passed"]:
                    logger.info("✅ Basic connectivity test passed")
                else:
                    logger.error("❌ Basic connectivity test failed")
                    
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"❌ Basic connectivity test failed: {e}")
        
        results["duration"] = time.time() - test_start
        return results
    
    async def test_workflow_operations(self) -> Dict[str, Any]:
        """Test 2: Workflow CRUD operations."""
        logger.info("🧪 Test 2: Workflow CRUD Operations")
        
        test_start = time.time()
        results = {
            "test_name": "Workflow Operations",
            "passed": False,
            "details": {},
            "duration": 0,
            "errors": []
        }
        
        try:
            async with N8nClient() as client:
                # Test workflow creation
                test_workflow_name = f"Integration Test Workflow {uuid.uuid4().hex[:8]}"
                
                create_start = time.time()
                created_workflow = await client.create_workflow(
                    name=test_workflow_name,
                    nodes=[
                        {
                            "id": "start",
                            "type": "manualTrigger",
                            "position": [240, 300],
                            "parameters": {}
                        },
                        {
                            "id": "set",
                            "type": "set",
                            "position": [460, 300],
                            "parameters": {
                                "values": {
                                    "string": [
                                        {
                                            "name": "message",
                                            "value": "Integration test successful"
                                        }
                                    ]
                                }
                            }
                        }
                    ],
                    connections={
                        "start": {
                            "main": [[{"node": "set", "type": "main", "index": 0}]]
                        }
                    },
                    tags=["integration_test"]
                )
                create_duration = time.time() - create_start
                
                self.created_workflows.append(created_workflow.id)
                
                results["details"]["create_workflow"] = {
                    "workflow_id": created_workflow.id,
                    "duration": create_duration,
                    "success": True
                }
                
                # Test workflow retrieval
                get_start = time.time()
                retrieved_workflow = await client.get_workflow(created_workflow.id)
                get_duration = time.time() - get_start
                
                results["details"]["get_workflow"] = {
                    "found": retrieved_workflow is not None,
                    "name_matches": retrieved_workflow.name == test_workflow_name if retrieved_workflow else False,
                    "duration": get_duration
                }
                
                # Test workflow execution
                exec_start = time.time()
                execution_result = await client.execute_workflow(
                    workflow_id=created_workflow.id,
                    data={"test_input": "integration_test"}
                )
                exec_duration = time.time() - exec_start
                
                results["details"]["execute_workflow"] = {
                    "execution_id": execution_result.execution_id,
                    "status": execution_result.status,
                    "duration": exec_duration,
                    "success": execution_result.status in ["success", "completed"]
                }
                
                # Test workflow deletion
                delete_start = time.time()
                delete_result = await client.delete_workflow(created_workflow.id)
                delete_duration = time.time() - delete_start
                
                if delete_result:
                    self.created_workflows.remove(created_workflow.id)
                
                results["details"]["delete_workflow"] = {
                    "success": delete_result,
                    "duration": delete_duration
                }
                
                # Overall test success
                results["passed"] = all([
                    results["details"]["create_workflow"]["success"],
                    results["details"]["get_workflow"]["found"],
                    results["details"]["execute_workflow"]["success"],
                    results["details"]["delete_workflow"]["success"]
                ])
                
                if results["passed"]:
                    logger.info("✅ Workflow operations test passed")
                else:
                    logger.error("❌ Workflow operations test failed")
                    
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"❌ Workflow operations test failed: {e}")
        
        results["duration"] = time.time() - test_start
        return results
    
    async def test_service_layer_integration(self) -> Dict[str, Any]:
        """Test 3: Service layer integration."""
        logger.info("🧪 Test 3: Service Layer Integration")
        
        test_start = time.time()
        results = {
            "test_name": "Service Layer Integration",
            "passed": False,
            "details": {},
            "duration": 0,
            "errors": []
        }
        
        try:
            # Mock database session
            mock_db = MagicMock()
            service = N8nService(mock_db)
            
            # Test service health check
            health_start = time.time()
            health_status = await service.health_check()
            health_duration = time.time() - health_start
            
            results["details"]["service_health_check"] = {
                "status": health_status,
                "duration": health_duration
            }
            
            # Test workflow statistics
            stats_start = time.time()
            try:
                stats = await service.get_workflow_statistics(organization_id=1)
                stats_duration = time.time() - stats_start
                
                results["details"]["workflow_statistics"] = {
                    "success": True,
                    "duration": stats_duration,
                    "has_data": bool(stats)
                }
            except Exception as e:
                results["details"]["workflow_statistics"] = {
                    "success": False,
                    "error": str(e)
                }
            
            # Test workflow validation
            try:
                # Create a test workflow first
                async with N8nClient() as client:
                    test_workflow = await client.create_workflow(
                        name=f"Service Test Workflow {uuid.uuid4().hex[:8]}",
                        nodes=[{"id": "start", "type": "manualTrigger", "position": [240, 300]}],
                        connections={},
                        tags=["service_test"]
                    )
                    self.created_workflows.append(test_workflow.id)
                    
                    # Mock workflow in database
                    from models import Workflow
                    mock_workflow = Workflow(
                        id=1,
                        n8n_workflow_id=test_workflow.id,
                        name=test_workflow.name,
                        is_active=True
                    )
                    mock_db.query.return_value.filter.return_value.first.return_value = mock_workflow
                    
                    validation_start = time.time()
                    validation_result = await service.validate_workflow_configuration(1)
                    validation_duration = time.time() - validation_start
                    
                    results["details"]["workflow_validation"] = {
                        "success": validation_result.get("workflow_exists_in_n8n", False),
                        "duration": validation_duration,
                        "details": validation_result
                    }
                    
                    # Cleanup
                    await client.delete_workflow(test_workflow.id)
                    self.created_workflows.remove(test_workflow.id)
                    
            except Exception as e:
                results["details"]["workflow_validation"] = {
                    "success": False,
                    "error": str(e)
                }
            
            await service.close()
            
            # Overall test success
            results["passed"] = (
                results["details"]["service_health_check"]["status"] and
                results["details"].get("workflow_statistics", {}).get("success", False)
            )
            
            if results["passed"]:
                logger.info("✅ Service layer integration test passed")
            else:
                logger.error("❌ Service layer integration test failed")
                
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"❌ Service layer integration test failed: {e}")
        
        results["duration"] = time.time() - test_start
        return results
    
    async def test_error_handling_scenarios(self) -> Dict[str, Any]:
        """Test 4: Error handling scenarios."""
        logger.info("🧪 Test 4: Error Handling Scenarios")
        
        test_start = time.time()
        results = {
            "test_name": "Error Handling Scenarios",
            "passed": False,
            "details": {},
            "duration": 0,
            "errors": []
        }
        
        try:
            # Test connection error handling
            try:
                invalid_client = N8nClient(base_url="http://invalid-host:9999/rest")
                await invalid_client.health_check()
                results["details"]["connection_error"] = {"handled": False}
            except N8nConnectionError:
                results["details"]["connection_error"] = {"handled": True}
            except Exception as e:
                results["details"]["connection_error"] = {
                    "handled": False,
                    "unexpected_error": str(e)
                }
            
            # Test authentication error handling
            try:
                auth_client = N8nClient(
                    email="invalid@example.com",
                    password="wrongpassword"
                )
                await auth_client.authenticate()
                results["details"]["auth_error"] = {"handled": False}
            except N8nAuthenticationError:
                results["details"]["auth_error"] = {"handled": True}
            except Exception as e:
                results["details"]["auth_error"] = {
                    "handled": False,
                    "unexpected_error": str(e)
                }
            
            # Test API error handling (non-existent workflow)
            try:
                async with N8nClient() as client:
                    await client.get_workflow("nonexistent-workflow-id")
                results["details"]["api_error"] = {"handled": True}  # Should return None, not error
            except Exception as e:
                results["details"]["api_error"] = {
                    "handled": False,
                    "error": str(e)
                }
            
            # Test service layer error handling
            mock_db = MagicMock()
            service = N8nService(mock_db)
            service._n8n_client = AsyncMock()
            service._n8n_client.health_check.side_effect = Exception("Simulated error")
            
            service_health = await service.health_check()
            results["details"]["service_error"] = {
                "handled": service_health == False  # Should return False on error
            }
            
            await service.close()
            
            # Overall test success
            error_tests = [
                results["details"]["connection_error"]["handled"],
                results["details"]["auth_error"]["handled"],
                results["details"]["service_error"]["handled"]
            ]
            results["passed"] = all(error_tests)
            
            if results["passed"]:
                logger.info("✅ Error handling scenarios test passed")
            else:
                logger.error("❌ Error handling scenarios test failed")
                
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"❌ Error handling scenarios test failed: {e}")
        
        results["duration"] = time.time() - test_start
        return results
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test 5: Performance metrics and load testing."""
        logger.info("🧪 Test 5: Performance Metrics and Load Testing")
        
        test_start = time.time()
        results = {
            "test_name": "Performance Metrics",
            "passed": False,
            "details": {},
            "duration": 0,
            "errors": []
        }
        
        try:
            # Performance thresholds
            thresholds = {
                "health_check": 1.0,  # seconds
                "authentication": 3.0,  # seconds
                "workflow_list": 5.0,  # seconds
                "workflow_creation": 10.0,  # seconds
                "workflow_execution": 30.0  # seconds
            }
            
            async with N8nClient() as client:
                # Test health check performance
                health_times = []
                for i in range(5):
                    start = time.time()
                    await client.health_check()
                    health_times.append(time.time() - start)
                
                avg_health_time = sum(health_times) / len(health_times)
                results["details"]["health_check_performance"] = {
                    "average_time": avg_health_time,
                    "max_time": max(health_times),
                    "min_time": min(health_times),
                    "within_threshold": avg_health_time <= thresholds["health_check"]
                }
                
                # Test workflow listing performance
                list_times = []
                for i in range(3):
                    start = time.time()
                    await client.get_workflows()
                    list_times.append(time.time() - start)
                
                avg_list_time = sum(list_times) / len(list_times)
                results["details"]["workflow_list_performance"] = {
                    "average_time": avg_list_time,
                    "max_time": max(list_times),
                    "min_time": min(list_times),
                    "within_threshold": avg_list_time <= thresholds["workflow_list"]
                }
                
                # Test concurrent operations
                concurrent_start = time.time()
                tasks = [client.health_check() for _ in range(5)]
                await asyncio.gather(*tasks)
                concurrent_duration = time.time() - concurrent_start
                
                results["details"]["concurrent_operations"] = {
                    "duration": concurrent_duration,
                    "operations": len(tasks),
                    "avg_per_operation": concurrent_duration / len(tasks)
                }
                
                # Memory usage test (simple workflow creation/deletion)
                memory_test_start = time.time()
                test_workflows = []
                
                try:
                    # Create multiple workflows
                    for i in range(3):
                        workflow = await client.create_workflow(
                            name=f"Performance Test {i} {uuid.uuid4().hex[:6]}",
                            nodes=[{"id": "start", "type": "manualTrigger", "position": [240, 300]}],
                            connections={},
                            tags=["performance_test"]
                        )
                        test_workflows.append(workflow.id)
                        self.created_workflows.append(workflow.id)
                    
                    # Delete all test workflows
                    for workflow_id in test_workflows:
                        await client.delete_workflow(workflow_id)
                        self.created_workflows.remove(workflow_id)
                    
                    memory_test_duration = time.time() - memory_test_start
                    results["details"]["memory_test"] = {
                        "duration": memory_test_duration,
                        "workflows_created": len(test_workflows),
                        "success": True
                    }
                    
                except Exception as e:
                    results["details"]["memory_test"] = {
                        "success": False,
                        "error": str(e)
                    }
                
                # Overall performance test success
                performance_checks = [
                    results["details"]["health_check_performance"]["within_threshold"],
                    results["details"]["workflow_list_performance"]["within_threshold"],
                    results["details"]["memory_test"]["success"]
                ]
                results["passed"] = all(performance_checks)
                
                if results["passed"]:
                    logger.info("✅ Performance metrics test passed")
                else:
                    logger.error("❌ Performance metrics test failed")
                    
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"❌ Performance metrics test failed: {e}")
        
        results["duration"] = time.time() - test_start
        return results
    
    async def test_workflow_templates(self) -> Dict[str, Any]:
        """Test 6: Workflow template functionality."""
        logger.info("🧪 Test 6: Workflow Template Functionality")
        
        test_start = time.time()
        results = {
            "test_name": "Workflow Templates",
            "passed": False,
            "details": {},
            "duration": 0,
            "errors": []
        }
        
        try:
            # Test template availability
            template_file = Path("backend/n8n_workflow_templates.json")
            if template_file.exists():
                with open(template_file, 'r') as f:
                    templates = json.load(f)
                
                results["details"]["template_availability"] = {
                    "templates_found": len(templates),
                    "template_names": list(templates.keys()),
                    "success": len(templates) > 0
                }
                
                # Test template creation
                if templates:
                    template_name = list(templates.keys())[0]
                    template_data = templates[template_name]
                    
                    async with N8nClient() as client:
                        try:
                            created_workflow = await client.create_workflow(
                                name=f"Template Test {uuid.uuid4().hex[:6]}",
                                nodes=template_data.get("nodes", []),
                                connections=template_data.get("connections", {}),
                                settings=template_data.get("settings", {}),
                                tags=["template_test"]
                            )
                            
                            self.created_workflows.append(created_workflow.id)
                            
                            results["details"]["template_creation"] = {
                                "template_used": template_name,
                                "workflow_id": created_workflow.id,
                                "node_count": len(created_workflow.nodes),
                                "success": True
                            }
                            
                            # Cleanup
                            await client.delete_workflow(created_workflow.id)
                            self.created_workflows.remove(created_workflow.id)
                            
                        except Exception as e:
                            results["details"]["template_creation"] = {
                                "success": False,
                                "error": str(e)
                            }
                else:
                    results["details"]["template_creation"] = {
                        "success": False,
                        "error": "No templates available"
                    }
            else:
                results["details"]["template_availability"] = {
                    "success": False,
                    "error": "Template file not found"
                }
            
            # Test template index endpoint
            try:
                import httpx
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.get("http://localhost:8000/api/workflows/templates/")
                    if response.status_code == 200:
                        api_templates = response.json()
                        results["details"]["template_api"] = {
                            "success": True,
                            "template_count": len(api_templates),
                            "status_code": response.status_code
                        }
                    else:
                        results["details"]["template_api"] = {
                            "success": False,
                            "status_code": response.status_code
                        }
            except Exception as e:
                results["details"]["template_api"] = {
                    "success": False,
                    "error": str(e)
                }
            
            # Overall template test success
            template_checks = [
                results["details"].get("template_availability", {}).get("success", False),
                results["details"].get("template_creation", {}).get("success", False)
            ]
            results["passed"] = any(template_checks)  # Pass if either check succeeds
            
            if results["passed"]:
                logger.info("✅ Workflow templates test passed")
            else:
                logger.error("❌ Workflow templates test failed")
                
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"❌ Workflow templates test failed: {e}")
        
        results["duration"] = time.time() - test_start
        return results
    
    async def cleanup_test_resources(self):
        """Clean up any test resources created during testing."""
        logger.info("🧹 Cleaning up test resources...")
        
        if self.created_workflows:
            try:
                async with N8nClient() as client:
                    for workflow_id in self.created_workflows:
                        try:
                            await client.delete_workflow(workflow_id)
                            logger.info(f"Deleted test workflow: {workflow_id}")
                        except Exception as e:
                            logger.warning(f"Failed to delete workflow {workflow_id}: {e}")
                self.created_workflows.clear()
            except Exception as e:
                logger.error(f"Failed to cleanup workflows: {e}")
        
        logger.info("✅ Cleanup complete")
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all integration tests and return comprehensive results."""
        logger.info("🚀 Starting comprehensive n8n integration testing...")
        
        start_time = time.time()
        
        # Setup test environment
        try:
            env_setup = self.setup_test_environment()
        except Exception as e:
            logger.error(f"❌ Test environment setup failed: {e}")
            return {
                "overall_success": False,
                "error": str(e),
                "tests_run": 0,
                "tests_passed": 0
            }
        
        # Define test cases
        test_cases = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Workflow Operations", self.test_workflow_operations),
            ("Service Layer Integration", self.test_service_layer_integration),
            ("Error Handling Scenarios", self.test_error_handling_scenarios),
            ("Performance Metrics", self.test_performance_metrics),
            ("Workflow Templates", self.test_workflow_templates),
        ]
        
        test_results = []
        passed_tests = 0
        
        try:
            # Run each test case
            for test_name, test_function in test_cases:
                logger.info(f"\n{'='*60}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*60}")
                
                try:
                    result = await test_function()
                    test_results.append(result)
                    
                    if result["passed"]:
                        passed_tests += 1
                        logger.info(f"✅ {test_name}: PASSED")
                    else:
                        logger.error(f"❌ {test_name}: FAILED")
                        if result.get("errors"):
                            for error in result["errors"]:
                                logger.error(f"   Error: {error}")
                                
                except Exception as e:
                    logger.error(f"❌ {test_name}: CRASHED - {e}")
                    test_results.append({
                        "test_name": test_name,
                        "passed": False,
                        "errors": [str(e)],
                        "duration": 0
                    })
            
            # Cleanup
            await self.cleanup_test_resources()
            
        except Exception as e:
            logger.error(f"Test suite crashed: {e}")
            await self.cleanup_test_resources()
            raise
        
        # Generate summary
        total_duration = time.time() - start_time
        overall_success = passed_tests == len(test_cases)
        
        summary = {
            "overall_success": overall_success,
            "tests_run": len(test_cases),
            "tests_passed": passed_tests,
            "tests_failed": len(test_cases) - passed_tests,
            "total_duration": total_duration,
            "environment_setup": env_setup,
            "test_results": test_results
        }
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("🧪 N8N INTEGRATION TEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Tests Run: {summary['tests_run']}")
        logger.info(f"Tests Passed: {summary['tests_passed']}")
        logger.info(f"Tests Failed: {summary['tests_failed']}")
        logger.info(f"Overall Success: {'✅ YES' if overall_success else '❌ NO'}")
        logger.info(f"Total Duration: {total_duration:.2f} seconds")
        logger.info("="*80)
        
        if overall_success:
            logger.info("🎉 ALL INTEGRATION TESTS PASSED!")
            logger.info("✅ n8n integration is fully functional and ready for production.")
        else:
            logger.error("⚠️  SOME TESTS FAILED!")
            logger.error("❌ Review failed tests before proceeding to production.")
        
        return summary

async def main():
    """Main function to run the comprehensive integration test suite."""
    test_suite = N8nIntegrationTestSuite()
    
    try:
        results = await test_suite.run_comprehensive_tests()
        
        # Save results to file
        results_file = Path("backend/logs/integration_test_results.json")
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📋 Test results saved to: {results_file}")
        
        # Exit with appropriate code
        return 0 if results["overall_success"] else 1
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    print("🧪 Running comprehensive n8n integration test suite...")
    exit_code = asyncio.run(main())
    exit(exit_code) 