"""
Web Automation Platform
======================

A comprehensive platform for browser automation, social media automation, 
CAPTCHA bypassing, and task scheduling.

Core Features:
- Browser automation with Playwright
- Cloudflare and CAPTCHA bypassing
- Automated account creation
- Cron job scheduling
- Background process management
- LLM-based task orchestration
- Robust and deterministic automation
- High-performance async operations
"""

from .browser import BrowserManager, BrowserConfig
from .captcha import CaptchaSolver, CaptchaType, CaptchaTask
from .accounts import AccountCreator, Platform, PersonalInfo, DataGenerator
from .scheduler import JobScheduler, JobConfig, JobStatus, TriggerType
from .processes import ProcessManager, ProcessConfig, ProcessType, ProcessStatus
from .orchestrator import TaskOrchestrator, TaskDefinition, TaskType, WorkflowDefinition

__version__ = "1.0.0"
__all__ = [
    "BrowserManager", "BrowserConfig",
    "CaptchaSolver", "CaptchaType", "CaptchaTask",
    "AccountCreator", "Platform", "PersonalInfo", "DataGenerator",
    "JobScheduler", "JobConfig", "JobStatus", "TriggerType",
    "ProcessManager", "ProcessConfig", "ProcessType", "ProcessStatus",
    "TaskOrchestrator", "TaskDefinition", "TaskType", "WorkflowDefinition"
]