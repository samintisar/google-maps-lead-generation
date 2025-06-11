"""
Automation Router

FastAPI router for managing Python automation scripts,
scheduling, and execution. Replaces n8n workflow endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..automation import AutomationEngine, AutomationScheduler, ScriptManager
from ..automation.scripts import create_default_templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["automation"])

# Global instances (would be properly injected in production)
automation_engine = None
automation_scheduler = None
script_manager = None

def get_automation_engine() -> AutomationEngine:
    """Get automation engine instance"""
    global automation_engine
    if automation_engine is None:
        raise HTTPException(status_code=500, detail="Automation engine not initialized")
    return automation_engine

def get_automation_scheduler() -> AutomationScheduler:
    """Get automation scheduler instance"""
    global automation_scheduler
    if automation_scheduler is None:
        raise HTTPException(status_code=500, detail="Automation scheduler not initialized")
    return automation_scheduler

def get_script_manager() -> ScriptManager:
    """Get script manager instance"""
    global script_manager
    if script_manager is None:
        raise HTTPException(status_code=500, detail="Script manager not initialized")
    return script_manager

@router.get("/scripts")
async def list_scripts(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    script_manager: ScriptManager = Depends(get_script_manager)
):
    """List all available automation scripts"""
    try:
        if category:
            scripts = script_manager.get_scripts_by_category(category)
            return {"scripts": list(scripts.values()), "category": category}
        else:
            scripts = script_manager.list_scripts()
            return {"scripts": scripts, "categories": script_manager.list_categories()}
    except Exception as e:
        logger.error(f"Error listing scripts: {e}")
        raise HTTPException(status_code=500, detail="Failed to list scripts")

@router.get("/scripts/{script_name}")
async def get_script_details(
    script_name: str,
    current_user: User = Depends(get_current_user),
    script_manager: ScriptManager = Depends(get_script_manager)
):
    """Get details of a specific script"""
    script = script_manager.get_script(script_name)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return {
        "name": script_name,
        "category": script["category"],
        "description": script["description"],
        "parameters": script["parameters"],
        "schedule": script["schedule"],
        "is_async": script["is_async"]
    }

@router.post("/scripts/{script_name}/execute")
async def execute_script(
    script_name: str,
    context: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    automation_engine: AutomationEngine = Depends(get_automation_engine),
    background_tasks: BackgroundTasks = None
):
    """Execute a script immediately"""
    try:
        # Execute the script
        result = await automation_engine.execute_script(
            script_name=script_name,
            context=context or {}
        )
        
        return {
            "execution_id": result.execution_id,
            "script_name": result.script_name,
            "status": result.status.value,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "result_data": result.result_data,
            "error_message": result.error_message
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing script {script_name}: {e}")
        raise HTTPException(status_code=500, detail="Script execution failed")

@router.get("/executions")
async def get_execution_history(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    automation_engine: AutomationEngine = Depends(get_automation_engine)
):
    """Get execution history"""
    try:
        history = automation_engine.get_execution_history(limit=limit)
        return {
            "executions": [
                {
                    "execution_id": result.execution_id,
                    "script_name": result.script_name,
                    "status": result.status.value,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "error_message": result.error_message
                }
                for result in history
            ],
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get execution history")

@router.get("/executions/active")
async def get_active_executions(
    current_user: User = Depends(get_current_user),
    automation_engine: AutomationEngine = Depends(get_automation_engine)
):
    """Get currently active executions"""
    try:
        active = automation_engine.get_active_executions()
        return {
            "active_executions": [
                {
                    "execution_id": result.execution_id,
                    "script_name": result.script_name,
                    "status": result.status.value,
                    "start_time": result.start_time
                }
                for result in active.values()
            ],
            "count": len(active)
        }
    except Exception as e:
        logger.error(f"Error getting active executions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active executions")

@router.delete("/executions/{execution_id}")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    automation_engine: AutomationEngine = Depends(get_automation_engine)
):
    """Cancel an active execution"""
    try:
        success = await automation_engine.cancel_execution(execution_id)
        if success:
            return {"message": "Execution cancelled", "execution_id": execution_id}
        else:
            raise HTTPException(status_code=404, detail="Execution not found or not active")
    except Exception as e:
        logger.error(f"Error cancelling execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel execution")

@router.get("/jobs")
async def list_scheduled_jobs(
    current_user: User = Depends(get_current_user),
    scheduler: AutomationScheduler = Depends(get_automation_scheduler)
):
    """List all scheduled jobs"""
    try:
        jobs = scheduler.get_jobs()
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Error listing scheduled jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list scheduled jobs")

@router.post("/jobs/schedule")
async def schedule_job(
    job_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    scheduler: AutomationScheduler = Depends(get_automation_scheduler)
):
    """Schedule a new job"""
    try:
        script_name = job_config.get("script_name")
        job_id = job_config.get("job_id")
        schedule_type = job_config.get("schedule_type")  # 'cron', 'interval', 'once'
        
        if not all([script_name, job_id, schedule_type]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        if schedule_type == "cron":
            cron_expression = job_config.get("cron_expression")
            if not cron_expression:
                raise HTTPException(status_code=400, detail="cron_expression required for cron jobs")
            
            job_id = scheduler.schedule_cron(
                script_name=script_name,
                cron_expression=cron_expression,
                job_id=job_id,
                args=job_config.get("args", ()),
                kwargs=job_config.get("kwargs", {})
            )
            
        elif schedule_type == "interval":
            interval_seconds = job_config.get("interval_seconds")
            if not interval_seconds:
                raise HTTPException(status_code=400, detail="interval_seconds required for interval jobs")
            
            job_id = scheduler.schedule_interval(
                script_name=script_name,
                interval_seconds=interval_seconds,
                job_id=job_id,
                args=job_config.get("args", ()),
                kwargs=job_config.get("kwargs", {})
            )
            
        elif schedule_type == "once":
            run_date = job_config.get("run_date")
            if not run_date:
                raise HTTPException(status_code=400, detail="run_date required for one-time jobs")
            
            # Parse run_date string to datetime
            if isinstance(run_date, str):
                run_date = datetime.fromisoformat(run_date)
            
            job_id = scheduler.schedule_once(
                script_name=script_name,
                run_date=run_date,
                job_id=job_id,
                args=job_config.get("args", ()),
                kwargs=job_config.get("kwargs", {})
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid schedule_type")
        
        return {"message": "Job scheduled successfully", "job_id": job_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error scheduling job: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule job")

@router.delete("/jobs/{job_id}")
async def remove_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    scheduler: AutomationScheduler = Depends(get_automation_scheduler)
):
    """Remove a scheduled job"""
    try:
        scheduler.remove_job(job_id)
        return {"message": "Job removed", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error removing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove job")

@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    scheduler: AutomationScheduler = Depends(get_automation_scheduler)
):
    """Pause a scheduled job"""
    try:
        scheduler.pause_job(job_id)
        return {"message": "Job paused", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause job")

@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    scheduler: AutomationScheduler = Depends(get_automation_scheduler)
):
    """Resume a paused job"""
    try:
        scheduler.resume_job(job_id)
        return {"message": "Job resumed", "job_id": job_id}
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume job")

@router.get("/templates")
async def list_templates(
    current_user: User = Depends(get_current_user),
    script_manager: ScriptManager = Depends(get_script_manager)
):
    """List all workflow templates"""
    try:
        templates = script_manager.list_templates()
        return {"templates": templates, "count": len(templates)}
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")

@router.get("/templates/{template_name}")
async def get_template(
    template_name: str,
    current_user: User = Depends(get_current_user),
    script_manager: ScriptManager = Depends(get_script_manager)
):
    """Get a specific template"""
    template = script_manager.get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "name": template_name,
        "description": template["description"],
        "parameters": template["parameters"],
        "steps": template["steps"]
    }

@router.post("/templates/{template_name}/execute")
async def execute_template(
    template_name: str,
    context: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    script_manager: ScriptManager = Depends(get_script_manager),
    automation_engine: AutomationEngine = Depends(get_automation_engine)
):
    """Execute a workflow template"""
    try:
        template = script_manager.get_template(template_name)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Execute the workflow
        results = await automation_engine.execute_workflow(
            workflow_config=template,
            initial_context=context or {}
        )
        
        return {
            "template_name": template_name,
            "execution_results": [
                {
                    "execution_id": result.execution_id,
                    "script_name": result.script_name,
                    "status": result.status.value,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "error_message": result.error_message
                }
                for result in results
            ],
            "total_steps": len(results),
            "successful_steps": len([r for r in results if r.status.value == "success"])
        }
        
    except Exception as e:
        logger.error(f"Error executing template {template_name}: {e}")
        raise HTTPException(status_code=500, detail="Template execution failed")

@router.get("/health")
async def health_check(
    automation_engine: AutomationEngine = Depends(get_automation_engine),
    scheduler: AutomationScheduler = Depends(get_automation_scheduler),
    script_manager: ScriptManager = Depends(get_script_manager)
):
    """Health check endpoint for automation system"""
    try:
        from ..automation.metrics import metrics_collector
        
        # Get health data from metrics collector
        health_data = metrics_collector.health_check()
        
        # Additional health checks
        health_data.update({
            "automation_engine": "operational" if automation_engine else "unavailable",
            "scheduler": "operational" if scheduler else "unavailable", 
            "script_manager": "operational" if script_manager else "unavailable",
            "registered_scripts": len(automation_engine.scripts) if automation_engine else 0,
            "active_executions": len(automation_engine.active_executions) if automation_engine else 0,
            "execution_history_size": len(automation_engine.execution_history) if automation_engine else 0,
        })
        
        # Determine overall status
        overall_healthy = all([
            automation_engine is not None,
            scheduler is not None,
            script_manager is not None,
            health_data.get('status') == 'healthy'
        ])
        
        health_data['overall_status'] = 'healthy' if overall_healthy else 'degraded'
        
        status_code = 200 if overall_healthy else 503
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )

# Initialization function
async def init_automation_system(database_url: str, redis_client=None):
    """Initialize the automation system"""
    global automation_engine, automation_scheduler, script_manager
    
    try:
        # Initialize components
        from ..database import SessionLocal
        script_manager = ScriptManager()
        automation_engine = AutomationEngine(db_session_factory=SessionLocal, redis_client=redis_client)
        automation_scheduler = AutomationScheduler(database_url=database_url)
        
        # Create default templates
        create_default_templates(script_manager)
        
        # Start scheduler
        await automation_scheduler.start()
        
        logger.info("Automation system initialized successfully")
        
        # Return the automation engine for webhook integration
        return automation_engine
        
    except Exception as e:
        logger.error(f"Failed to initialize automation system: {e}")
        raise 