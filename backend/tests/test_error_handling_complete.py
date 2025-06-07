"""
Comprehensive test for n8n error handling and logging mechanisms.
This test validates that task 5.4 (Implement error handling and logging) is complete.
"""
import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict

# Test imports for error handling and logging
from utils.logging_config import (
    LoggingConfig, get_n8n_logger, ErrorCategory, WorkflowLogContext, 
    StructuredFormatter, N8nLogger
)
from utils.error_handling import (
    N8nConnectionError, N8nAuthenticationError, N8nApiError, N8nTimeoutError,
    N8nValidationError, N8nWorkflowExecutionError, N8nConfigurationError,
    handle_n8n_exception, with_retry, RetryConfig, ErrorSeverity,
    error_recovery_manager, N8nBaseException
)
from n8n_client import N8nClient
from services.n8n_service import N8nService

logger = get_n8n_logger("error_handling_test")

class ErrorHandlingTester:
    """Comprehensive error handling and logging test suite."""
    
    def __init__(self):
        """Initialize the error handling tester."""
        self.test_results = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Set up enhanced logging for testing."""
        LoggingConfig.setup_logging(
            log_level="DEBUG",
            enable_console=True,
            enable_file=True,
            enable_structured=True
        )
        logger.info("Logging configuration initialized for error handling tests")
    
    def test_logging_infrastructure(self) -> bool:
        """Test logging infrastructure setup."""
        try:
            logger.info("Testing logging infrastructure...")
            
            # Test 1: Verify log directory exists
            logs_path = Path("logs")
            assert logs_path.exists(), "Logs directory should exist"
            logger.info("✅ Logs directory exists")
            
            # Test 2: Verify log files are created
            expected_files = ["n8n_integration.log", "n8n_errors.log"]
            for log_file in expected_files:
                log_path = logs_path / log_file
                assert log_path.exists(), f"Log file {log_file} should exist"
                logger.info(f"✅ Log file {log_file} exists")
            
            # Test 3: Test context logging
            context = WorkflowLogContext(
                workflow_id="test-workflow",
                execution_id="test-execution",
                lead_id=123,
                organization_id=456
            )
            logger.set_context(context)
            logger.info("Testing context logging", extra_fields={"test": "context"})
            logger.clear_context()
            logger.info("✅ Context logging working")
            
            # Test 4: Test error categorization
            logger.error(
                "Test error message",
                error_category=ErrorCategory.WORKFLOW_EXECUTION_ERROR,
                extra_fields={"error_code": "TEST_001"}
            )
            logger.info("✅ Error categorization working")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Logging infrastructure test failed: {e}")
            return False
    
    def test_custom_exceptions(self) -> bool:
        """Test custom exception hierarchy."""
        try:
            logger.info("Testing custom exception hierarchy...")
            
            # Test all custom exception types
            test_context = WorkflowLogContext(workflow_id="test", lead_id=1)
            
            exceptions_to_test = [
                (N8nConnectionError, "Test connection error"),
                (N8nAuthenticationError, "Test auth error"),
                (N8nApiError, "Test API error"),
                (N8nTimeoutError, "Test timeout error"),
                (N8nValidationError, "Test validation error"),
                (N8nWorkflowExecutionError, "Test execution error"),
                (N8nConfigurationError, "Test config error"),
            ]
            
            for exception_class, message in exceptions_to_test:
                try:
                    raise exception_class(message, context=test_context)
                except N8nBaseException as e:
                    # Verify exception properties
                    assert e.message == message, f"Message should match for {exception_class.__name__}"
                    assert e.context == test_context, f"Context should match for {exception_class.__name__}"
                    assert hasattr(e, 'error_category'), f"Should have error_category for {exception_class.__name__}"
                    assert hasattr(e, 'severity'), f"Should have severity for {exception_class.__name__}"
                    assert hasattr(e, 'recovery_action'), f"Should have recovery_action for {exception_class.__name__}"
                    
                    # Test to_dict method
                    error_dict = e.to_dict()
                    assert isinstance(error_dict, dict), f"to_dict should return dict for {exception_class.__name__}"
                    assert 'error_type' in error_dict, f"Should have error_type for {exception_class.__name__}"
                    assert 'message' in error_dict, f"Should have message for {exception_class.__name__}"
                    
                    logger.info(f"✅ {exception_class.__name__} working correctly")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Custom exceptions test failed: {e}")
            traceback.print_exc()
            return False
    
    async def test_retry_mechanism(self) -> bool:
        """Test retry decorator and circuit breaker."""
        try:
            logger.info("Testing retry mechanism...")
            
            # Test retry with success after failures
            call_count = 0
            
            @with_retry(
                config=RetryConfig(max_attempts=3, base_delay=0.1),
                circuit_breaker_key="test_retry"
            )
            async def flaky_function():
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise N8nConnectionError("Simulated connection failure")
                return {"success": True, "attempts": call_count}
            
            result = await flaky_function()
            assert result["success"] == True, "Should succeed after retries"
            assert result["attempts"] == 3, "Should have made 3 attempts"
            logger.info("✅ Retry mechanism working correctly")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Retry mechanism test failed: {e}")
            return False
    
    async def test_error_recovery_manager(self) -> bool:
        """Test error recovery manager."""
        try:
            logger.info("Testing error recovery manager...")
            
            # Test different error scenarios
            test_errors = [
                N8nConnectionError("Connection failed"),
                N8nAuthenticationError("Auth failed"),
                N8nWorkflowExecutionError("Execution failed"),
                N8nValidationError("Validation failed"),
            ]
            
            for error in test_errors:
                recovery_result = await error_recovery_manager.handle_error(error)
                assert isinstance(recovery_result, dict), "Recovery should return dict"
                assert "action" in recovery_result, "Recovery should specify action"
                logger.info(f"✅ Recovery for {type(error).__name__}: {recovery_result['action']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recovery manager test failed: {e}")
            return False
    
    @handle_n8n_exception
    async def test_exception_decorator(self) -> bool:
        """Test the exception handling decorator."""
        try:
            logger.info("Testing exception handling decorator...")
            
            # This should convert generic exceptions to N8nBaseException
            def failing_function():
                raise ValueError("Generic error")
            
            try:
                failing_function()
            except N8nBaseException as e:
                assert isinstance(e, N8nBaseException), "Should convert to N8nBaseException"
                logger.info("✅ Exception decorator working correctly")
                return True
            except Exception:
                logger.error("❌ Exception decorator failed to convert exception")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Exception decorator test failed: {e}")
            return False
    
    async def test_real_integration_error_handling(self) -> bool:
        """Test error handling in real integration scenarios."""
        try:
            logger.info("Testing real integration error handling...")
            
            # Test 1: Connection error handling
            try:
                # Use invalid URL to force connection error
                invalid_client = N8nClient(base_url="http://invalid-url:9999/rest")
                await invalid_client.health_check()
                logger.error("❌ Should have failed with connection error")
                return False
            except N8nConnectionError as e:
                logger.info("✅ Connection error properly handled")
            except Exception as e:
                logger.error(f"❌ Unexpected exception type: {type(e)}")
                return False
            
            # Test 2: Authentication error handling
            try:
                # Use invalid credentials
                auth_client = N8nClient(
                    base_url="http://localhost:5678/rest",
                    email="invalid@example.com",
                    password="wrongpassword"
                )
                await auth_client.authenticate()
                logger.error("❌ Should have failed with auth error")
                return False
            except N8nAuthenticationError as e:
                logger.info("✅ Authentication error properly handled")
            except Exception as e:
                logger.error(f"❌ Unexpected exception type: {type(e)}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Real integration error handling test failed: {e}")
            return False
    
    async def test_service_layer_error_handling(self) -> bool:
        """Test service layer error handling."""
        try:
            logger.info("Testing service layer error handling...")
            
            from unittest.mock import AsyncMock, MagicMock
            
            # Mock database session
            mock_db = MagicMock()
            service = N8nService(mock_db)
            
            # Test health check error handling
            # Mock the client to raise an exception
            service._n8n_client = AsyncMock()
            service._n8n_client.health_check.side_effect = Exception("Connection failed")
            
            # Health check should handle the error gracefully
            health_result = await service.health_check()
            assert health_result == False, "Health check should return False on error"
            logger.info("✅ Service layer health check error handling working")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Service layer error handling test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all error handling and logging tests."""
        logger.info("🧪 Starting comprehensive error handling and logging tests...")
        
        tests = [
            ("Logging Infrastructure", self.test_logging_infrastructure),
            ("Custom Exceptions", self.test_custom_exceptions),
            ("Retry Mechanism", self.test_retry_mechanism),
            ("Error Recovery Manager", self.test_error_recovery_manager),
            ("Exception Decorator", self.test_exception_decorator),
            ("Real Integration Error Handling", self.test_real_integration_error_handling),
            ("Service Layer Error Handling", self.test_service_layer_error_handling),
        ]
        
        for test_name, test_function in tests:
            try:
                logger.info(f"\n📋 Running test: {test_name}")
                if asyncio.iscoroutinefunction(test_function):
                    result = await test_function()
                else:
                    result = test_function()
                
                self.test_results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                logger.info(f"{status}: {test_name}")
                
            except Exception as e:
                logger.error(f"❌ FAILED: {test_name} - {e}")
                self.test_results[test_name] = False
        
        return self.test_results
    
    def print_summary(self):
        """Print test results summary."""
        logger.info("\n" + "="*60)
        logger.info("🧪 ERROR HANDLING & LOGGING TEST SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {test_name}")
        
        logger.info(f"\n📊 Results: {passed_tests}/{total_tests} tests passed")
        
        if failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED! Task 5.4 is COMPLETE!")
            logger.info("✅ Error handling and logging implementation is working correctly.")
        else:
            logger.info(f"⚠️  {failed_tests} tests failed. Task 5.4 needs additional work.")
        
        logger.info("="*60)

async def main():
    """Run the comprehensive error handling test suite."""
    tester = ErrorHandlingTester()
    
    try:
        results = await tester.run_all_tests()
        tester.print_summary()
        
        # Check if all tests passed
        all_passed = all(results.values())
        return all_passed
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Running comprehensive error handling and logging tests...")
    success = asyncio.run(main())
    exit(0 if success else 1) 