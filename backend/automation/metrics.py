"""
Automation Metrics

Prometheus metrics collection for the automation system.
Tracks execution performance, success rates, and system health.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary, Info
import time
import logging
from typing import Dict, Any
from datetime import datetime
from .engine import ExecutionStatus

logger = logging.getLogger(__name__)

# Execution Metrics
AUTOMATION_EXECUTIONS_TOTAL = Counter(
    'automation_executions_total',
    'Total number of automation script executions',
    ['script_name', 'status', 'triggered_by']
)

AUTOMATION_EXECUTION_DURATION = Histogram(
    'automation_execution_duration_seconds',
    'Time spent executing automation scripts',
    ['script_name', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float("inf")]
)

AUTOMATION_EXECUTION_ERRORS = Counter(
    'automation_execution_errors_total',
    'Total number of automation execution errors',
    ['script_name', 'error_type']
)

# Active Executions
AUTOMATION_ACTIVE_EXECUTIONS = Gauge(
    'automation_active_executions',
    'Number of currently active executions',
    ['script_name']
)

# Scheduler Metrics
AUTOMATION_SCHEDULED_JOBS = Gauge(
    'automation_scheduled_jobs_total',
    'Total number of scheduled jobs',
    ['job_type', 'status']
)

AUTOMATION_JOB_EXECUTIONS = Counter(
    'automation_job_executions_total',
    'Total number of scheduled job executions',
    ['job_id', 'script_name', 'status']
)

# Webhook Metrics
WEBHOOK_EVENTS_RECEIVED = Counter(
    'webhook_events_received_total',
    'Total number of webhook events received',
    ['webhook_id', 'event_type', 'source']
)

WEBHOOK_PROCESSING_DURATION = Histogram(
    'webhook_processing_duration_seconds',
    'Time spent processing webhook events',
    ['event_type', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, float("inf")]
)

WEBHOOK_PROCESSING_ERRORS = Counter(
    'webhook_processing_errors_total',
    'Total number of webhook processing errors',
    ['event_type', 'error_type']
)

# Script Management Metrics
AUTOMATION_SCRIPTS_REGISTERED = Gauge(
    'automation_scripts_registered_total',
    'Total number of registered automation scripts',
    ['category']
)

AUTOMATION_TEMPLATES_AVAILABLE = Gauge(
    'automation_templates_available_total',
    'Total number of available workflow templates'
)

# Performance Metrics
AUTOMATION_MEMORY_USAGE = Gauge(
    'automation_memory_usage_bytes',
    'Memory usage of automation components',
    ['component']
)

AUTOMATION_CPU_USAGE = Gauge(
    'automation_cpu_usage_percent',
    'CPU usage of automation components',
    ['component']
)

# System Health Metrics
AUTOMATION_SYSTEM_HEALTH = Gauge(
    'automation_system_health',
    'Overall automation system health (1 = healthy, 0 = unhealthy)',
    ['component']
)

AUTOMATION_LAST_EXECUTION_TIME = Gauge(
    'automation_last_execution_timestamp',
    'Timestamp of last successful execution',
    ['script_name']
)

# Queue Metrics
AUTOMATION_QUEUE_SIZE = Gauge(
    'automation_queue_size',
    'Number of items in automation queues',
    ['queue_type']
)

# Database Connection Metrics
AUTOMATION_DB_CONNECTIONS = Gauge(
    'automation_db_connections_active',
    'Number of active database connections from automation'
)

AUTOMATION_DB_OPERATIONS = Counter(
    'automation_db_operations_total',
    'Total number of database operations',
    ['operation_type', 'status']
)

# Application Info
automation_info = Info(
    'automation_system_info',
    'Information about the automation system'
)

class AutomationMetricsCollector:
    """Collects and manages automation metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.script_execution_times = {}
        self.webhook_processing_times = {}
        
        # Set initial system info
        automation_info.info({
            'version': '1.0.0',
            'component': 'automation_engine',
            'started_at': datetime.utcnow().isoformat()
        })
        
        logger.info("Automation metrics collector initialized")
    
    def record_script_execution_start(self, script_name: str, execution_id: str, triggered_by: str = 'manual'):
        """Record the start of a script execution"""
        start_time = time.time()
        self.script_execution_times[execution_id] = start_time
        
        # Increment active executions
        AUTOMATION_ACTIVE_EXECUTIONS.labels(script_name=script_name).inc()
        
        logger.debug(f"Started tracking execution {execution_id} for script {script_name}")
    
    def record_script_execution_end(self, script_name: str, execution_id: str, status: ExecutionStatus, triggered_by: str = 'manual', error_type: str = None):
        """Record the completion of a script execution"""
        if execution_id in self.script_execution_times:
            duration = time.time() - self.script_execution_times[execution_id]
            del self.script_execution_times[execution_id]
            
            # Record metrics
            AUTOMATION_EXECUTION_DURATION.labels(
                script_name=script_name,
                status=status.value
            ).observe(duration)
            
            AUTOMATION_EXECUTIONS_TOTAL.labels(
                script_name=script_name,
                status=status.value,
                triggered_by=triggered_by
            ).inc()
            
            # Record last successful execution
            if status == ExecutionStatus.SUCCESS:
                AUTOMATION_LAST_EXECUTION_TIME.labels(script_name=script_name).set(time.time())
            
            # Record errors if any
            if status == ExecutionStatus.FAILED and error_type:
                AUTOMATION_EXECUTION_ERRORS.labels(
                    script_name=script_name,
                    error_type=error_type
                ).inc()
            
            # Decrement active executions
            AUTOMATION_ACTIVE_EXECUTIONS.labels(script_name=script_name).dec()
            
            logger.debug(f"Completed tracking execution {execution_id} for script {script_name} (duration: {duration:.2f}s)")
    
    def record_webhook_processing_start(self, event_type: str, webhook_id: str, source: str = 'unknown'):
        """Record the start of webhook processing"""
        start_time = time.time()
        self.webhook_processing_times[webhook_id] = start_time
        
        # Record webhook received
        WEBHOOK_EVENTS_RECEIVED.labels(
            webhook_id=webhook_id,
            event_type=event_type,
            source=source
        ).inc()
        
        logger.debug(f"Started tracking webhook processing {webhook_id} for event {event_type}")
    
    def record_webhook_processing_end(self, event_type: str, webhook_id: str, status: str, error_type: str = None):
        """Record the completion of webhook processing"""
        if webhook_id in self.webhook_processing_times:
            duration = time.time() - self.webhook_processing_times[webhook_id]
            del self.webhook_processing_times[webhook_id]
            
            # Record processing duration
            WEBHOOK_PROCESSING_DURATION.labels(
                event_type=event_type,
                status=status
            ).observe(duration)
            
            # Record errors if any
            if status == 'failed' and error_type:
                WEBHOOK_PROCESSING_ERRORS.labels(
                    event_type=event_type,
                    error_type=error_type
                ).inc()
            
            logger.debug(f"Completed tracking webhook processing {webhook_id} (duration: {duration:.2f}s)")
    
    def update_scheduled_jobs_count(self, job_counts: Dict[str, int]):
        """Update scheduled jobs count metrics"""
        for job_type, count in job_counts.items():
            AUTOMATION_SCHEDULED_JOBS.labels(job_type=job_type, status='active').set(count)
    
    def record_job_execution(self, job_id: str, script_name: str, status: str):
        """Record a scheduled job execution"""
        AUTOMATION_JOB_EXECUTIONS.labels(
            job_id=job_id,
            script_name=script_name,
            status=status
        ).inc()
    
    def update_scripts_count(self, script_counts: Dict[str, int]):
        """Update registered scripts count by category"""
        for category, count in script_counts.items():
            AUTOMATION_SCRIPTS_REGISTERED.labels(category=category).set(count)
    
    def update_templates_count(self, count: int):
        """Update available templates count"""
        AUTOMATION_TEMPLATES_AVAILABLE.set(count)
    
    def update_system_health(self, component: str, is_healthy: bool):
        """Update system health status"""
        AUTOMATION_SYSTEM_HEALTH.labels(component=component).set(1 if is_healthy else 0)
    
    def update_queue_size(self, queue_type: str, size: int):
        """Update queue size metrics"""
        AUTOMATION_QUEUE_SIZE.labels(queue_type=queue_type).set(size)
    
    def record_db_operation(self, operation_type: str, status: str):
        """Record database operation"""
        AUTOMATION_DB_OPERATIONS.labels(
            operation_type=operation_type,
            status=status
        ).inc()
    
    def update_db_connections(self, count: int):
        """Update active database connections count"""
        AUTOMATION_DB_CONNECTIONS.set(count)
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check and return status"""
        try:
            uptime = self.get_uptime()
            
            # Basic health checks
            health_data = {
                'status': 'healthy',
                'uptime_seconds': uptime,
                'metrics_collector': 'operational',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Update health metrics
            self.update_system_health('metrics_collector', True)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.update_system_health('metrics_collector', False)
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global metrics collector instance
metrics_collector = AutomationMetricsCollector() 