"""
Main application demonstrating the web automation platform.
Provides FastAPI endpoints for managing automation tasks.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    FastAPI = None
    HTTPException = None
    BaseModel = None

from automation import (
    BrowserManager, BrowserConfig,
    CaptchaSolver,
    AccountCreator, Platform,
    JobScheduler,
    ProcessManager, ProcessConfig, ProcessType,
    TaskOrchestrator
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global components
browser_manager = None
captcha_solver = None
account_creator = None
job_scheduler = None
process_manager = None
task_orchestrator = None

@asynccontextmanager
async def lifespan(app):
    """Application lifespan management"""
    global browser_manager, captcha_solver, account_creator
    global job_scheduler, process_manager, task_orchestrator
    
    logger.info("Starting automation platform...")
    
    try:
        # Initialize components
        browser_config = BrowserConfig(
            headless=True,
            stealth_mode=True,
            timeout=30000
        )
        browser_manager = BrowserManager(browser_config)
        
        # CAPTCHA solver with API keys from environment
        api_keys = {
            '2captcha': os.getenv('CAPTCHA_2CAPTCHA_API_KEY'),
            'anticaptcha': os.getenv('CAPTCHA_ANTICAPTCHA_API_KEY')
        }
        captcha_solver = CaptchaSolver(api_keys)
        
        # Account creator
        account_creator = AccountCreator(browser_manager, captcha_solver)
        
        # Job scheduler
        job_scheduler = JobScheduler()
        await job_scheduler.start()
        
        # Process manager
        process_manager = ProcessManager()
        await process_manager.start()
        
        # Task orchestrator
        task_orchestrator = TaskOrchestrator(
            job_scheduler=job_scheduler,
            browser_manager=browser_manager,
            account_creator=account_creator,
            captcha_solver=captcha_solver,
            process_manager=process_manager
        )
        
        # Register example functions
        await _register_example_functions()
        
        logger.info("Automation platform started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start automation platform: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down automation platform...")
        
        if job_scheduler:
            await job_scheduler.stop()
        if process_manager:
            await process_manager.stop()
        if browser_manager:
            await browser_manager.close()
            
        logger.info("Automation platform shutdown complete")

# Create FastAPI app if available
if FastAPI:
    app = FastAPI(
        title="Web Automation Platform",
        description="Comprehensive platform for browser automation, social media automation, and task scheduling",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Pydantic models for API
    class TaskRequest(BaseModel):
        text: str
        workflow_name: Optional[str] = None
        
    class AccountCreationRequest(BaseModel):
        platform: str
        count: int = 1
        
    class JobRequest(BaseModel):
        job_id: str
        name: str
        function: str
        cron_expression: str
        
    class ProcessRequest(BaseModel):
        process_id: str
        name: str
        command: str
        process_type: str = "background_job"
        auto_restart: bool = True
        
    # API Routes
    @app.get("/")
    async def root():
        """Root endpoint with platform information"""
        return {
            "platform": "Web Automation Platform",
            "version": "1.0.0",
            "status": "running",
            "features": [
                "Browser automation",
                "CAPTCHA solving",
                "Account creation",
                "Job scheduling",
                "Process management",
                "LLM task orchestration"
            ]
        }
        
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "components": {
                "browser_manager": browser_manager is not None,
                "captcha_solver": captcha_solver is not None,
                "account_creator": account_creator is not None,
                "job_scheduler": job_scheduler is not None and job_scheduler.running,
                "process_manager": process_manager is not None and process_manager.running,
                "task_orchestrator": task_orchestrator is not None
            }
        }
        
    # Task Orchestration Endpoints
    @app.post("/orchestrate")
    async def orchestrate_tasks(request: TaskRequest):
        """Create and schedule tasks from natural language description"""
        try:
            workflow = await task_orchestrator.create_workflow_from_text(
                request.text, 
                request.workflow_name
            )
            
            if not workflow:
                raise HTTPException(status_code=400, detail="Failed to parse tasks from text")
                
            # Schedule the workflow
            success = await task_orchestrator.schedule_workflow(workflow.workflow_id)
            
            return {
                "success": True,
                "workflow_id": workflow.workflow_id,
                "workflow_name": workflow.name,
                "tasks_count": len(workflow.tasks),
                "scheduled": success,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "name": task.name,
                        "type": task.task_type.value,
                        "schedule": task.schedule
                    }
                    for task in workflow.tasks
                ]
            }
            
        except Exception as e:
            logger.error(f"Task orchestration failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.get("/workflows")
    async def list_workflows():
        """List all workflows"""
        return task_orchestrator.list_workflows()
        
    @app.post("/workflows/{workflow_id}/execute")
    async def execute_workflow(workflow_id: str):
        """Execute a workflow immediately"""
        try:
            result = await task_orchestrator.execute_workflow(workflow_id)
            return result
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    # Account Creation Endpoints
    @app.post("/accounts/create")
    async def create_accounts(request: AccountCreationRequest):
        """Create social media accounts"""
        try:
            platform = Platform(request.platform.lower())
            
            if request.count == 1:
                result = await account_creator.create_account(platform)
                return {
                    "success": result.success,
                    "platform": result.platform.value,
                    "account_info": result.account_info.__dict__ if result.account_info else None,
                    "error": result.error_message,
                    "verification_required": result.verification_required
                }
            else:
                results = await account_creator.create_multiple_accounts(platform, request.count)
                return {
                    "success": True,
                    "total_requested": request.count,
                    "successful": sum(1 for r in results if r.success),
                    "results": [
                        {
                            "success": r.success,
                            "account_info": r.account_info.__dict__ if r.account_info else None,
                            "error": r.error_message
                        }
                        for r in results
                    ]
                }
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {request.platform}")
        except Exception as e:
            logger.error(f"Account creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    # Job Scheduling Endpoints
    @app.post("/jobs")
    async def add_job(request: JobRequest):
        """Add a scheduled job"""
        try:
            success = await job_scheduler.add_cron_job(
                job_id=request.job_id,
                name=request.name,
                function=request.function,
                cron_expression=request.cron_expression
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to add job")
                
            return {"success": True, "job_id": request.job_id}
            
        except Exception as e:
            logger.error(f"Job creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.get("/jobs")
    async def list_jobs():
        """List all scheduled jobs"""
        return job_scheduler.list_jobs()
        
    @app.post("/jobs/{job_id}/run")
    async def run_job(job_id: str):
        """Run a job immediately"""
        try:
            success = await job_scheduler.run_job_now(job_id)
            return {"success": success, "job_id": job_id}
        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.delete("/jobs/{job_id}")
    async def remove_job(job_id: str):
        """Remove a scheduled job"""
        try:
            success = await job_scheduler.remove_job(job_id)
            return {"success": success, "job_id": job_id}
        except Exception as e:
            logger.error(f"Job removal failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    # Process Management Endpoints
    @app.post("/processes")
    async def add_process(request: ProcessRequest):
        """Add a background process"""
        try:
            config = ProcessConfig(
                id=request.process_id,
                name=request.name,
                command=request.command,
                type=ProcessType(request.process_type),
                auto_restart=request.auto_restart
            )
            
            success = await process_manager.add_process(config)
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to add process")
                
            return {"success": True, "process_id": request.process_id}
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid process type: {request.process_type}")
        except Exception as e:
            logger.error(f"Process creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.get("/processes")
    async def list_processes():
        """List all processes"""
        return process_manager.list_processes()
        
    @app.post("/processes/{process_id}/start")
    async def start_process(process_id: str):
        """Start a process"""
        try:
            success = await process_manager.start_process(process_id)
            return {"success": success, "process_id": process_id}
        except Exception as e:
            logger.error(f"Process start failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.post("/processes/{process_id}/stop")
    async def stop_process(process_id: str):
        """Stop a process"""
        try:
            success = await process_manager.stop_process(process_id)
            return {"success": success, "process_id": process_id}
        except Exception as e:
            logger.error(f"Process stop failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @app.delete("/processes/{process_id}")
    async def remove_process(process_id: str):
        """Remove a process"""
        try:
            success = await process_manager.remove_process(process_id)
            return {"success": success, "process_id": process_id}
        except Exception as e:
            logger.error(f"Process removal failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    # CAPTCHA Endpoints
    @app.post("/captcha/solve")
    async def solve_captcha(
        captcha_type: str,
        site_key: Optional[str] = None,
        site_url: Optional[str] = None,
        service: Optional[str] = None
    ):
        """Solve a CAPTCHA"""
        try:
            if captcha_type == "turnstile":
                solution = await captcha_solver.solve_turnstile(site_key, site_url, service)
            elif captcha_type == "recaptcha_v2":
                solution = await captcha_solver.solve_recaptcha_v2(site_key, site_url, service)
            elif captcha_type == "recaptcha_v3":
                solution = await captcha_solver.solve_recaptcha_v3(site_key, site_url, service=service)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported CAPTCHA type: {captcha_type}")
                
            if solution:
                return {"success": True, "solution": solution}
            else:
                return {"success": False, "error": "Failed to solve CAPTCHA"}
                
        except Exception as e:
            logger.error(f"CAPTCHA solving failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def _register_example_functions():
    """Register example functions for job scheduling"""
    
    async def example_web_scraping():
        """Example web scraping function"""
        logger.info("Executing example web scraping task")
        # Implementation would go here
        return {"status": "completed", "data": "example_data"}
        
    async def example_account_maintenance():
        """Example account maintenance function"""
        logger.info("Executing account maintenance task")
        # Implementation would go here
        return {"status": "completed", "accounts_checked": 5}
        
    def example_data_processing():
        """Example data processing function"""
        logger.info("Executing data processing task")
        # Implementation would go here
        return {"status": "completed", "records_processed": 100}
        
    # Register functions with job scheduler
    job_scheduler.register_function("example_web_scraping", example_web_scraping)
    job_scheduler.register_function("example_account_maintenance", example_account_maintenance)
    job_scheduler.register_function("example_data_processing", example_data_processing)

def run_server():
    """Run the FastAPI server"""
    if not FastAPI:
        print("FastAPI not available. Install with: pip install fastapi uvicorn")
        return
        
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

async def run_cli():
    """Run CLI interface for testing"""
    print("🤖 Web Automation Platform CLI")
    print("=" * 40)
    
    # Initialize components
    browser_config = BrowserConfig(headless=True, stealth_mode=True)
    browser_manager = BrowserManager(browser_config)
    captcha_solver = CaptchaSolver()
    account_creator = AccountCreator(browser_manager, captcha_solver)
    job_scheduler = JobScheduler()
    process_manager = ProcessManager()
    
    await job_scheduler.start()
    await process_manager.start()
    
    task_orchestrator = TaskOrchestrator(
        job_scheduler=job_scheduler,
        browser_manager=browser_manager,
        account_creator=account_creator,
        captcha_solver=captcha_solver,
        process_manager=process_manager
    )
    
    try:
        while True:
            print("\nAvailable commands:")
            print("1. Create workflow from text")
            print("2. List workflows")
            print("3. Execute workflow")
            print("4. List jobs")
            print("5. List processes")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                text = input("Describe the automation task: ").strip()
                if text:
                    workflow = await task_orchestrator.create_workflow_from_text(text)
                    if workflow:
                        print(f"✅ Created workflow: {workflow.name}")
                        print(f"   Tasks: {len(workflow.tasks)}")
                        for task in workflow.tasks:
                            print(f"   - {task.name} ({task.task_type.value})")
                    else:
                        print("❌ Failed to create workflow")
                        
            elif choice == "2":
                workflows = task_orchestrator.list_workflows()
                if workflows:
                    print(f"\n📋 Found {len(workflows)} workflows:")
                    for wf_id, wf_data in workflows.items():
                        print(f"   {wf_id}: {wf_data['name']}")
                else:
                    print("No workflows found")
                    
            elif choice == "3":
                workflow_id = input("Enter workflow ID: ").strip()
                if workflow_id:
                    result = await task_orchestrator.execute_workflow(workflow_id)
                    print(f"Execution result: {result}")
                    
            elif choice == "4":
                jobs = job_scheduler.list_jobs()
                print(f"\n📅 Found {len(jobs)} jobs:")
                for job_id, job_data in jobs.items():
                    print(f"   {job_id}: {job_data['job_config']['name']}")
                    
            elif choice == "5":
                processes = process_manager.list_processes()
                print(f"\n⚙️ Found {len(processes)} processes:")
                for proc_id, proc_data in processes.items():
                    status = proc_data['status']
                    print(f"   {proc_id}: {proc_data['config']['name']} ({status})")
                    
            elif choice == "6":
                break
            else:
                print("Invalid choice")
                
    finally:
        await job_scheduler.stop()
        await process_manager.stop()
        await browser_manager.close()
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        asyncio.run(run_cli())
    else:
        run_server()