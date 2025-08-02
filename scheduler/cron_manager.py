"""
Cron Manager
Handles scheduled task execution with cron-like functionality
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timedelta
import json
from croniter import croniter

logger = logging.getLogger(__name__)

class CronJob:
    """Represents a single cron job"""
    
    def __init__(self, job_id: str, cron_expression: str, task_name: str, 
                 task_params: Dict[str, Any], callback: Callable = None):
        self.job_id = job_id
        self.cron_expression = cron_expression
        self.task_name = task_name
        self.task_params = task_params
        self.callback = callback
        self.is_active = True
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.error_count = 0
        self.created_at = datetime.now()
        
        # Calculate next run time
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate the next run time based on cron expression"""
        try:
            cron = croniter(self.cron_expression, datetime.now())
            self.next_run = cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Invalid cron expression {self.cron_expression}: {e}")
            self.next_run = None
    
    def should_run(self) -> bool:
        """Check if job should run now"""
        if not self.is_active or not self.next_run:
            return False
        return datetime.now() >= self.next_run
    
    def mark_completed(self, success: bool = True):
        """Mark job as completed and calculate next run"""
        self.last_run = datetime.now()
        self.run_count += 1
        
        if not success:
            self.error_count += 1
        
        self._calculate_next_run()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        return {
            "job_id": self.job_id,
            "cron_expression": self.cron_expression,
            "task_name": self.task_name,
            "task_params": self.task_params,
            "is_active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat()
        }

class CronManager:
    """Manages cron jobs and task scheduling"""
    
    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}
        self.task_registry: Dict[str, Callable] = {}
        self.is_running = False
        self.check_interval = 60  # Check jobs every minute
        self._scheduler_task = None
        
        # Register built-in tasks
        self._register_builtin_tasks()
    
    def _register_builtin_tasks(self):
        """Register built-in task types"""
        self.task_registry.update({
            "browser_navigate": self._task_browser_navigate,
            "account_create": self._task_account_create,
            "data_scrape": self._task_data_scrape,
            "health_check": self._task_health_check,
            "cleanup": self._task_cleanup,
            "backup": self._task_backup
        })
    
    async def start(self):
        """Start the cron manager"""
        if self.is_running:
            return
        
        self.is_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Cron manager started")
    
    async def stop(self):
        """Stop the cron manager"""
        self.is_running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Cron manager stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                await self._check_and_run_jobs()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _check_and_run_jobs(self):
        """Check and run jobs that are due"""
        current_time = datetime.now()
        
        for job in list(self.jobs.values()):
            if job.should_run():
                logger.info(f"Running job {job.job_id}: {job.task_name}")
                
                # Run job in background
                asyncio.create_task(self._execute_job(job))
    
    async def _execute_job(self, job: CronJob):
        """Execute a single job"""
        try:
            task_func = self.task_registry.get(job.task_name)
            
            if not task_func:
                logger.error(f"Task function not found: {job.task_name}")
                job.mark_completed(success=False)
                return
            
            # Execute the task
            if asyncio.iscoroutinefunction(task_func):
                await task_func(job.task_params)
            else:
                task_func(job.task_params)
            
            job.mark_completed(success=True)
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job.mark_completed(success=False)
    
    async def schedule_job(self, cron_expression: str, task_name: str, 
                          task_params: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a new cron job"""
        try:
            # Validate cron expression
            try:
                croniter(cron_expression)
            except Exception as e:
                return {"success": False, "error": f"Invalid cron expression: {e}"}
            
            # Validate task name
            if task_name not in self.task_registry:
                return {
                    "success": False, 
                    "error": f"Unknown task: {task_name}",
                    "available_tasks": list(self.task_registry.keys())
                }
            
            # Generate job ID
            job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.jobs)}"
            
            # Create job
            job = CronJob(job_id, cron_expression, task_name, task_params)
            self.jobs[job_id] = job
            
            logger.info(f"Scheduled job {job_id}: {task_name} with expression {cron_expression}")
            
            return {
                "success": True,
                "job_id": job_id,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "message": f"Job scheduled successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule job: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all jobs"""
        return {
            "is_running": self.is_running,
            "total_jobs": len(self.jobs),
            "active_jobs": len([j for j in self.jobs.values() if j.is_active]),
            "available_tasks": list(self.task_registry.keys()),
            "jobs": [job.to_dict() for job in self.jobs.values()]
        }
    
    async def pause_job(self, job_id: str) -> Dict[str, Any]:
        """Pause a specific job"""
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
        
        self.jobs[job_id].is_active = False
        return {"success": True, "message": f"Job {job_id} paused"}
    
    async def resume_job(self, job_id: str) -> Dict[str, Any]:
        """Resume a specific job"""
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
        
        job = self.jobs[job_id]
        job.is_active = True
        job._calculate_next_run()
        
        return {"success": True, "message": f"Job {job_id} resumed"}
    
    async def delete_job(self, job_id: str) -> Dict[str, Any]:
        """Delete a specific job"""
        if job_id not in self.jobs:
            return {"success": False, "error": "Job not found"}
        
        del self.jobs[job_id]
        return {"success": True, "message": f"Job {job_id} deleted"}
    
    def register_task(self, task_name: str, task_func: Callable):
        """Register a new task function"""
        self.task_registry[task_name] = task_func
        logger.info(f"Registered task: {task_name}")
    
    # Built-in task implementations
    async def _task_browser_navigate(self, params: Dict[str, Any]):
        """Task: Navigate browser to URL"""
        url = params.get("url")
        if not url:
            raise ValueError("URL parameter required")
        
        # This would integrate with the browser manager
        logger.info(f"Browser navigation task: {url}")
    
    async def _task_account_create(self, params: Dict[str, Any]):
        """Task: Create social media account"""
        platform = params.get("platform")
        account_data = params.get("account_data", {})
        
        if not platform:
            raise ValueError("Platform parameter required")
        
        # This would integrate with the account creator
        logger.info(f"Account creation task: {platform}")
    
    async def _task_data_scrape(self, params: Dict[str, Any]):
        """Task: Scrape data from websites"""
        urls = params.get("urls", [])
        selectors = params.get("selectors", {})
        
        logger.info(f"Data scraping task: {len(urls)} URLs")
    
    async def _task_health_check(self, params: Dict[str, Any]):
        """Task: Perform system health check"""
        logger.info("Health check task executed")
    
    async def _task_cleanup(self, params: Dict[str, Any]):
        """Task: Clean up temporary files and resources"""
        logger.info("Cleanup task executed")
    
    async def _task_backup(self, params: Dict[str, Any]):
        """Task: Backup important data"""
        logger.info("Backup task executed")