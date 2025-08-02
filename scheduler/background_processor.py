"""
Background Processor
Handles long-running background processes similar to render.com
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid
import json

logger = logging.getLogger(__name__)

class BackgroundProcess:
    """Represents a background process"""
    
    def __init__(self, process_id: str, name: str, target_func: Callable, 
                 params: Dict[str, Any] = None, restart_on_failure: bool = True):
        self.process_id = process_id
        self.name = name
        self.target_func = target_func
        self.params = params or {}
        self.restart_on_failure = restart_on_failure
        self.status = "pending"  # pending, running, stopped, failed
        self.created_at = datetime.now()
        self.started_at = None
        self.stopped_at = None
        self.restart_count = 0
        self.error_count = 0
        self.last_error = None
        self.task = None
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert process to dictionary"""
        return {
            "process_id": self.process_id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "restart_count": self.restart_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "restart_on_failure": self.restart_on_failure
        }

class BackgroundProcessor:
    """Manages background processes"""
    
    def __init__(self):
        self.processes: Dict[str, BackgroundProcess] = {}
        self.is_running = False
        self.monitor_task = None
        self.monitor_interval = 30  # Check processes every 30 seconds
        
        # Register built-in processes
        self._register_builtin_processes()
    
    def _register_builtin_processes(self):
        """Register built-in background processes"""
        # These would be actual process implementations
        pass
    
    async def start(self):
        """Start the background processor"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Background processor started")
    
    async def stop(self):
        """Stop the background processor"""
        self.is_running = False
        
        # Stop all processes
        for process in self.processes.values():
            await self._stop_process(process)
        
        # Stop monitor
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Background processor stopped")
    
    async def _monitor_loop(self):
        """Monitor background processes"""
        while self.is_running:
            try:
                await self._check_processes()
                await asyncio.sleep(self.monitor_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)
    
    async def _check_processes(self):
        """Check status of all processes and restart if needed"""
        for process in list(self.processes.values()):
            try:
                # Check if process is still running
                if process.status == "running" and process.task:
                    if process.task.done():
                        # Process finished unexpectedly
                        try:
                            result = process.task.result()
                            logger.info(f"Process {process.process_id} completed normally")
                            process.status = "stopped"
                            process.stopped_at = datetime.now()
                        except Exception as e:
                            logger.error(f"Process {process.process_id} failed: {e}")
                            process.status = "failed"
                            process.stopped_at = datetime.now()
                            process.error_count += 1
                            process.last_error = str(e)
                            
                            # Restart if configured
                            if process.restart_on_failure:
                                await self._restart_process(process)
                
                # Perform health check
                await self._health_check_process(process)
                
            except Exception as e:
                logger.error(f"Error checking process {process.process_id}: {e}")
    
    async def _health_check_process(self, process: BackgroundProcess):
        """Perform health check on a process"""
        if process.status != "running":
            return
        
        now = datetime.now()
        if (process.last_health_check and 
            (now - process.last_health_check).total_seconds() < process.health_check_interval):
            return
        
        try:
            # Basic health check - process is running and responsive
            if process.task and not process.task.done():
                process.last_health_check = now
                logger.debug(f"Health check passed for process {process.process_id}")
            else:
                logger.warning(f"Health check failed for process {process.process_id}")
                
        except Exception as e:
            logger.error(f"Health check error for process {process.process_id}: {e}")
    
    async def start_process(self, name: str, target_func: Callable, 
                           params: Dict[str, Any] = None, 
                           restart_on_failure: bool = True) -> Dict[str, Any]:
        """Start a new background process"""
        try:
            process_id = str(uuid.uuid4())
            
            process = BackgroundProcess(
                process_id=process_id,
                name=name,
                target_func=target_func,
                params=params,
                restart_on_failure=restart_on_failure
            )
            
            self.processes[process_id] = process
            
            # Start the process
            await self._start_process(process)
            
            return {
                "success": True,
                "process_id": process_id,
                "message": f"Process {name} started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start process {name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _start_process(self, process: BackgroundProcess):
        """Start a specific process"""
        try:
            # Create and start the task
            if asyncio.iscoroutinefunction(process.target_func):
                process.task = asyncio.create_task(
                    process.target_func(process.params)
                )
            else:
                # Wrap sync function in async
                process.task = asyncio.create_task(
                    asyncio.get_event_loop().run_in_executor(
                        None, process.target_func, process.params
                    )
                )
            
            process.status = "running"
            process.started_at = datetime.now()
            process.last_health_check = datetime.now()
            
            logger.info(f"Started process {process.process_id}: {process.name}")
            
        except Exception as e:
            process.status = "failed"
            process.last_error = str(e)
            process.error_count += 1
            logger.error(f"Failed to start process {process.process_id}: {e}")
            raise
    
    async def _stop_process(self, process: BackgroundProcess):
        """Stop a specific process"""
        try:
            if process.task and not process.task.done():
                process.task.cancel()
                try:
                    await process.task
                except asyncio.CancelledError:
                    pass
            
            process.status = "stopped"
            process.stopped_at = datetime.now()
            logger.info(f"Stopped process {process.process_id}")
            
        except Exception as e:
            logger.error(f"Error stopping process {process.process_id}: {e}")
    
    async def _restart_process(self, process: BackgroundProcess):
        """Restart a process"""
        try:
            logger.info(f"Restarting process {process.process_id}")
            
            # Stop current task
            await self._stop_process(process)
            
            # Wait a bit before restart
            await asyncio.sleep(5)
            
            # Start again
            await self._start_process(process)
            process.restart_count += 1
            
            logger.info(f"Process {process.process_id} restarted (count: {process.restart_count})")
            
        except Exception as e:
            logger.error(f"Failed to restart process {process.process_id}: {e}")
            process.status = "failed"
            process.last_error = str(e)
    
    async def stop_process(self, process_id: str) -> Dict[str, Any]:
        """Stop a specific process"""
        if process_id not in self.processes:
            return {"success": False, "error": "Process not found"}
        
        process = self.processes[process_id]
        await self._stop_process(process)
        
        return {"success": True, "message": f"Process {process_id} stopped"}
    
    async def restart_process(self, process_id: str) -> Dict[str, Any]:
        """Restart a specific process"""
        if process_id not in self.processes:
            return {"success": False, "error": "Process not found"}
        
        process = self.processes[process_id]
        await self._restart_process(process)
        
        return {"success": True, "message": f"Process {process_id} restarted"}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all processes"""
        return {
            "is_running": self.is_running,
            "total_processes": len(self.processes),
            "running_processes": len([p for p in self.processes.values() if p.status == "running"]),
            "failed_processes": len([p for p in self.processes.values() if p.status == "failed"]),
            "processes": [process.to_dict() for process in self.processes.values()]
        }
    
    async def get_process_logs(self, process_id: str, lines: int = 100) -> Dict[str, Any]:
        """Get logs for a specific process"""
        if process_id not in self.processes:
            return {"success": False, "error": "Process not found"}
        
        # In a real implementation, this would fetch actual logs
        # For now, return mock logs
        return {
            "success": True,
            "process_id": process_id,
            "logs": [
                f"[{datetime.now().isoformat()}] Process started",
                f"[{datetime.now().isoformat()}] Process running normally",
                f"[{datetime.now().isoformat()}] Health check passed"
            ][-lines:]
        }
    
    # Built-in background processes
    async def start_web_scraper(self, params: Dict[str, Any]) -> str:
        """Start a web scraping background process"""
        async def scraper_func(params):
            """Web scraper background function"""
            urls = params.get("urls", [])
            interval = params.get("interval", 3600)  # 1 hour default
            
            while True:
                try:
                    for url in urls:
                        logger.info(f"Scraping {url}")
                        # Actual scraping logic would go here
                        await asyncio.sleep(10)  # Simulate scraping time
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Scraper error: {e}")
                    await asyncio.sleep(60)  # Wait before retry
        
        result = await self.start_process("web_scraper", scraper_func, params)
        return result.get("process_id")
    
    async def start_account_manager(self, params: Dict[str, Any]) -> str:
        """Start account management background process"""
        async def account_manager_func(params):
            """Account manager background function"""
            platforms = params.get("platforms", [])
            check_interval = params.get("check_interval", 1800)  # 30 minutes
            
            while True:
                try:
                    for platform in platforms:
                        logger.info(f"Checking accounts on {platform}")
                        # Account management logic would go here
                        await asyncio.sleep(5)
                    
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"Account manager error: {e}")
                    await asyncio.sleep(300)  # Wait before retry
        
        result = await self.start_process("account_manager", account_manager_func, params)
        return result.get("process_id")
    
    async def start_health_monitor(self, params: Dict[str, Any]) -> str:
        """Start system health monitoring process"""
        async def health_monitor_func(params):
            """Health monitor background function"""
            check_interval = params.get("check_interval", 300)  # 5 minutes
            
            while True:
                try:
                    # Check system health
                    logger.info("Performing system health check")
                    # Health check logic would go here
                    
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
                    await asyncio.sleep(60)
        
        result = await self.start_process("health_monitor", health_monitor_func, params)
        return result.get("process_id")