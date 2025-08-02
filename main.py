#!/usr/bin/env python3
"""
Browser Automation Platform
A comprehensive platform for browser automation, CAPTCHA bypassing, 
social media account creation, and task orchestration.
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

from automation.browser_manager import BrowserManager
from automation.captcha_solver import CaptchaSolver
from automation.account_creator import AccountCreator
from scheduler.cron_manager import CronManager
from scheduler.background_processor import BackgroundProcessor
from orchestration.llm_orchestrator import LLMOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for quick response times
app = FastAPI(
    title="Browser Automation Platform",
    description="Comprehensive browser automation with CAPTCHA bypassing and task orchestration",
    version="1.0.0"
)

# Global managers
browser_manager: BrowserManager = None
captcha_solver: CaptchaSolver = None
account_creator: AccountCreator = None
cron_manager: CronManager = None
background_processor: BackgroundProcessor = None
llm_orchestrator: LLMOrchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    global browser_manager, captcha_solver, account_creator, cron_manager, background_processor, llm_orchestrator
    
    logger.info("Starting Browser Automation Platform...")
    
    # Initialize components
    browser_manager = BrowserManager()
    captcha_solver = CaptchaSolver()
    account_creator = AccountCreator(browser_manager, captcha_solver)
    cron_manager = CronManager()
    background_processor = BackgroundProcessor()
    llm_orchestrator = LLMOrchestrator()
    
    # Start background services
    await background_processor.start()
    await cron_manager.start()
    
    logger.info("Browser Automation Platform started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Browser Automation Platform...")
    
    if background_processor:
        await background_processor.stop()
    if cron_manager:
        await cron_manager.stop()
    if browser_manager:
        await browser_manager.cleanup()
    
    logger.info("Browser Automation Platform stopped.")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with platform overview"""
    return """
    <html>
        <head><title>Browser Automation Platform</title></head>
        <body>
            <h1>Browser Automation Platform</h1>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/browser/status">Browser Status</a></li>
                <li><a href="/jobs/status">Job Status</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "browser_manager": browser_manager is not None,
            "captcha_solver": captcha_solver is not None,
            "account_creator": account_creator is not None,
            "cron_manager": cron_manager is not None,
            "background_processor": background_processor is not None,
            "llm_orchestrator": llm_orchestrator is not None
        }
    }

@app.get("/browser/status")
async def browser_status():
    """Get browser manager status"""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not initialized")
    
    return await browser_manager.get_status()

@app.post("/browser/navigate")
async def navigate_browser(url: str):
    """Navigate browser to URL"""
    if not browser_manager:
        raise HTTPException(status_code=503, detail="Browser manager not initialized")
    
    return await browser_manager.navigate(url)

@app.post("/captcha/solve")
async def solve_captcha(image_data: str = None, site_key: str = None, page_url: str = None):
    """Solve CAPTCHA (image or Cloudflare turnstile)"""
    if not captcha_solver:
        raise HTTPException(status_code=503, detail="CAPTCHA solver not initialized")
    
    return await captcha_solver.solve(image_data=image_data, site_key=site_key, page_url=page_url)

@app.post("/account/create")
async def create_account(platform: str, account_data: Dict[str, Any]):
    """Create account on social media platform"""
    if not account_creator:
        raise HTTPException(status_code=503, detail="Account creator not initialized")
    
    return await account_creator.create_account(platform, account_data)

@app.get("/jobs/status")
async def get_jobs_status():
    """Get status of all scheduled jobs"""
    if not cron_manager:
        raise HTTPException(status_code=503, detail="Cron manager not initialized")
    
    return await cron_manager.get_status()

@app.post("/jobs/schedule")
async def schedule_job(cron_expression: str, task_name: str, task_params: Dict[str, Any]):
    """Schedule a new cron job"""
    if not cron_manager:
        raise HTTPException(status_code=503, detail="Cron manager not initialized")
    
    return await cron_manager.schedule_job(cron_expression, task_name, task_params)

@app.post("/orchestrate")
async def orchestrate_from_text(text_description: str):
    """Convert text description to orchestrated tasks using LLM"""
    if not llm_orchestrator:
        raise HTTPException(status_code=503, detail="LLM orchestrator not initialized")
    
    return await llm_orchestrator.orchestrate_from_text(text_description)

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )