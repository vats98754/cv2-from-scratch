"""
Job scheduling system with cron-like functionality.
Supports various triggers, persistence, and monitoring.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.asyncio import AsyncIOExecutor
except ImportError:
    # Fallback implementation without APScheduler
    AsyncIOScheduler = None
    CronTrigger = None
    IntervalTrigger = None
    DateTrigger = None

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TriggerType(Enum):
    """Supported trigger types"""
    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"
    IMMEDIATE = "immediate"

@dataclass
class JobConfig:
    """Job configuration"""
    id: str
    name: str
    function: str  # Function name or module path
    trigger_type: TriggerType
    trigger_config: Dict[str, Any]
    args: List[Any] = None
    kwargs: Dict[str, Any] = None
    max_instances: int = 1
    misfire_grace_time: int = 300  # seconds
    enabled: bool = True
    description: str = ""
    tags: List[str] = None

@dataclass
class JobExecution:
    """Job execution record"""
    job_id: str
    execution_id: str
    started_at: float
    finished_at: Optional[float] = None
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    duration: Optional[float] = None

class JobScheduler:
    """
    Advanced job scheduling system with cron-like functionality.
    Supports various triggers, job persistence, and monitoring.
    """
    
    def __init__(self, data_dir: str = "/tmp/scheduler"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.scheduler = None
        self.jobs: Dict[str, JobConfig] = {}
        self.executions: Dict[str, List[JobExecution]] = {}
        self.job_functions: Dict[str, Callable] = {}
        self.running = False
        
        # Initialize scheduler if APScheduler is available
        if AsyncIOScheduler:
            self._init_apscheduler()
        else:
            logger.warning("APScheduler not available, using basic implementation")
            self.scheduler = None
            
    def _init_apscheduler(self):
        """Initialize APScheduler"""
        jobstores = {
            'default': MemoryJobStore()
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
            job_defaults=job_defaults
        )
        
    async def start(self):
        """Start the job scheduler"""
        if self.scheduler:
            self.scheduler.start()
        else:
            # Start basic scheduler loop
            asyncio.create_task(self._basic_scheduler_loop())
            
        self.running = True
        await self._load_jobs()
        logger.info("Job scheduler started")
        
    async def stop(self):
        """Stop the job scheduler"""
        self.running = False
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
        await self._save_jobs()
        logger.info("Job scheduler stopped")
        
    def register_function(self, name: str, func: Callable):
        """Register a function that can be called by jobs"""
        self.job_functions[name] = func
        logger.info(f"Registered job function: {name}")
        
    async def add_cron_job(self, job_id: str, name: str, function: str,
                          cron_expression: str, **kwargs) -> bool:
        """Add a cron-triggered job"""
        # Parse cron expression
        cron_parts = cron_expression.split()
        if len(cron_parts) != 5:
            raise ValueError("Cron expression must have 5 parts: minute hour day month day_of_week")
            
        minute, hour, day, month, day_of_week = cron_parts
        
        trigger_config = {
            'minute': minute,
            'hour': hour,
            'day': day,
            'month': month,
            'day_of_week': day_of_week
        }
        
        return await self.add_job(
            job_id=job_id,
            name=name,
            function=function,
            trigger_type=TriggerType.CRON,
            trigger_config=trigger_config,
            **kwargs
        )
        
    async def add_interval_job(self, job_id: str, name: str, function: str,
                              seconds: int = None, minutes: int = None, 
                              hours: int = None, days: int = None, **kwargs) -> bool:
        """Add an interval-triggered job"""
        trigger_config = {}
        if seconds: trigger_config['seconds'] = seconds
        if minutes: trigger_config['minutes'] = minutes
        if hours: trigger_config['hours'] = hours
        if days: trigger_config['days'] = days
        
        if not trigger_config:
            raise ValueError("At least one time interval must be specified")
            
        return await self.add_job(
            job_id=job_id,
            name=name,
            function=function,
            trigger_type=TriggerType.INTERVAL,
            trigger_config=trigger_config,
            **kwargs
        )
        
    async def add_date_job(self, job_id: str, name: str, function: str,
                          run_date: Union[datetime, str], **kwargs) -> bool:
        """Add a date-triggered job (run once at specific time)"""
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date)
            
        trigger_config = {
            'run_date': run_date.isoformat()
        }
        
        return await self.add_job(
            job_id=job_id,
            name=name,
            function=function,
            trigger_type=TriggerType.DATE,
            trigger_config=trigger_config,
            **kwargs
        )
        
    async def add_job(self, job_id: str, name: str, function: str,
                     trigger_type: TriggerType, trigger_config: Dict[str, Any],
                     args: List[Any] = None, kwargs_: Dict[str, Any] = None,
                     **options) -> bool:
        """Add a job to the scheduler"""
        try:
            job_config = JobConfig(
                id=job_id,
                name=name,
                function=function,
                trigger_type=trigger_type,
                trigger_config=trigger_config,
                args=args or [],
                kwargs=kwargs_ or {},
                **options
            )
            
            # Validate function exists
            if function not in self.job_functions:
                raise ValueError(f"Function '{function}' not registered")
                
            self.jobs[job_id] = job_config
            self.executions[job_id] = []
            
            # Add to APScheduler if available
            if self.scheduler and self.running:
                await self._add_apscheduler_job(job_config)
                
            await self._save_jobs()
            logger.info(f"Added job: {job_id} ({name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")
            return False
            
    async def _add_apscheduler_job(self, job_config: JobConfig):
        """Add job to APScheduler"""
        if not self.scheduler:
            return
            
        # Create appropriate trigger
        if job_config.trigger_type == TriggerType.CRON:
            trigger = CronTrigger(**job_config.trigger_config)
        elif job_config.trigger_type == TriggerType.INTERVAL:
            trigger = IntervalTrigger(**job_config.trigger_config)
        elif job_config.trigger_type == TriggerType.DATE:
            run_date = datetime.fromisoformat(job_config.trigger_config['run_date'])
            trigger = DateTrigger(run_date=run_date)
        else:
            raise ValueError(f"Unsupported trigger type: {job_config.trigger_type}")
            
        self.scheduler.add_job(
            func=self._execute_job,
            trigger=trigger,
            id=job_config.id,
            args=[job_config.id],
            max_instances=job_config.max_instances,
            misfire_grace_time=job_config.misfire_grace_time,
            replace_existing=True
        )
        
    async def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler"""
        try:
            if job_id in self.jobs:
                del self.jobs[job_id]
                
            if job_id in self.executions:
                del self.executions[job_id]
                
            if self.scheduler:
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass  # Job might not exist in scheduler
                    
            await self._save_jobs()
            logger.info(f"Removed job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False
            
    async def pause_job(self, job_id: str) -> bool:
        """Pause a job"""
        try:
            if job_id in self.jobs:
                self.jobs[job_id].enabled = False
                
            if self.scheduler:
                self.scheduler.pause_job(job_id)
                
            logger.info(f"Paused job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False
            
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            if job_id in self.jobs:
                self.jobs[job_id].enabled = True
                
            if self.scheduler:
                self.scheduler.resume_job(job_id)
                
            logger.info(f"Resumed job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False
            
    async def run_job_now(self, job_id: str) -> bool:
        """Execute a job immediately"""
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return False
            
        try:
            await self._execute_job(job_id)
            return True
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            return False
            
    async def _execute_job(self, job_id: str):
        """Execute a job"""
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return
            
        job_config = self.jobs[job_id]
        
        if not job_config.enabled:
            logger.info(f"Job {job_id} is disabled, skipping execution")
            return
            
        execution_id = str(uuid.uuid4())
        execution = JobExecution(
            job_id=job_id,
            execution_id=execution_id,
            started_at=time.time(),
            status=JobStatus.RUNNING
        )
        
        self.executions[job_id].append(execution)
        
        logger.info(f"Executing job {job_id} ({job_config.name})")
        
        try:
            # Get the function
            func = self.job_functions[job_config.function]
            
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*job_config.args, **job_config.kwargs)
            else:
                result = func(*job_config.args, **job_config.kwargs)
                
            # Update execution record
            execution.finished_at = time.time()
            execution.duration = execution.finished_at - execution.started_at
            execution.status = JobStatus.COMPLETED
            execution.result = result
            
            logger.info(f"Job {job_id} completed successfully in {execution.duration:.2f}s")
            
        except Exception as e:
            execution.finished_at = time.time()
            execution.duration = execution.finished_at - execution.started_at
            execution.status = JobStatus.FAILED
            execution.error = str(e)
            
            logger.error(f"Job {job_id} failed: {e}")
            
        # Keep only last 100 executions per job
        if len(self.executions[job_id]) > 100:
            self.executions[job_id] = self.executions[job_id][-100:]
            
    async def _basic_scheduler_loop(self):
        """Basic scheduler loop for when APScheduler is not available"""
        logger.info("Starting basic scheduler loop")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                for job_id, job_config in self.jobs.items():
                    if not job_config.enabled:
                        continue
                        
                    # Check if job should run
                    should_run = False
                    
                    if job_config.trigger_type == TriggerType.INTERVAL:
                        # Simple interval checking
                        last_execution = self._get_last_execution(job_id)
                        if last_execution:
                            time_since_last = current_time.timestamp() - last_execution.started_at
                            interval_seconds = self._calculate_interval_seconds(job_config.trigger_config)
                            should_run = time_since_last >= interval_seconds
                        else:
                            should_run = True  # First execution
                            
                    elif job_config.trigger_type == TriggerType.IMMEDIATE:
                        should_run = True
                        job_config.trigger_type = TriggerType.DATE  # Convert to prevent re-execution
                        
                    if should_run:
                        asyncio.create_task(self._execute_job(job_id))
                        
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
                
    def _calculate_interval_seconds(self, trigger_config: Dict[str, Any]) -> int:
        """Calculate total seconds from interval configuration"""
        total_seconds = 0
        total_seconds += trigger_config.get('seconds', 0)
        total_seconds += trigger_config.get('minutes', 0) * 60
        total_seconds += trigger_config.get('hours', 0) * 3600
        total_seconds += trigger_config.get('days', 0) * 86400
        return total_seconds
        
    def _get_last_execution(self, job_id: str) -> Optional[JobExecution]:
        """Get the last execution record for a job"""
        executions = self.executions.get(job_id, [])
        return executions[-1] if executions else None
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and execution history"""
        if job_id not in self.jobs:
            return None
            
        job_config = self.jobs[job_id]
        executions = self.executions.get(job_id, [])
        last_execution = executions[-1] if executions else None
        
        return {
            'job_config': asdict(job_config),
            'total_executions': len(executions),
            'last_execution': asdict(last_execution) if last_execution else None,
            'recent_executions': [asdict(ex) for ex in executions[-10:]]
        }
        
    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all jobs with their status"""
        return {job_id: self.get_job_status(job_id) for job_id in self.jobs}
        
    async def _save_jobs(self):
        """Save jobs to persistent storage"""
        try:
            jobs_file = self.data_dir / "jobs.json"
            jobs_data = {
                'jobs': {
                    job_id: {
                        **asdict(job),
                        'trigger_type': job.trigger_type.value
                    } for job_id, job in self.jobs.items()
                },
                'executions': {
                    job_id: [
                        {
                            **asdict(ex),
                            'status': ex.status.value
                        } for ex in executions
                    ]
                    for job_id, executions in self.executions.items()
                }
            }
            
            with open(jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
            
    async def _load_jobs(self):
        """Load jobs from persistent storage"""
        try:
            jobs_file = self.data_dir / "jobs.json"
            if not jobs_file.exists():
                return
                
            with open(jobs_file, 'r') as f:
                jobs_data = json.load(f)
                
            # Load jobs
            for job_id, job_dict in jobs_data.get('jobs', {}).items():
                job_dict['trigger_type'] = TriggerType(job_dict['trigger_type'])
                self.jobs[job_id] = JobConfig(**job_dict)
                
                # Add to APScheduler if running
                if self.scheduler and self.running:
                    await self._add_apscheduler_job(self.jobs[job_id])
                    
            # Load executions
            for job_id, exec_list in jobs_data.get('executions', {}).items():
                self.executions[job_id] = [
                    JobExecution(**{**ex, 'status': JobStatus(ex['status'])})
                    for ex in exec_list
                ]
                
            logger.info(f"Loaded {len(self.jobs)} jobs from storage")
            
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")