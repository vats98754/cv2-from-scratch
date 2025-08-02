#!/usr/bin/env python3
"""
Browser Automation Platform Demo
Demonstrates key features of the platform
"""

import asyncio
import requests
import time
from datetime import datetime

def print_banner():
    """Print demo banner"""
    print("=" * 60)
    print("🚀 Browser Automation Platform Demo")
    print("=" * 60)
    print()

async def demo_llm_orchestration():
    """Demo natural language task orchestration"""
    print("📝 Natural Language Task Orchestration")
    print("-" * 40)
    
    # Example task descriptions
    examples = [
        "Create Twitter accounts every day at 9 AM",
        "Scrape product prices from Amazon every hour", 
        "Monitor system health every 5 minutes",
        "Create Instagram accounts twice a week and post content daily",
        "Check competitor websites every 4 hours and send alerts"
    ]
    
    # Import here to avoid startup issues
    try:
        from orchestration.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        
        for i, description in enumerate(examples, 1):
            print(f"\n{i}. Input: '{description}'")
            result = await orchestrator.orchestrate_from_text(description)
            
            if result.get('success'):
                plan = result['orchestration_plan']
                print(f"   📋 Generated {len(plan['execution_steps'])} steps")
                print(f"   ⏰ Created {len(plan['cron_jobs'])} scheduled jobs")
                print(f"   🔄 Background processes: {len(plan['background_processes'])}")
                
                # Show first cron job if any
                if plan['cron_jobs']:
                    job = plan['cron_jobs'][0]
                    print(f"   📅 Schedule: {job['cron_expression']} ({job['description']})")
            else:
                print(f"   ❌ Failed: {result.get('error')}")
        
        print("\n✅ LLM Orchestration demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

async def demo_scheduling():
    """Demo cron job scheduling"""
    print("\n⏰ Cron Job Scheduling Demo")
    print("-" * 40)
    
    try:
        from scheduler.cron_manager import CronManager
        
        cron_manager = CronManager()
        await cron_manager.start()
        
        # Schedule some example jobs
        jobs = [
            ("0 9 * * *", "account_create", {"platform": "twitter"}),
            ("*/15 * * * *", "health_check", {"checks": ["memory", "disk"]}),
            ("0 */2 * * *", "data_scrape", {"urls": ["https://example.com"]}),
            ("0 0 * * 0", "cleanup", {"pattern": "*.tmp"})
        ]
        
        for cron_expr, task_name, params in jobs:
            result = await cron_manager.schedule_job(cron_expr, task_name, params)
            if result.get('success'):
                print(f"✅ Scheduled {task_name}: {cron_expr}")
            else:
                print(f"❌ Failed to schedule {task_name}: {result.get('error')}")
        
        # Show status
        status = await cron_manager.get_status()
        print(f"\n📊 Status: {status['active_jobs']} active jobs, {status['total_jobs']} total")
        
        await cron_manager.stop()
        print("✅ Scheduling demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

async def demo_background_processes():
    """Demo background process management"""
    print("\n🔄 Background Process Management Demo")
    print("-" * 40)
    
    try:
        from scheduler.background_processor import BackgroundProcessor
        
        bg_processor = BackgroundProcessor()
        await bg_processor.start()
        
        # Start some example processes
        processes = [
            ("web_scraper", {"urls": ["https://example.com"], "interval": 300}),
            ("account_manager", {"platforms": ["twitter"], "check_interval": 600}),
            ("health_monitor", {"check_interval": 120})
        ]
        
        for name, params in processes:
            result = await bg_processor.start_web_scraper(params) if name == "web_scraper" else \
                     await bg_processor.start_account_manager(params) if name == "account_manager" else \
                     await bg_processor.start_health_monitor(params)
            
            if result:
                print(f"✅ Started {name} (Process ID: {result[:8]}...)")
            else:
                print(f"❌ Failed to start {name}")
        
        # Show status
        status = await bg_processor.get_status()
        print(f"\n📊 Status: {status['running_processes']} running, {status['total_processes']} total")
        
        await bg_processor.stop()
        print("✅ Background processes demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

async def demo_captcha_solver():
    """Demo CAPTCHA solving capabilities"""
    print("\n🔐 CAPTCHA Solving Demo")
    print("-" * 40)
    
    try:
        from automation.captcha_solver import CaptchaSolver
        
        solver = CaptchaSolver()
        
        # Demo different CAPTCHA types
        captcha_tests = [
            ("image", {"image_data": "mock_base64_image_data"}),
            ("recaptcha", {"site_key": "6Le-wvkSAAAAAPBMRTvw0Q4Muexq...", "page_url": "https://example.com"}),
            ("turnstile", {"site_key": "0x4AAAAAAADnPIDROrmt1Wkv", "page_url": "https://example.com"})
        ]
        
        for captcha_type, params in captcha_tests:
            result = await solver.solve(captcha_type=captcha_type, **params)
            if result.get('success'):
                print(f"✅ {captcha_type.upper()}: {result.get('message', 'Solved')}")
            else:
                print(f"❌ {captcha_type.upper()}: {result.get('error', 'Failed')}")
        
        print("✅ CAPTCHA solving demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

async def demo_account_creation():
    """Demo account creation (mock mode)"""
    print("\n👤 Account Creation Demo")
    print("-" * 40)
    
    try:
        from automation.account_creator import AccountCreator
        from automation.browser_manager import BrowserManager
        from automation.captcha_solver import CaptchaSolver
        
        # Create components (without actually initializing browser)
        browser_manager = BrowserManager()
        captcha_solver = CaptchaSolver()
        account_creator = AccountCreator(browser_manager, captcha_solver)
        
        # Demo account data generation
        platforms = ["twitter", "instagram", "facebook", "linkedin", "reddit"]
        
        for platform in platforms:
            # Generate account data
            account_data = account_creator._generate_missing_data({})
            print(f"✅ {platform.upper()}: Generated account data")
            print(f"   📧 Email: {account_data['email']}")
            print(f"   👤 Username: {account_data['username']}")
            print(f"   🔑 Password: {'*' * len(account_data['password'])}")
        
        print("✅ Account creation demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def demo_api_info():
    """Show API endpoint information"""
    print("\n🌐 API Endpoints")
    print("-" * 40)
    
    endpoints = [
        ("GET", "/", "Platform overview"),
        ("GET", "/health", "Health check"),
        ("GET", "/docs", "API documentation"),
        ("POST", "/browser/navigate", "Navigate browser"),
        ("POST", "/captcha/solve", "Solve CAPTCHA"),
        ("POST", "/account/create", "Create social account"),
        ("POST", "/jobs/schedule", "Schedule cron job"),
        ("POST", "/orchestrate", "LLM orchestration"),
        ("GET", "/jobs/status", "Job status"),
        ("GET", "/browser/status", "Browser status")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"  {method:4} {endpoint:20} - {description}")
    
    print("\n🚀 Start the server with: python main.py")
    print("📖 View docs at: http://localhost:8000/docs")

async def main():
    """Run all demos"""
    print_banner()
    
    # Run demos
    await demo_llm_orchestration()
    await demo_scheduling()
    await demo_background_processes()
    await demo_captcha_solver()
    await demo_account_creation()
    demo_api_info()
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed! The Browser Automation Platform is ready!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())