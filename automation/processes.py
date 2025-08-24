"""
Background process management system similar to render.com.
Handles process lifecycle, monitoring, and health checks.
"""

import asyncio
import os
import signal
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
import json
import time
import subprocess
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProcessStatus(Enum):
    """Process status"""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    CRASHED = "crashed"

class ProcessType(Enum):
    """Process types"""
    WEB_SERVICE = "web_service"
    BACKGROUND_JOB = "background_job"
    CRON_JOB = "cron_job"
    WORKER = "worker"
    DAEMON = "daemon"

@dataclass
class ProcessConfig:
    """Process configuration"""
    id: str
    name: str
    command: str
    type: ProcessType
    working_dir: Optional[str] = None
    environment: Dict[str, str] = None
    auto_restart: bool = True
    max_restarts: int = 3
    restart_delay: int = 5
    health_check_url: Optional[str] = None
    health_check_interval: int = 30
    memory_limit: Optional[int] = None  # MB
    cpu_limit: Optional[float] = None   # percentage
    port: Optional[int] = None
    enabled: bool = True

@dataclass
class ProcessInfo:
    """Process runtime information"""
    config: ProcessConfig
    status: ProcessStatus
    pid: Optional[int] = None
    started_at: Optional[float] = None
    stopped_at: Optional[float] = None
    restart_count: int = 0
    last_restart_at: Optional[float] = None
    memory_usage: Optional[float] = None  # MB
    cpu_usage: Optional[float] = None     # percentage
    uptime: Optional[float] = None        # seconds
    health_status: Optional[str] = None

