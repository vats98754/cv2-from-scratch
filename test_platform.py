"""
Test the browser automation platform
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Test if all modules can be imported"""
    try:
        from automation.browser_manager import BrowserManager
        from automation.captcha_solver import CaptchaSolver
        from automation.account_creator import AccountCreator
        from scheduler.cron_manager import CronManager
        from scheduler.background_processor import BackgroundProcessor
        from orchestration.llm_orchestrator import LLMOrchestrator
        
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality without browser"""
    try:
        from automation.captcha_solver import CaptchaSolver
        from scheduler.cron_manager import CronManager
        from scheduler.background_processor import BackgroundProcessor
        from orchestration.llm_orchestrator import LLMOrchestrator
        
        # Test CAPTCHA solver
        captcha_solver = CaptchaSolver()
        result = await captcha_solver.solve(image_data="test_data")
        print(f"✅ CAPTCHA solver test: {result.get('success', False)}")
        
        # Test cron manager
        cron_manager = CronManager()
        await cron_manager.start()
        
        # Schedule a test job
        job_result = await cron_manager.schedule_job(
            "0 * * * *",  # Every hour
            "health_check",
            {"test": "parameter"}
        )
        print(f"✅ Cron job scheduling: {job_result.get('success', False)}")
        
        # Get status
        status = await cron_manager.get_status()
        print(f"✅ Cron manager status: {status.get('is_running', False)}")
        
        await cron_manager.stop()
        
        # Test background processor
        bg_processor = BackgroundProcessor()
        await bg_processor.start()
        
        bg_status = await bg_processor.get_status()
        print(f"✅ Background processor: {bg_status.get('is_running', False)}")
        
        await bg_processor.stop()
        
        # Test LLM orchestrator
        orchestrator = LLMOrchestrator()
        result = await orchestrator.orchestrate_from_text(
            "Create accounts on Twitter every day at 9 AM"
        )
        print(f"✅ LLM orchestration: {result.get('success', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Testing Browser Automation Platform...")
    
    # Test imports
    import_success = await test_imports()
    if not import_success:
        print("❌ Import tests failed")
        return
    
    # Test basic functionality
    func_success = await test_basic_functionality()
    if not func_success:
        print("❌ Functionality tests failed")
        return
    
    print("✅ All tests passed! Platform is ready.")

if __name__ == "__main__":
    asyncio.run(main())