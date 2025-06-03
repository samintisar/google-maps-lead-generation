"""
Comprehensive test script for n8n error handling and logging implementation.
Tests all aspects of task 5.4: error handling, logging, circuit breakers, and recovery mechanisms.
"""
import asyncio
import json
import traceback
from datetime import datetime
from pathlib import Path

# Initialize logging first
from utils.logging_config import LoggingConfig, get_n8n_logger, check_logging_health
from utils.error_handling import (
    N8nConnectionError, N8nAuthenticationError, N8nTimeoutError, 
    N8nValidationError, N8nWorkflowExecutionError, N8nConfigurationError,
    circuit_breakers, error_recovery_manager, error_metrics,
    get_error_handling_health, ErrorSeverity
)

# Setup enhanced logging for testing
LoggingConfig.setup_logging(
    log_level="DEBUG",
    log_dir="logs/test",
    enable_console=True,
    enable_file=True,
    enable_structured=True
)

logger = get_n8n_logger("error_handling_test")

class ErrorHandlingTestSuite:
    """Comprehensive test suite for error handling and logging."""
    
    def __init__(self):
        self.test_results = {
            "test_suite": "N8n Error Handling and Logging",
            "start_time": datetime.utcnow().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
        
    def log_test_result(self, test_name: str, passed: bool, details: dict = None, error: str = None):
        """Log test result with structured data."""
        test_result = {
            "test_name": test_name,
            "passed": passed,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
            "error": error
        }
        
        self.test_results["tests"].append(test_result)
        self.test_results["summary"]["total_tests"] += 1
        
        if passed:
            self.test_results["summary"]["passed"] += 1
            logger.info(f"✅ {test_name} PASSED", extra_fields=test_result)
        else:
            self.test_results["summary"]["failed"] += 1
            if error:
                self.test_results["summary"]["errors"].append(f"{test_name}: {error}")
            logger.error(f"❌ {test_name} FAILED", extra_fields=test_result)
        
        return passed
    
    async def test_logging_configuration(self):
        """Test 1: Verify logging configuration and file creation."""
        try:
            # Check if log directory exists
            log_dir = Path("logs/test")
            log_dir_exists = log_dir.exists()
            
            # Check if log files are created
            log_files = list(log_dir.glob("*.log")) if log_dir_exists else []
            
            # Test structured logging
            test_logger = get_n8n_logger("test_structured")
            test_logger.info("Test structured log message", extra_fields={"test_key": "test_value"})
            
            # Check logging health
            health_status = check_logging_health()
            
            passed = (
                log_dir_exists and
                len(log_files) > 0 and
                health_status["status"] == "healthy"
            )
            
            return self.log_test_result(
                "test_logging_configuration",
                passed,
                {
                    "log_directory_exists": log_dir_exists,
                    "log_files_count": len(log_files),
                    "log_files": [f.name for f in log_files],
                    "health_status": health_status
                }
            )
            
        except Exception as e:
            return self.log_test_result(
                "test_logging_configuration",
                False,
                error=str(e)
            )
    
    async def test_custom_exceptions(self):
        """Test 2: Verify custom exception creation and categorization."""
        try:
            test_cases = [
                {
                    "exception_class": N8nConnectionError,
                    "message": "Test connection error",
                    "expected_category": "connection_error"
                },
                {
                    "exception_class": N8nAuthenticationError,
                    "message": "Test authentication error",
                    "expected_category": "authentication_error"
                },
                {
                    "exception_class": N8nTimeoutError,
                    "message": "Test timeout error",
                    "expected_category": "timeout_error"
                },
                {
                    "exception_class": N8nValidationError,
                    "message": "Test validation error",
                    "expected_category": "validation_error"
                },
                {
                    "exception_class": N8nWorkflowExecutionError,
                    "message": "Test execution error",
                    "expected_category": "workflow_execution_error"
                }
            ]
            
            results = []
            for test_case in test_cases:
                try:
                    exception = test_case["exception_class"](test_case["message"])
                    exception_dict = exception.to_dict()
                    
                    category_correct = exception_dict["category"] == test_case["expected_category"]
                    has_timestamp = "timestamp" in exception_dict
                    has_message = exception_dict["message"] == test_case["message"]
                    
                    test_passed = category_correct and has_timestamp and has_message
                    results.append({
                        "exception_type": test_case["exception_class"].__name__,
                        "passed": test_passed,
                        "category": exception_dict["category"],
                        "expected_category": test_case["expected_category"]
                    })
                    
                except Exception as e:
                    results.append({
                        "exception_type": test_case["exception_class"].__name__,
                        "passed": False,
                        "error": str(e)
                    })
            
            all_passed = all(result["passed"] for result in results)
            
            return self.log_test_result(
                "test_custom_exceptions",
                all_passed,
                {"test_results": results}
            )
            
        except Exception as e:
            return self.log_test_result(
                "test_custom_exceptions",
                False,
                error=str(e)
            )
    
    async def test_circuit_breaker_functionality(self):
        """Test 3: Verify circuit breaker pattern implementation."""
        try:
            # Test circuit breaker states
            test_breaker = circuit_breakers["authentication"]
            
            # Reset circuit breaker
            test_breaker.failure_count = 0
            test_breaker.state = "closed"
            
            # Test initial state
            initial_can_proceed = test_breaker.can_proceed()
            
            # Simulate failures to trigger circuit breaker
            for i in range(test_breaker.failure_threshold + 1):
                test_breaker.record_failure()
            
            # Circuit breaker should be open now
            breaker_open = test_breaker.state == "open"
            cannot_proceed = not test_breaker.can_proceed()
            
            # Test recovery
            test_breaker.record_success()
            success_recorded = test_breaker.state == "closed"
            
            passed = (
                initial_can_proceed and
                breaker_open and
                cannot_proceed and
                success_recorded
            )
            
            return self.log_test_result(
                "test_circuit_breaker_functionality",
                passed,
                {
                    "initial_can_proceed": initial_can_proceed,
                    "breaker_opened": breaker_open,
                    "cannot_proceed_when_open": cannot_proceed,
                    "success_recorded": success_recorded,
                    "final_state": test_breaker.state
                }
            )
            
        except Exception as e:
            return self.log_test_result(
                "test_circuit_breaker_functionality",
                False,
                error=str(e)
            )
    
    async def test_error_metrics_tracking(self):
        """Test 4: Verify error metrics tracking and reporting."""
        try:
            # Clear existing metrics
            error_metrics.error_counts.clear()
            error_metrics.error_categories.clear()
            error_metrics.last_errors.clear()
            
            # Create test errors
            test_errors = [
                N8nConnectionError("Test connection error 1"),
                N8nConnectionError("Test connection error 2"),
                N8nAuthenticationError("Test auth error"),
                N8nTimeoutError("Test timeout error")
            ]
            
            # Get metrics summary
            initial_summary = error_metrics.get_error_summary()
            
            # Create new errors for current test
            for error in test_errors:
                # Errors are automatically recorded when created
                pass
            
            # Get updated metrics
            final_summary = error_metrics.get_error_summary()
            
            # Verify metrics tracking
            total_errors_increased = final_summary["total_errors"] > initial_summary["total_errors"]
            categories_tracked = len(final_summary["error_categories"]) > 0
            recent_errors_recorded = len(final_summary["recent_errors"]) > 0
            
            passed = (
                total_errors_increased and
                categories_tracked and
                recent_errors_recorded
            )
            
            return self.log_test_result(
                "test_error_metrics_tracking",
                passed,
                {
                    "initial_total": initial_summary["total_errors"],
                    "final_total": final_summary["total_errors"],
                    "categories": list(final_summary["error_categories"].keys()),
                    "recent_errors_count": len(final_summary["recent_errors"])
                }
            )
            
        except Exception as e:
            return self.log_test_result(
                "test_error_metrics_tracking",
                False,
                error=str(e)
            )
    
    async def test_error_recovery_manager(self):
        """Test 5: Verify error recovery manager functionality."""
        try:
            # Test recovery strategies for different error types
            test_error = N8nConnectionError("Test recovery error")
            
            # Attempt error recovery
            recovery_result = await error_recovery_manager.handle_error(test_error)
            
            # Verify recovery result structure
            has_error_info = "error" in recovery_result
            has_strategies = "strategies_attempted" in recovery_result
            has_success_flag = "recovery_successful" in recovery_result
            has_final_action = "final_action" in recovery_result
            
            # Verify strategies were attempted
            strategies_attempted = len(recovery_result.get("strategies_attempted", [])) > 0
            
            passed = (
                has_error_info and
                has_strategies and
                has_success_flag and
                has_final_action and
                strategies_attempted
            )
            
            return self.log_test_result(
                "test_error_recovery_manager",
                passed,
                {
                    "recovery_result": recovery_result,
                    "strategies_count": len(recovery_result.get("strategies_attempted", []))
                }
            )
            
        except Exception as e:
            return self.log_test_result(
                "test_error_recovery_manager",
                False,
                error=str(e)
            )
    
    async def test_system_health_monitoring(self):
        """Test 6: Verify system health monitoring functionality."""
        try:
            # Test error handling health
            error_health = get_error_handling_health()
            
            # Test logging health
            logging_health = check_logging_health()
            
            # Verify health status structure
            error_health_valid = (
                "circuit_breakers" in error_health and
                "error_metrics" in error_health and
                "recovery_manager_status" in error_health
            )
            
            logging_health_valid = (
                "status" in logging_health and
                "log_directory_exists" in logging_health
            )
            
            passed = error_health_valid and logging_health_valid
            
            return self.log_test_result(
                "test_system_health_monitoring",
                passed,
                {
                    "error_handling_health": error_health,
                    "logging_health": logging_health
                }
            )
            
        except Exception as e:
            return self.log_test_result(
                "test_system_health_monitoring",
                False,
                error=str(e)
            )
    
    async def test_workflow_context_tracking(self):
        """Test 7: Verify workflow context tracking in logs."""
        try:
            from utils.logging_config import WorkflowLogContext
            
            # Create test context
            context = WorkflowLogContext(
                workflow_id="test_workflow_123",
                execution_id="test_execution_456",
                lead_id=789,
                organization_id=1
            )
            
            # Test context logger
            context_logger = get_n8n_logger("context_test")
            context_logger.set_context(context)
            
            # Log message with context
            context_logger.info("Test message with context", extra_fields={"test_data": "context_test"})
            
            # Verify context dictionary
            context_dict = context.to_dict()
            
            required_fields = ["workflow_id", "execution_id", "lead_id", "organization_id", "timestamp"]
            has_all_fields = all(field in context_dict for field in required_fields)
            
            # Clear context
            context_logger.clear_context()
            
            passed = has_all_fields and context_dict["workflow_id"] == "test_workflow_123"
            
            return self.log_test_result(
                "test_workflow_context_tracking",
                passed,
                {
                    "context_fields": list(context_dict.keys()),
                    "workflow_id": context_dict["workflow_id"],
                    "has_all_required_fields": has_all_fields
                }
            )
            
        except Exception as e:
            return self.log_test_result(
                "test_workflow_context_tracking",
                False,
                error=str(e)
            )
    
    async def run_all_tests(self):
        """Run all error handling and logging tests."""
        logger.info("🧪 Starting comprehensive error handling and logging test suite")
        
        test_methods = [
            self.test_logging_configuration,
            self.test_custom_exceptions,
            self.test_circuit_breaker_functionality,
            self.test_error_metrics_tracking,
            self.test_error_recovery_manager,
            self.test_system_health_monitoring,
            self.test_workflow_context_tracking
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                test_name = test_method.__name__
                self.log_test_result(test_name, False, error=f"Test execution failed: {str(e)}")
                logger.error(f"Test {test_name} execution failed", exc_info=True)
        
        # Finalize results
        self.test_results["end_time"] = datetime.utcnow().isoformat()
        self.test_results["duration"] = "Test completed"
        
        # Log final summary
        summary = self.test_results["summary"]
        success_rate = (summary["passed"] / summary["total_tests"]) * 100 if summary["total_tests"] > 0 else 0
        
        logger.info(
            f"🎯 Test suite completed: {summary['passed']}/{summary['total_tests']} tests passed ({success_rate:.1f}%)",
            extra_fields=self.test_results["summary"]
        )
        
        if summary["failed"] > 0:
            logger.error(f"❌ {summary['failed']} tests failed:")
            for error in summary["errors"]:
                logger.error(f"   - {error}")
        
        return self.test_results
    
    def save_test_results(self, filename: str = None):
        """Save test results to JSON file."""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_error_handling_{timestamp}.json"
        
        results_dir = Path("logs/test")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = results_dir / filename
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"📊 Test results saved to {results_file}")
        return results_file

async def main():
    """Main test execution function."""
    print("=" * 80)
    print("🔧 N8N ERROR HANDLING AND LOGGING TEST SUITE - TASK 5.4")
    print("=" * 80)
    
    test_suite = ErrorHandlingTestSuite()
    
    try:
        # Run all tests
        results = await test_suite.run_all_tests()
        
        # Save results
        results_file = test_suite.save_test_results()
        
        # Print summary
        summary = results["summary"]
        print(f"\n📋 TEST SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: ✅ {summary['passed']}")
        print(f"   Failed: ❌ {summary['failed']}")
        
        if summary['failed'] == 0:
            print(f"\n🎉 ALL TESTS PASSED! Task 5.4 implementation is working correctly.")
            print(f"✅ Error handling and logging mechanisms are fully functional.")
        else:
            print(f"\n⚠️  Some tests failed. Check the logs for details.")
            print(f"📄 Detailed results saved to: {results_file}")
        
        return summary['failed'] == 0
        
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}", exc_info=True)
        print(f"❌ Test suite execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 