class ProcessManager:
    """
    Background process management system.
    Provides process lifecycle management, monitoring, and health checks.
    """
    
    def __init__(self, data_dir: str = "/tmp/processes"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.processes: Dict[str, ProcessInfo] = {}
        self.health_checkers: Dict[str, asyncio.Task] = {}
        self.monitors: Dict[str, asyncio.Task] = {}
        self.running = False
        
    async def start(self):
        """Start the process manager"""
        self.running = True
        await self._load_processes()
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_loop())
        asyncio.create_task(self._health_check_loop())
        
        logger.info("Process manager started")
        
    async def stop(self):
        """Stop the process manager"""
        self.running = False
        
        # Stop all processes
        for process_id in list(self.processes.keys()):
            await self.stop_process(process_id)
            
        # Cancel monitoring tasks
        for task in self.health_checkers.values():
            task.cancel()
        for task in self.monitors.values():
            task.cancel()
            
        await self._save_processes()
        logger.info("Process manager stopped")
        
    async def add_process(self, config: ProcessConfig) -> bool:
        """Add a new process configuration"""
        try:
            process_info = ProcessInfo(
                config=config,
                status=ProcessStatus.STOPPED
            )
            
            self.processes[config.id] = process_info
            await self._save_processes()
            
            logger.info(f"Added process: {config.id} ({config.name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add process {config.id}: {e}")
            return False
            
    async def remove_process(self, process_id: str) -> bool:
        """Remove a process"""
        try:
            if process_id in self.processes:
                # Stop the process first
                await self.stop_process(process_id)
                
                # Remove from tracking
                del self.processes[process_id]
                
                # Cancel monitoring tasks
                if process_id in self.health_checkers:
                    self.health_checkers[process_id].cancel()
                    del self.health_checkers[process_id]
                    
                if process_id in self.monitors:
                    self.monitors[process_id].cancel()
                    del self.monitors[process_id]
                    
                await self._save_processes()
                logger.info(f"Removed process: {process_id}")
                return True
            else:
                logger.warning(f"Process {process_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove process {process_id}: {e}")
            return False
            
    async def start_process(self, process_id: str) -> bool:
        """Start a process"""
        if process_id not in self.processes:
            logger.error(f"Process {process_id} not found")
            return False
            
        process_info = self.processes[process_id]
        
        if not process_info.config.enabled:
            logger.info(f"Process {process_id} is disabled")
            return False
            
        if process_info.status == ProcessStatus.RUNNING:
            logger.info(f"Process {process_id} is already running")
            return True
            
        try:
            logger.info(f"Starting process: {process_id}")
            process_info.status = ProcessStatus.STARTING
            
            # Prepare environment
            env = os.environ.copy()
            if process_info.config.environment:
                env.update(process_info.config.environment)
                
            # Start the process
            process = await asyncio.create_subprocess_shell(
                process_info.config.command,
                cwd=process_info.config.working_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            process_info.pid = process.pid
            process_info.started_at = time.time()
            process_info.status = ProcessStatus.RUNNING
            process_info.restart_count = 0
            
            # Start monitoring
            self.monitors[process_id] = asyncio.create_task(
                self._monitor_process(process_id, process)
            )
            
            # Start health checking if configured
            if process_info.config.health_check_url:
                self.health_checkers[process_id] = asyncio.create_task(
                    self._health_check_process(process_id)
                )
                
            logger.info(f"Process {process_id} started with PID {process.pid}")
            return True
            
        except Exception as e:
            process_info.status = ProcessStatus.FAILED
            logger.error(f"Failed to start process {process_id}: {e}")
            return False
            
    async def stop_process(self, process_id: str) -> bool:
        """Stop a process"""
        if process_id not in self.processes:
            logger.error(f"Process {process_id} not found")
            return False
            
        process_info = self.processes[process_id]
        
        if process_info.status != ProcessStatus.RUNNING:
            logger.info(f"Process {process_id} is not running")
            return True
            
        try:
            logger.info(f"Stopping process: {process_id}")
            process_info.status = ProcessStatus.STOPPING
            
            if process_info.pid:
                # Try graceful shutdown first
                try:
                    os.killpg(os.getpgid(process_info.pid), signal.SIGTERM)
                    
                    # Wait for graceful shutdown
                    for _ in range(10):  # 10 seconds
                        if not psutil.pid_exists(process_info.pid):
                            break
                        await asyncio.sleep(1)
                    else:
                        # Force kill if still running
                        logger.warning(f"Force killing process {process_id}")
                        os.killpg(os.getpgid(process_info.pid), signal.SIGKILL)
                        
                except ProcessLookupError:
                    pass  # Process already dead
                    
            process_info.status = ProcessStatus.STOPPED
            process_info.stopped_at = time.time()
            process_info.pid = None
            
            # Cancel monitoring tasks
            if process_id in self.monitors:
                self.monitors[process_id].cancel()
                del self.monitors[process_id]
                
            if process_id in self.health_checkers:
                self.health_checkers[process_id].cancel()
                del self.health_checkers[process_id]
                
            logger.info(f"Process {process_id} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop process {process_id}: {e}")
            return False
            
    async def restart_process(self, process_id: str) -> bool:
        """Restart a process"""
        logger.info(f"Restarting process: {process_id}")
        
        if await self.stop_process(process_id):
            await asyncio.sleep(2)  # Brief delay
            return await self.start_process(process_id)
        return False
        
    async def _monitor_process(self, process_id: str, process: asyncio.subprocess.Process):
        """Monitor a process for crashes and handle restarts"""
        process_info = self.processes[process_id]
        
        try:
            # Wait for process to finish
            await process.wait()
            
            # Process has exited
            if process_info.status == ProcessStatus.STOPPING:
                # Expected shutdown
                return
                
            # Unexpected exit
            logger.warning(f"Process {process_id} exited unexpectedly (code: {process.returncode})")
            process_info.status = ProcessStatus.CRASHED
            
            # Handle auto-restart
            if (process_info.config.auto_restart and 
                process_info.restart_count < process_info.config.max_restarts):
                
                process_info.restart_count += 1
                process_info.last_restart_at = time.time()
                
                logger.info(f"Auto-restarting process {process_id} (attempt {process_info.restart_count})")
                
                await asyncio.sleep(process_info.config.restart_delay)
                await self.start_process(process_id)
            else:
                logger.error(f"Process {process_id} exceeded max restarts or auto-restart disabled")
                process_info.status = ProcessStatus.FAILED
                
        except Exception as e:
            logger.error(f"Error monitoring process {process_id}: {e}")
            
    async def _health_check_process(self, process_id: str):
        """Perform health checks on a process"""
        process_info = self.processes[process_id]
        
        try:
            import aiohttp
            
            while self.running and process_info.status == ProcessStatus.RUNNING:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                        async with session.get(process_info.config.health_check_url) as response:
                            if response.status == 200:
                                process_info.health_status = "healthy"
                            else:
                                process_info.health_status = f"unhealthy (status: {response.status})"
                                logger.warning(f"Health check failed for {process_id}: {response.status}")
                                
                except Exception as e:
                    process_info.health_status = f"unhealthy (error: {str(e)})"
                    logger.warning(f"Health check error for {process_id}: {e}")
                    
                await asyncio.sleep(process_info.config.health_check_interval)
                
        except ImportError:
            logger.warning("aiohttp not available, skipping health checks")
        except Exception as e:
            logger.error(f"Health check error for {process_id}: {e}")
            
    async def _monitor_loop(self):
        """Main monitoring loop for resource usage"""
        while self.running:
            try:
                for process_id, process_info in self.processes.items():
                    if process_info.status == ProcessStatus.RUNNING and process_info.pid:
                        try:
                            proc = psutil.Process(process_info.pid)
                            
                            # Update resource usage
                            process_info.memory_usage = proc.memory_info().rss / 1024 / 1024  # MB
                            process_info.cpu_usage = proc.cpu_percent()
                            process_info.uptime = time.time() - process_info.started_at
                            
                            # Check resource limits
                            if (process_info.config.memory_limit and 
                                process_info.memory_usage > process_info.config.memory_limit):
                                logger.warning(f"Process {process_id} exceeds memory limit")
                                
                            if (process_info.config.cpu_limit and 
                                process_info.cpu_usage > process_info.config.cpu_limit):
                                logger.warning(f"Process {process_id} exceeds CPU limit")
                                
                        except psutil.NoSuchProcess:
                            # Process no longer exists
                            process_info.status = ProcessStatus.CRASHED
                            process_info.pid = None
                            
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
                
    async def _health_check_loop(self):
        """Health check coordination loop"""
        while self.running:
            try:
                # This could coordinate health checks across processes
                # or perform system-level health checks
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)
                
    def get_process_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Get process status and metrics"""
        if process_id not in self.processes:
            return None
            
        process_info = self.processes[process_id]
        return asdict(process_info)
        
    def list_processes(self) -> Dict[str, Dict[str, Any]]:
        """List all processes with their status"""
        return {
            process_id: self.get_process_status(process_id)
            for process_id in self.processes
        }
        
    async def start_all_enabled(self):
        """Start all enabled processes"""
        for process_id, process_info in self.processes.items():
            if process_info.config.enabled and process_info.status != ProcessStatus.RUNNING:
                await self.start_process(process_id)
                await asyncio.sleep(1)  # Brief delay between starts
                
    async def stop_all(self):
        """Stop all running processes"""
        for process_id, process_info in self.processes.items():
            if process_info.status == ProcessStatus.RUNNING:
                await self.stop_process(process_id)
                
    async def _save_processes(self):
        """Save process configurations to disk"""
        try:
            processes_file = self.data_dir / "processes.json"
            processes_data = {
                process_id: {
                    'config': {
                        **asdict(process_info.config),
                        'type': process_info.config.type.value
                    },
                    'status': process_info.status.value,
                    'restart_count': process_info.restart_count
                }
                for process_id, process_info in self.processes.items()
            }
            
            with open(processes_file, 'w') as f:
                json.dump(processes_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save processes: {e}")
            
    async def _load_processes(self):
        """Load process configurations from disk"""
        try:
            processes_file = self.data_dir / "processes.json"
            if not processes_file.exists():
                return
                
            with open(processes_file, 'r') as f:
                processes_data = json.load(f)
                
            for process_id, data in processes_data.items():
                # Reconstruct config
                config_data = data['config']
                config_data['type'] = ProcessType(config_data['type'])
                config = ProcessConfig(**config_data)
                
                # Create process info
                process_info = ProcessInfo(
                    config=config,
                    status=ProcessStatus.STOPPED,  # Always start as stopped
                    restart_count=data.get('restart_count', 0)
                )
                
                self.processes[process_id] = process_info
                
            logger.info(f"Loaded {len(self.processes)} process configurations")
            
        except Exception as e:
            logger.error(f"Failed to load processes: {e}")
            
    # Convenience methods for common process types
    async def add_web_service(self, process_id: str, name: str, command: str, 
                            port: int, health_check_path: str = "/health", **kwargs) -> bool:
        """Add a web service process"""
        config = ProcessConfig(
            id=process_id,
            name=name,
            command=command,
            type=ProcessType.WEB_SERVICE,
            port=port,
            health_check_url=f"http://localhost:{port}{health_check_path}",
            **kwargs
        )
        return await self.add_process(config)
        
    async def add_background_job(self, process_id: str, name: str, command: str, **kwargs) -> bool:
        """Add a background job process"""
        config = ProcessConfig(
            id=process_id,
            name=name,
            command=command,
            type=ProcessType.BACKGROUND_JOB,
            **kwargs
        )
        return await self.add_process(config)
        
    async def add_worker(self, process_id: str, name: str, command: str, **kwargs) -> bool:
        """Add a worker process"""
        config = ProcessConfig(
            id=process_id,
            name=name,
            command=command,
            type=ProcessType.WORKER,
            **kwargs
        )
        return await self.add_process(config)