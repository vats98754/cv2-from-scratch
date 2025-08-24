"""
LLM-based task orchestration system.
Converts natural language descriptions into scheduled tasks and automation workflows.
"""

import asyncio
import json
import re
import time
import random
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks that can be orchestrated"""
    BROWSER_AUTOMATION = "browser_automation"
    ACCOUNT_CREATION = "account_creation"
    CAPTCHA_SOLVING = "captcha_solving"
    DATA_SCRAPING = "data_scraping"
    FORM_FILLING = "form_filling"
    FILE_PROCESSING = "file_processing"
    API_INTERACTION = "api_interaction"
    EMAIL_AUTOMATION = "email_automation"
    MONITORING = "monitoring"
    CUSTOM_SCRIPT = "custom_script"

@dataclass
class TaskDefinition:
    """Structured task definition"""
    task_id: str
    name: str
    task_type: TaskType
    description: str
    parameters: Dict[str, Any]
    schedule: Optional[str] = None  # Cron expression
    dependencies: List[str] = None  # Task IDs this depends on
    timeout: int = 3600  # seconds
    retries: int = 3
    enabled: bool = True

@dataclass
class WorkflowDefinition:
    """Workflow composed of multiple tasks"""
    workflow_id: str
    name: str
    description: str
    tasks: List[TaskDefinition]
    schedule: Optional[str] = None
    enabled: bool = True

class TaskOrchestrator:
    """
    LLM-powered task orchestration system.
    Converts natural language to structured automation tasks.
    """
    
    def __init__(self, job_scheduler=None, browser_manager=None, 
                 account_creator=None, captcha_solver=None, process_manager=None):
        self.job_scheduler = job_scheduler
        self.browser_manager = browser_manager
        self.account_creator = account_creator
        self.captcha_solver = captcha_solver
        self.process_manager = process_manager
        
        self.tasks: Dict[str, TaskDefinition] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.llm_client = None
        
        # Task templates for common patterns
        self.task_templates = {
            "social_media_account": {
                "task_type": TaskType.ACCOUNT_CREATION,
                "parameters": {
                    "platform": "twitter",
                    "verification_method": "email"
                }
            },
            "web_scraping": {
                "task_type": TaskType.DATA_SCRAPING,
                "parameters": {
                    "url": "",
                    "selectors": {},
                    "output_format": "json"
                }
            },
            "form_automation": {
                "task_type": TaskType.FORM_FILLING,
                "parameters": {
                    "url": "",
                    "form_data": {},
                    "submit": True
                }
            }
        }
        
    def set_llm_client(self, client):
        """Set the LLM client for natural language processing"""
        self.llm_client = client
        
    async def parse_natural_language(self, text: str) -> List[TaskDefinition]:
        """
        Parse natural language description into structured tasks.
        Uses LLM if available, otherwise falls back to pattern matching.
        """
        if self.llm_client:
            return await self._parse_with_llm(text)
        else:
            return await self._parse_with_patterns(text)
            
    async def _parse_with_llm(self, text: str) -> List[TaskDefinition]:
        """Parse using LLM"""
        try:
            # Prepare prompt for LLM
            prompt = self._create_parsing_prompt(text)
            
            # Call LLM (implementation depends on the specific LLM client)
            if hasattr(self.llm_client, 'chat'):
                # OpenAI-style client
                response = await self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                content = response.choices[0].message.content
                
            elif hasattr(self.llm_client, 'complete'):
                # Claude-style client
                response = await self.llm_client.complete(
                    prompt=f"{self._get_system_prompt()}\n\nUser: {prompt}\n\nAssistant:",
                    max_tokens=2000
                )
                content = response.completion
            else:
                raise ValueError("Unsupported LLM client")
                
            # Parse JSON response
            tasks_data = json.loads(content)
            
            # Convert to TaskDefinition objects
            tasks = []
            for i, task_data in enumerate(tasks_data.get('tasks', [])):
                task = TaskDefinition(
                    task_id=f"llm_task_{i}_{int(time.time())}",
                    name=task_data.get('name', f'Task {i+1}'),
                    task_type=TaskType(task_data.get('task_type')),
                    description=task_data.get('description', ''),
                    parameters=task_data.get('parameters', {}),
                    schedule=task_data.get('schedule'),
                    dependencies=task_data.get('dependencies', []),
                    timeout=task_data.get('timeout', 3600),
                    retries=task_data.get('retries', 3)
                )
                tasks.append(task)
                
            return tasks
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            # Fallback to pattern matching
            return await self._parse_with_patterns(text)
            
    async def _parse_with_patterns(self, text: str) -> List[TaskDefinition]:
        """Parse using regex patterns and keywords"""
        tasks = []
        text_lower = text.lower()
        
        # Pattern for account creation
        if any(keyword in text_lower for keyword in ['create account', 'sign up', 'register', 'create']) and \
           any(platform in text_lower for platform in ['twitter', 'instagram', 'facebook', 'reddit', 'discord']):
            platform = self._extract_platform(text_lower)
            if platform:
                # Extract count if specified
                count_match = re.search(r'(\d+)', text)
                count = int(count_match.group(1)) if count_match else 1
                
                task = TaskDefinition(
                    task_id=f"account_creation_{platform}_{int(time.time())}",
                    name=f"Create {count} {platform} account{'s' if count > 1 else ''}",
                    task_type=TaskType.ACCOUNT_CREATION,
                    description=f"Create {count} account{'s' if count > 1 else ''} on {platform}",
                    parameters={"platform": platform, "count": count}
                )
                tasks.append(task)
                
        # Pattern for web scraping
        scraping_patterns = ['scrape', 'extract data', 'collect information', 'get data from']
        url_pattern = r'https?://[^\s]+'
        
        if any(pattern in text_lower for pattern in scraping_patterns):
            urls = re.findall(url_pattern, text)
            if not urls and 'from' in text_lower:
                # Extract domain name if no full URL
                domain_match = re.search(r'from\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_lower)
                if domain_match:
                    urls = [f"https://{domain_match.group(1)}"]
                    
            for url in urls:
                task = TaskDefinition(
                    task_id=f"scraping_{hash(url)}_{int(time.time())}",
                    name=f"Scrape data from {url}",
                    task_type=TaskType.DATA_SCRAPING,
                    description=f"Extract data from {url}",
                    parameters={"url": url, "selectors": {}, "output_format": "json"}
                )
                tasks.append(task)
                
        # Pattern for monitoring/checking
        if any(keyword in text_lower for keyword in ['check', 'monitor', 'watch']):
            if any(platform in text_lower for platform in ['social media', 'accounts', 'twitter', 'instagram']):
                task = TaskDefinition(
                    task_id=f"monitoring_{int(time.time())}",
                    name="Monitor social media accounts",
                    task_type=TaskType.MONITORING,
                    description="Check social media accounts for updates",
                    parameters={"platforms": ["twitter", "instagram", "facebook"], "check_messages": True, "check_notifications": True}
                )
                tasks.append(task)
                
        # Pattern for scheduling
        schedule_patterns = {
            'every day': '0 9 * * *',
            'daily': '0 9 * * *',
            'every hour': '0 * * * *',
            'hourly': '0 * * * *',
            'every week': '0 9 * * 1',
            'weekly': '0 9 * * 1',
            'every monday': '0 9 * * 1',
            'every tuesday': '0 9 * * 2',
            'every wednesday': '0 9 * * 3',
            'every thursday': '0 9 * * 4',
            'every friday': '0 9 * * 5',
            'every 30 minutes': '*/30 * * * *',
            'every 15 minutes': '*/15 * * * *'
        }
        
        schedule = None
        for pattern, cron in schedule_patterns.items():
            if pattern in text_lower:
                schedule = cron
                break
                
        # Extract time if specified
        time_match = re.search(r'at (\d{1,2})\s*(?::|am|pm)', text_lower)
        if time_match and schedule:
            hour = int(time_match.group(1))
            if 'pm' in text_lower and hour != 12:
                hour += 12
            elif 'am' in text_lower and hour == 12:
                hour = 0
            # Replace hour in cron expression
            schedule_parts = schedule.split()
            if len(schedule_parts) >= 2:
                schedule_parts[1] = str(hour)
                schedule = ' '.join(schedule_parts)
                
        # Apply schedule to all tasks
        for task in tasks:
            if schedule:
                task.schedule = schedule
                
        return tasks
        
    def _extract_platform(self, text: str) -> Optional[str]:
        """Extract platform name from text"""
        platforms = {
            'twitter': ['twitter', 'x.com'],
            'instagram': ['instagram', 'insta'],
            'facebook': ['facebook', 'fb'],
            'reddit': ['reddit'],
            'discord': ['discord'],
            'linkedin': ['linkedin'],
            'youtube': ['youtube'],
            'tiktok': ['tiktok'],
            'gmail': ['gmail', 'google mail'],
            'outlook': ['outlook', 'hotmail']
        }
        
        for platform, keywords in platforms.items():
            if any(keyword in text for keyword in keywords):
                return platform
                
        return None
        
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are a task orchestration assistant. Your job is to convert natural language descriptions into structured automation tasks.

Available task types:
- browser_automation: Automate browser interactions
- account_creation: Create accounts on platforms
- captcha_solving: Solve CAPTCHAs
- data_scraping: Extract data from websites
- form_filling: Fill and submit forms
- file_processing: Process files
- api_interaction: Make API calls
- email_automation: Send/receive emails
- monitoring: Monitor websites/services
- custom_script: Run custom scripts

Response format (JSON):
{
  "tasks": [
    {
      "name": "Task name",
      "task_type": "task_type_enum",
      "description": "Task description",
      "parameters": {"key": "value"},
      "schedule": "cron_expression",
      "dependencies": ["task_id"],
      "timeout": 3600,
      "retries": 3
    }
  ]
}

Extract concrete, actionable tasks. Include appropriate parameters and scheduling information."""

    def _create_parsing_prompt(self, text: str) -> str:
        """Create parsing prompt for LLM"""
        return f"""Parse this automation request into structured tasks:

"{text}"

Please identify:
1. What specific actions need to be performed
2. What platforms/websites are involved
3. What data needs to be collected or processed
4. Any scheduling requirements
5. Dependencies between tasks

Return the structured task definitions."""

    async def create_workflow_from_text(self, text: str, workflow_name: str = None) -> Optional[WorkflowDefinition]:
        """Create a complete workflow from natural language description"""
        try:
            tasks = await self.parse_natural_language(text)
            
            if not tasks:
                logger.warning("No tasks could be parsed from text")
                return None
                
            workflow_id = f"workflow_{int(time.time())}"
            workflow = WorkflowDefinition(
                workflow_id=workflow_id,
                name=workflow_name or f"Workflow {workflow_id}",
                description=text,
                tasks=tasks
            )
            
            self.workflows[workflow_id] = workflow
            
            # Add tasks to task registry
            for task in tasks:
                self.tasks[task.task_id] = task
                
            logger.info(f"Created workflow {workflow_id} with {len(tasks)} tasks")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow from text: {e}")
            return None
            
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a single task"""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
            
        task = self.tasks[task_id]
        
        try:
            logger.info(f"Executing task: {task.name}")
            
            # Route to appropriate executor based on task type
            if task.task_type == TaskType.ACCOUNT_CREATION:
                return await self._execute_account_creation(task)
            elif task.task_type == TaskType.DATA_SCRAPING:
                return await self._execute_data_scraping(task)
            elif task.task_type == TaskType.BROWSER_AUTOMATION:
                return await self._execute_browser_automation(task)
            elif task.task_type == TaskType.FORM_FILLING:
                return await self._execute_form_filling(task)
            elif task.task_type == TaskType.CUSTOM_SCRIPT:
                return await self._execute_custom_script(task)
            else:
                return {"success": False, "error": f"Unsupported task type: {task.task_type}"}
                
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def _execute_account_creation(self, task: TaskDefinition) -> Dict[str, Any]:
        """Execute account creation task"""
        if not self.account_creator:
            return {"success": False, "error": "Account creator not available"}
            
        platform = task.parameters.get('platform')
        if not platform:
            return {"success": False, "error": "Platform not specified"}
            
        try:
            from .accounts import Platform
            platform_enum = Platform(platform.lower())
            result = await self.account_creator.create_account(platform_enum)
            
            return {
                "success": result.success,
                "account_info": asdict(result.account_info) if result.account_info else None,
                "error": result.error_message
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def _execute_data_scraping(self, task: TaskDefinition) -> Dict[str, Any]:
        """Execute data scraping task"""
        if not self.browser_manager:
            return {"success": False, "error": "Browser manager not available"}
            
        url = task.parameters.get('url')
        selectors = task.parameters.get('selectors', {})
        
        if not url:
            return {"success": False, "error": "URL not specified"}
            
        try:
            async with self.browser_manager as browser:
                context = await browser.create_context()
                page = await browser.new_page(context)
                
                await browser.navigate_with_retry(page, url)
                
                # Extract data using selectors
                data = {}
                for key, selector in selectors.items():
                    elements = await page.query_selector_all(selector)
                    data[key] = [await elem.text_content() for elem in elements]
                    
                # If no selectors provided, get page text
                if not selectors:
                    data['page_text'] = await page.text_content('body')
                    
                await context.close()
                
                return {"success": True, "data": data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def _execute_browser_automation(self, task: TaskDefinition) -> Dict[str, Any]:
        """Execute browser automation task"""
        # Implementation for general browser automation
        return {"success": False, "error": "Browser automation not implemented yet"}
        
    async def _execute_form_filling(self, task: TaskDefinition) -> Dict[str, Any]:
        """Execute form filling task"""
        # Implementation for form filling
        return {"success": False, "error": "Form filling not implemented yet"}
        
    async def _execute_custom_script(self, task: TaskDefinition) -> Dict[str, Any]:
        """Execute custom script task"""
        # Implementation for custom script execution
        return {"success": False, "error": "Custom script execution not implemented yet"}
        
    async def schedule_workflow(self, workflow_id: str) -> bool:
        """Schedule a workflow with the job scheduler"""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return False
            
        if not self.job_scheduler:
            logger.error("Job scheduler not available")
            return False
            
        workflow = self.workflows[workflow_id]
        
        try:
            # Register workflow execution function
            self.job_scheduler.register_function(f"execute_workflow_{workflow_id}", 
                                               lambda: self.execute_workflow(workflow_id))
            
            # Schedule workflow if it has a schedule
            if workflow.schedule:
                await self.job_scheduler.add_cron_job(
                    job_id=f"workflow_{workflow_id}",
                    name=workflow.name,
                    function=f"execute_workflow_{workflow_id}",
                    cron_expression=workflow.schedule
                )
                
            # Schedule individual tasks
            for task in workflow.tasks:
                if task.schedule:
                    # Register task execution function
                    self.job_scheduler.register_function(
                        f"execute_task_{task.task_id}",
                        lambda tid=task.task_id: self.execute_task(tid)
                    )
                    
                    await self.job_scheduler.add_cron_job(
                        job_id=f"task_{task.task_id}",
                        name=task.name,
                        function=f"execute_task_{task.task_id}",
                        cron_expression=task.schedule
                    )
                    
            logger.info(f"Scheduled workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule workflow {workflow_id}: {e}")
            return False
            
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a complete workflow"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
            
        workflow = self.workflows[workflow_id]
        results = {}
        
        try:
            logger.info(f"Executing workflow: {workflow.name}")
            
            # Execute tasks in order, respecting dependencies
            executed_tasks = set()
            
            for task in workflow.tasks:
                # Check dependencies
                if task.dependencies:
                    missing_deps = set(task.dependencies) - executed_tasks
                    if missing_deps:
                        results[task.task_id] = {
                            "success": False,
                            "error": f"Missing dependencies: {missing_deps}"
                        }
                        continue
                        
                # Execute task
                result = await self.execute_task(task.task_id)
                results[task.task_id] = result
                
                if result.get("success"):
                    executed_tasks.add(task.task_id)
                else:
                    logger.error(f"Task {task.task_id} failed: {result.get('error')}")
                    
            success_count = sum(1 for r in results.values() if r.get("success"))
            
            return {
                "success": success_count == len(workflow.tasks),
                "workflow_id": workflow_id,
                "total_tasks": len(workflow.tasks),
                "successful_tasks": success_count,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {"success": False, "error": str(e)}
            
    def list_workflows(self) -> Dict[str, Dict[str, Any]]:
        """List all workflows"""
        return {
            workflow_id: asdict(workflow)
            for workflow_id, workflow in self.workflows.items()
        }
        
    def list_tasks(self) -> Dict[str, Dict[str, Any]]:
        """List all tasks"""
        return {
            task_id: asdict(task)
            for task_id, task in self.tasks.items()
        }