"""
Automation Scheduler

Handles scheduling of automation scripts using APScheduler.
Replaces n8n's cron and trigger functionality with Python-based scheduling.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

logger = logging.getLogger(__name__)

class AutomationScheduler:
    """
    Manages scheduling of automation scripts and tasks.
    Provides cron, interval, and one-time scheduling capabilities.
    """
    
    def __init__(self, database_url: str):
        # Configure job store with PostgreSQL
        jobstores = {
            'default': SQLAlchemyJobStore(url=database_url, tablename='automation_jobs')
        }
        
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        self._running = False
        self.registered_scripts: Dict[str, Callable] = {}
    
    async def start(self):
        """Start the scheduler"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("Automation scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        if self._running:
            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Automation scheduler stopped")
    
    def register_script(self, name: str, func: Callable):
        """Register an automation script function"""
        self.registered_scripts[name] = func
        logger.info(f"Registered automation script: {name}")
    
    def schedule_cron(
        self,
        script_name: str,
        cron_expression: str,
        job_id: str,
        args: tuple = (),
        kwargs: dict = None,
        replace_existing: bool = True
    ) -> str:
        """
        Schedule a script to run on a cron schedule
        
        Args:
            script_name: Name of the registered script
            cron_expression: Cron expression (e.g., "0 9 * * *" for daily at 9 AM)
            job_id: Unique identifier for this job
            args: Arguments to pass to the script
            kwargs: Keyword arguments to pass to the script
            replace_existing: Whether to replace existing job with same ID
        
        Returns:
            Job ID
        """
        if script_name not in self.registered_scripts:
            raise ValueError(f"Script {script_name} not registered")
        
        kwargs = kwargs or {}
        
        # Parse cron expression
        cron_parts = cron_expression.split()
        if len(cron_parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month day_of_week")
        
        minute, hour, day, month, day_of_week = cron_parts
        
        trigger = CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            timezone='UTC'
        )
        
        self.scheduler.add_job(
            self.registered_scripts[script_name],
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=replace_existing
        )
        
        logger.info(f"Scheduled cron job {job_id} for script {script_name}: {cron_expression}")
        return job_id
    
    def schedule_interval(
        self,
        script_name: str,
        interval_seconds: int,
        job_id: str,
        args: tuple = (),
        kwargs: dict = None,
        replace_existing: bool = True
    ) -> str:
        """
        Schedule a script to run at regular intervals
        
        Args:
            script_name: Name of the registered script
            interval_seconds: Interval in seconds
            job_id: Unique identifier for this job
            args: Arguments to pass to the script
            kwargs: Keyword arguments to pass to the script
            replace_existing: Whether to replace existing job with same ID
        
        Returns:
            Job ID
        """
        if script_name not in self.registered_scripts:
            raise ValueError(f"Script {script_name} not registered")
        
        kwargs = kwargs or {}
        
        trigger = IntervalTrigger(seconds=interval_seconds)
        
        self.scheduler.add_job(
            self.registered_scripts[script_name],
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=replace_existing
        )
        
        logger.info(f"Scheduled interval job {job_id} for script {script_name}: every {interval_seconds}s")
        return job_id
    
    def schedule_once(
        self,
        script_name: str,
        run_date: datetime,
        job_id: str,
        args: tuple = (),
        kwargs: dict = None,
        replace_existing: bool = True
    ) -> str:
        """
        Schedule a script to run once at a specific time
        
        Args:
            script_name: Name of the registered script
            run_date: When to run the script
            job_id: Unique identifier for this job
            args: Arguments to pass to the script
            kwargs: Keyword arguments to pass to the script
            replace_existing: Whether to replace existing job with same ID
        
        Returns:
            Job ID
        """
        if script_name not in self.registered_scripts:
            raise ValueError(f"Script {script_name} not registered")
        
        kwargs = kwargs or {}
        
        trigger = DateTrigger(run_date=run_date)
        
        self.scheduler.add_job(
            self.registered_scripts[script_name],
            trigger=trigger,
            id=job_id,
            args=args,
            kwargs=kwargs,
            replace_existing=replace_existing
        )
        
        logger.info(f"Scheduled one-time job {job_id} for script {script_name} at {run_date}")
        return job_id
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'trigger': str(job.trigger),
                'next_run_time': job.next_run_time,
                'args': job.args,
                'kwargs': job.kwargs
            })
        return jobs
    
    def pause_job(self, job_id: str):
        """Pause a scheduled job"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job {job_id}")
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
    
    def resume_job(self, job_id: str):
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job {job_id}")
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
    
    async def run_script_now(self, script_name: str, args: tuple = (), kwargs: dict = None):
        """Run a registered script immediately"""
        if script_name not in self.registered_scripts:
            raise ValueError(f"Script {script_name} not registered")
        
        kwargs = kwargs or {}
        
        try:
            # Run the script
            result = await self.registered_scripts[script_name](*args, **kwargs)
            logger.info(f"Successfully executed script {script_name}")
            return result
        except Exception as e:
            logger.error(f"Error executing script {script_name}: {e}")
            raise 