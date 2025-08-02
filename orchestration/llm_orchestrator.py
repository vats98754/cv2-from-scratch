"""
LLM Orchestrator
Converts natural language descriptions into orchestrated tasks and schedules
"""

import asyncio
import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    """Orchestrates tasks based on natural language input using LLM"""
    
    def __init__(self):
        self.api_key = None  # OpenAI API key
        self.model = "gpt-3.5-turbo"  # Default model
        self.task_patterns = self._build_task_patterns()
        self.schedule_patterns = self._build_schedule_patterns()
    
    def _build_task_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build patterns for recognizing different task types"""
        return {
            "account_creation": {
                "patterns": [
                    r"create\s+accounts?\s+on\s+(\w+)",
                    r"sign\s+up\s+(?:for|on)\s+(\w+)",
                    r"register\s+(?:for|on)\s+(\w+)",
                    r"make\s+accounts?\s+(?:for|on)\s+(\w+)"
                ],
                "task_type": "account_create",
                "extract_platforms": True
            },
            "web_scraping": {
                "patterns": [
                    r"scrape\s+data\s+from\s+(https?://[^\s]+)",
                    r"extract\s+(?:data|information)\s+from\s+(https?://[^\s]+)",
                    r"collect\s+data\s+from\s+(https?://[^\s]+)",
                    r"monitor\s+(https?://[^\s]+)"
                ],
                "task_type": "data_scrape",
                "extract_urls": True
            },
            "browser_automation": {
                "patterns": [
                    r"navigate\s+to\s+(https?://[^\s]+)",
                    r"visit\s+(https?://[^\s]+)",
                    r"open\s+(https?://[^\s]+)",
                    r"go\s+to\s+(https?://[^\s]+)"
                ],
                "task_type": "browser_navigate",
                "extract_urls": True
            },
            "monitoring": {
                "patterns": [
                    r"monitor\s+(?:the\s+)?system",
                    r"health\s+check",
                    r"keep\s+(?:an\s+)?eye\s+on",
                    r"watch\s+(?:for|the)"
                ],
                "task_type": "health_check",
                "extract_intervals": True
            },
            "cleanup": {
                "patterns": [
                    r"clean\s+up",
                    r"remove\s+(?:old|temporary)\s+files",
                    r"delete\s+(?:old|temp)\s+data",
                    r"maintenance"
                ],
                "task_type": "cleanup",
                "extract_patterns": True
            }
        }
    
    def _build_schedule_patterns(self) -> Dict[str, str]:
        """Build patterns for recognizing schedule expressions"""
        return {
            # Time-based patterns
            r"every\s+(\d+)\s+minutes?": "*/{}:*:*:*:*",
            r"every\s+(\d+)\s+hours?": "0:*/{}:*:*:*",
            r"every\s+(\d+)\s+days?": "0:0:*/{}:*:*",
            r"every\s+hour": "0:*:*:*:*",
            r"every\s+day": "0:0:*:*:*",
            r"every\s+week": "0:0:*:*:0",
            r"every\s+month": "0:0:1:*:*",
            
            # Specific time patterns
            r"at\s+(\d{1,2}):(\d{2})": "{}:{}:*:*:*",
            r"at\s+(\d{1,2})\s*(?:am|pm)": "{}:0:*:*:*",
            
            # Day-specific patterns
            r"every\s+monday": "0:0:*:*:1",
            r"every\s+tuesday": "0:0:*:*:2",
            r"every\s+wednesday": "0:0:*:*:3",
            r"every\s+thursday": "0:0:*:*:4",
            r"every\s+friday": "0:0:*:*:5",
            r"every\s+saturday": "0:0:*:*:6",
            r"every\s+sunday": "0:0:*:*:0",
            
            # Complex patterns
            r"twice\s+a\s+day": "0:0,12:*:*:*",
            r"three\s+times\s+a\s+day": "0:0,8,16:*:*:*",
            r"once\s+a\s+week": "0:0:*:*:1",
            r"daily": "0:0:*:*:*",
            r"weekly": "0:0:*:*:0",
            r"monthly": "0:0:1:*:*"
        }
    
    async def orchestrate_from_text(self, text_description: str) -> Dict[str, Any]:
        """
        Convert text description to orchestrated tasks and schedules
        
        Args:
            text_description: Natural language description of what to do
        """
        try:
            # Clean and prepare text
            text = text_description.lower().strip()
            
            # Extract tasks and schedules
            tasks = await self._extract_tasks(text)
            schedules = await self._extract_schedules(text)
            
            # If we have an API key, use LLM for more sophisticated parsing
            if self.api_key:
                llm_result = await self._llm_parse(text_description)
                if llm_result.get("success"):
                    # Merge LLM results with pattern-based results
                    tasks.extend(llm_result.get("tasks", []))
                    schedules.extend(llm_result.get("schedules", []))
            
            # Create orchestration plan
            orchestration_plan = await self._create_orchestration_plan(tasks, schedules, text)
            
            return {
                "success": True,
                "original_text": text_description,
                "extracted_tasks": tasks,
                "extracted_schedules": schedules,
                "orchestration_plan": orchestration_plan,
                "execution_summary": await self._generate_execution_summary(orchestration_plan)
            }
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _extract_tasks(self, text: str) -> List[Dict[str, Any]]:
        """Extract task information from text using patterns"""
        tasks = []
        
        for task_name, config in self.task_patterns.items():
            for pattern in config["patterns"]:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    task = {
                        "task_type": config["task_type"],
                        "category": task_name,
                        "matched_text": match.group(0),
                        "parameters": {}
                    }
                    
                    # Extract specific parameters based on task type
                    if config.get("extract_platforms"):
                        if match.groups():
                            task["parameters"]["platform"] = match.group(1)
                    
                    elif config.get("extract_urls"):
                        if match.groups():
                            task["parameters"]["url"] = match.group(1)
                    
                    elif config.get("extract_intervals"):
                        # Look for interval specifications
                        interval_match = re.search(r"every\s+(\d+)\s+(minute|hour|day)s?", text)
                        if interval_match:
                            amount = int(interval_match.group(1))
                            unit = interval_match.group(2)
                            
                            # Convert to seconds
                            multipliers = {"minute": 60, "hour": 3600, "day": 86400}
                            task["parameters"]["interval"] = amount * multipliers.get(unit, 3600)
                    
                    tasks.append(task)
        
        return tasks
    
    async def _extract_schedules(self, text: str) -> List[Dict[str, Any]]:
        """Extract schedule information from text"""
        schedules = []
        
        for pattern, cron_template in self.schedule_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                schedule = {
                    "matched_text": match.group(0),
                    "pattern": pattern,
                    "cron_expression": self._convert_to_cron(cron_template, match.groups())
                }
                schedules.append(schedule)
        
        return schedules
    
    def _convert_to_cron(self, template: str, groups: tuple) -> str:
        """Convert template to actual cron expression"""
        try:
            if groups:
                cron_expr = template.format(*groups)
            else:
                cron_expr = template
            
            # Convert our simplified format to standard cron
            # Our format: minute:hour:day:month:dayofweek
            # Standard cron: minute hour day month dayofweek
            
            parts = cron_expr.split(":")
            if len(parts) == 5:
                return " ".join(parts)
            else:
                return "0 * * * *"  # Default: every hour
                
        except Exception as e:
            logger.error(f"Cron conversion failed: {e}")
            return "0 * * * *"  # Default fallback
    
    async def _llm_parse(self, text: str) -> Dict[str, Any]:
        """Use LLM to parse more complex task descriptions"""
        try:
            # This would integrate with OpenAI API or similar
            # For now, return a mock response
            
            prompt = f"""
            Parse the following task description and extract:
            1. Tasks to be performed
            2. Schedule/timing information
            3. Parameters for each task
            
            Text: "{text}"
            
            Return JSON format:
            {{
                "tasks": [
                    {{
                        "task_type": "task_name",
                        "parameters": {{}},
                        "priority": 1
                    }}
                ],
                "schedules": [
                    {{
                        "cron_expression": "0 * * * *",
                        "description": "every hour"
                    }}
                ],
                "dependencies": [],
                "estimated_duration": "5 minutes"
            }}
            """
            
            # Simulate LLM API call
            await asyncio.sleep(1)
            
            # Mock response - in production this would be actual LLM response
            return {
                "success": True,
                "tasks": [],
                "schedules": [],
                "confidence": 0.8
            }
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_orchestration_plan(self, tasks: List[Dict[str, Any]], 
                                        schedules: List[Dict[str, Any]], 
                                        original_text: str) -> Dict[str, Any]:
        """Create a comprehensive orchestration plan"""
        plan = {
            "plan_id": f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "source_text": original_text,
            "total_tasks": len(tasks),
            "total_schedules": len(schedules),
            "execution_steps": [],
            "cron_jobs": [],
            "background_processes": [],
            "estimated_duration": "Unknown",
            "priority": "medium"
        }
        
        # Create execution steps
        step_counter = 1
        
        for task in tasks:
            step = {
                "step_id": step_counter,
                "task_type": task["task_type"],
                "parameters": task["parameters"],
                "category": task.get("category", "general"),
                "estimated_time": self._estimate_task_time(task["task_type"]),
                "dependencies": [],
                "retry_policy": {
                    "max_retries": 3,
                    "backoff_multiplier": 2
                }
            }
            
            plan["execution_steps"].append(step)
            step_counter += 1
        
        # Create cron jobs from schedules
        for i, schedule in enumerate(schedules):
            if tasks:  # Associate schedule with tasks
                for task in tasks:
                    cron_job = {
                        "job_id": f"cron_{i}_{task['task_type']}",
                        "cron_expression": schedule["cron_expression"],
                        "task_name": task["task_type"],
                        "task_params": task["parameters"],
                        "description": f"Scheduled {task['task_type']} - {schedule['matched_text']}"
                    }
                    plan["cron_jobs"].append(cron_job)
        
        # Identify background processes
        background_task_types = ["data_scrape", "health_check", "monitor"]
        for task in tasks:
            if task["task_type"] in background_task_types:
                bg_process = {
                    "process_name": f"bg_{task['task_type']}",
                    "target_function": task["task_type"],
                    "parameters": task["parameters"],
                    "restart_on_failure": True,
                    "health_check_interval": 300
                }
                plan["background_processes"].append(bg_process)
        
        return plan
    
    def _estimate_task_time(self, task_type: str) -> str:
        """Estimate time required for different task types"""
        time_estimates = {
            "account_create": "5-10 minutes",
            "browser_navigate": "30 seconds",
            "data_scrape": "2-5 minutes",
            "health_check": "30 seconds",
            "cleanup": "1-2 minutes"
        }
        return time_estimates.get(task_type, "1-3 minutes")
    
    async def _generate_execution_summary(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the execution plan"""
        return {
            "total_steps": len(plan["execution_steps"]),
            "total_cron_jobs": len(plan["cron_jobs"]),
            "total_background_processes": len(plan["background_processes"]),
            "task_breakdown": self._count_task_types(plan["execution_steps"]),
            "estimated_total_time": self._calculate_total_time(plan["execution_steps"]),
            "complexity_score": self._calculate_complexity(plan),
            "recommendations": self._generate_recommendations(plan)
        }
    
    def _count_task_types(self, steps: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count different types of tasks"""
        counts = {}
        for step in steps:
            task_type = step["task_type"]
            counts[task_type] = counts.get(task_type, 0) + 1
        return counts
    
    def _calculate_total_time(self, steps: List[Dict[str, Any]]) -> str:
        """Calculate estimated total execution time"""
        # Simplified calculation - in practice this would be more sophisticated
        total_minutes = len(steps) * 3  # Assume 3 minutes per step on average
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours} hours {minutes} minutes"
    
    def _calculate_complexity(self, plan: Dict[str, Any]) -> float:
        """Calculate complexity score for the plan"""
        # Simplified complexity calculation
        base_score = len(plan["execution_steps"]) * 0.1
        schedule_complexity = len(plan["cron_jobs"]) * 0.2
        background_complexity = len(plan["background_processes"]) * 0.3
        
        total_score = base_score + schedule_complexity + background_complexity
        return min(total_score, 10.0)  # Cap at 10
    
    def _generate_recommendations(self, plan: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the execution plan"""
        recommendations = []
        
        if len(plan["execution_steps"]) > 10:
            recommendations.append("Consider breaking down into smaller batches")
        
        if len(plan["background_processes"]) > 5:
            recommendations.append("Monitor resource usage with multiple background processes")
        
        if len(plan["cron_jobs"]) > 20:
            recommendations.append("Review job scheduling to avoid conflicts")
        
        # Check for potential conflicts
        task_types = [step["task_type"] for step in plan["execution_steps"]]
        if "account_create" in task_types and len([t for t in task_types if t == "account_create"]) > 5:
            recommendations.append("Add delays between account creations to avoid rate limits")
        
        if not recommendations:
            recommendations.append("Plan looks good for execution")
        
        return recommendations
    
    def configure_llm(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """Configure LLM integration"""
        self.api_key = api_key
        self.model = model
        logger.info(f"LLM configured with model: {model}")
    
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an orchestration plan"""
        try:
            execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            results = {
                "execution_id": execution_id,
                "plan_id": plan["plan_id"],
                "started_at": datetime.now().isoformat(),
                "status": "running",
                "completed_steps": 0,
                "total_steps": len(plan["execution_steps"]),
                "step_results": [],
                "errors": []
            }
            
            # Execute steps sequentially
            for step in plan["execution_steps"]:
                try:
                    step_result = await self._execute_step(step)
                    results["step_results"].append(step_result)
                    
                    if step_result.get("success"):
                        results["completed_steps"] += 1
                    else:
                        results["errors"].append(step_result.get("error"))
                        
                except Exception as e:
                    error_msg = f"Step {step['step_id']} failed: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            results["status"] = "completed"
            results["finished_at"] = datetime.now().isoformat()
            results["success_rate"] = results["completed_steps"] / results["total_steps"]
            
            return results
            
        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step"""
        try:
            # This would integrate with actual task execution systems
            # For now, simulate execution
            await asyncio.sleep(1)  # Simulate work
            
            return {
                "step_id": step["step_id"],
                "success": True,
                "message": f"Step {step['step_id']} completed successfully",
                "execution_time": "1 second"
            }
            
        except Exception as e:
            return {
                "step_id": step["step_id"],
                "success": False,
                "error": str(e)
            }