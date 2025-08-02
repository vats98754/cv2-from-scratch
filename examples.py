#!/usr/bin/env python3
"""
Example usage of the Web Automation Platform.
Demonstrates key features and capabilities.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from automation import (
    BrowserManager, BrowserConfig,
    CaptchaSolver,
    AccountCreator, Platform,
    JobScheduler,
    ProcessManager, ProcessConfig, ProcessType,
    TaskOrchestrator, TaskType
)

async def example_natural_language_automation():
    """Demonstrate natural language to automation workflow"""
    print("🤖 Natural Language Automation Example")
    print("=" * 50)
    
    # Initialize components
    job_scheduler = JobScheduler()
    await job_scheduler.start()
    
    task_orchestrator = TaskOrchestrator(job_scheduler=job_scheduler)
    
    # Example natural language inputs
    examples = [
        "Create 3 Twitter accounts every Monday at 9 AM",
        "Scrape news articles from example.com every hour",
        "Check all social media accounts every 30 minutes",
        "Create Instagram account and post daily content"
    ]
    
    for i, text in enumerate(examples, 1):
        print(f"\nExample {i}: '{text}'")
        
        # Parse natural language into tasks
        tasks = await task_orchestrator.parse_natural_language(text)
        
        if tasks:
            print(f"✅ Parsed into {len(tasks)} tasks:")
            for j, task in enumerate(tasks, 1):
                print(f"   {j}. {task.name}")
                print(f"      Type: {task.task_type.value}")
                print(f"      Schedule: {task.schedule or 'immediate'}")
                if task.parameters:
                    print(f"      Parameters: {task.parameters}")
        else:
            print("⚠️  No tasks could be parsed from this text")
    
    await job_scheduler.stop()

async def example_account_creation():
    """Demonstrate account creation system"""
    print("\n👤 Account Creation Example")
    print("=" * 50)
    
    # Initialize data generator
    from automation.accounts import DataGenerator
    generator = DataGenerator()
    
    # Generate sample account data
    platforms = [Platform.TWITTER, Platform.INSTAGRAM, Platform.REDDIT]
    
    for platform in platforms:
        print(f"\n📱 {platform.value.title()} Account Data:")
        personal_info = generator.generate_personal_info(platform)
        
        print(f"   Name: {personal_info.first_name} {personal_info.last_name}")
        print(f"   Email: {personal_info.email}")
        print(f"   Username: {personal_info.username}")
        print(f"   Bio: {personal_info.bio}")

async def example_job_scheduling():
    """Demonstrate job scheduling system"""
    print("\n⏰ Job Scheduling Example")
    print("=" * 50)
    
    job_scheduler = JobScheduler()
    await job_scheduler.start()
    
    # Register example functions
    async def daily_report():
        print("📊 Generating daily report...")
        return {"status": "completed", "reports": 5}
    
    def cleanup_logs():
        print("🧹 Cleaning up old logs...")
        return {"status": "completed", "files_cleaned": 100}
    
    job_scheduler.register_function("daily_report", daily_report)
    job_scheduler.register_function("cleanup_logs", cleanup_logs)
    
    # Add some example jobs
    jobs = [
        {
            "job_id": "daily_report_job",
            "name": "Daily Report Generation",
            "function": "daily_report", 
            "cron_expression": "0 9 * * *"  # 9 AM daily
        },
        {
            "job_id": "weekly_cleanup",
            "name": "Weekly Log Cleanup",
            "function": "cleanup_logs",
            "cron_expression": "0 3 * * 1"  # 3 AM every Monday
        }
    ]
    
    for job in jobs:
        success = await job_scheduler.add_cron_job(**job)
        if success:
            print(f"✅ Added job: {job['name']}")
        else:
            print(f"❌ Failed to add job: {job['name']}")
    
    # List all jobs
    all_jobs = job_scheduler.list_jobs()
    print(f"\n📋 Total jobs scheduled: {len(all_jobs)}")
    
    await job_scheduler.stop()

async def example_process_management():
    """Demonstrate process management system"""
    print("\n⚙️ Process Management Example")
    print("=" * 50)
    
    process_manager = ProcessManager()
    await process_manager.start()
    
    # Add example processes
    processes = [
        {
            "process_id": "web_server",
            "name": "Web Server",
            "command": "python -m http.server 8080",
            "process_type": "web_service",
            "auto_restart": True
        },
        {
            "process_id": "data_processor",
            "name": "Data Processing Worker",
            "command": "python data_worker.py",
            "process_type": "worker",
            "auto_restart": True
        }
    ]
    
    for proc_config in processes:
        config = ProcessConfig(
            id=proc_config["process_id"],
            name=proc_config["name"],
            command=proc_config["command"],
            type=ProcessType(proc_config["process_type"]),
            auto_restart=proc_config["auto_restart"]
        )
        
        success = await process_manager.add_process(config)
        if success:
            print(f"✅ Added process: {proc_config['name']}")
        else:
            print(f"❌ Failed to add process: {proc_config['name']}")
    
    # List all processes
    all_processes = process_manager.list_processes()
    print(f"\n📊 Total processes configured: {len(all_processes)}")
    
    for proc_id, proc_data in all_processes.items():
        config = proc_data['config']
        print(f"   {proc_id}: {config['name']} ({config['type']})")
    
    await process_manager.stop()

async def example_captcha_handling():
    """Demonstrate CAPTCHA solving capabilities"""
    print("\n🔐 CAPTCHA Solving Example")
    print("=" * 50)
    
    # Initialize CAPTCHA solver (without real API keys)
    captcha_solver = CaptchaSolver()
    
    # Example CAPTCHA scenarios
    scenarios = [
        {
            "type": "turnstile",
            "description": "Cloudflare Turnstile CAPTCHA",
            "site_key": "0x4AAAAAAADnPIDROzI0RTnA",
            "site_url": "https://example.com"
        },
        {
            "type": "recaptcha_v2", 
            "description": "Google reCAPTCHA v2",
            "site_key": "6LfD3PIbAAAAAJs_eEHvoOl75_83eXSqpPSRFJ_u",
            "site_url": "https://example.com"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🎯 {scenario['description']}")
        print(f"   Type: {scenario['type']}")
        print(f"   Site: {scenario['site_url']}")
        print(f"   Site Key: {scenario['site_key'][:20]}...")
        print("   Status: Ready to solve (API keys required)")

async def main():
    """Run all examples"""
    print("🚀 Web Automation Platform Examples")
    print("=" * 60)
    print("Demonstrating key features and capabilities...")
    
    try:
        await example_natural_language_automation()
        await example_account_creation()
        await example_job_scheduling()
        await example_process_management()
        await example_captcha_handling()
        
        print("\n" + "=" * 60)
        print("🎉 All examples completed successfully!")
        print("\nTo get started:")
        print("1. Install dependencies: pip install -r automation_requirements.txt")
        print("2. Start the server: python main.py")
        print("3. Visit http://localhost:8000/docs for API documentation")
        print("4. Try the natural language endpoint at /orchestrate")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())