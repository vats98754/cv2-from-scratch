"""
Browser Manager
Handles browser automation with robust and deterministic behavior
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
import random

logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser instances with robust automation features"""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize browser manager"""
        if self.is_initialized:
            return
            
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with stealth settings
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Can be made configurable
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # For speed
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            )
            
            self.is_initialized = True
            logger.info("Browser manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser manager: {e}")
            raise
    
    async def create_context(self, context_id: str = "default", **kwargs) -> BrowserContext:
        """Create a new browser context with stealth settings"""
        if not self.is_initialized:
            await self.initialize()
            
        # Default context settings for robustness
        context_settings = {
            'viewport': {'width': 1366, 'height': 768},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},  # New York
            'permissions': ['geolocation'],
            **kwargs
        }
        
        context = await self.browser.new_context(**context_settings)
        
        # Add stealth scripts
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        self.contexts[context_id] = context
        return context
    
    async def get_page(self, context_id: str = "default", page_id: str = "main") -> Page:
        """Get or create a page in the specified context"""
        if context_id not in self.contexts:
            await self.create_context(context_id)
            
        if page_id not in self.pages:
            context = self.contexts[context_id]
            page = await context.new_page()
            
            # Set up page for robustness
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            self.pages[page_id] = page
            
        return self.pages[page_id]
    
    async def navigate(self, url: str, page_id: str = "main", wait_until: str = "networkidle") -> Dict[str, Any]:
        """Navigate to URL with robust error handling"""
        try:
            page = await self.get_page(page_id=page_id)
            
            # Add random delay for more human-like behavior
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            response = await page.goto(url, wait_until=wait_until, timeout=30000)
            
            # Wait for page to be fully loaded
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            return {
                "success": True,
                "url": response.url,
                "status": response.status,
                "title": await page.title()
            }
            
        except Exception as e:
            logger.error(f"Navigation failed for {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def wait_for_element(self, selector: str, page_id: str = "main", timeout: int = 10000) -> bool:
        """Wait for element to be visible"""
        try:
            page = await self.get_page(page_id=page_id)
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Element not found {selector}: {e}")
            return False
    
    async def click_element(self, selector: str, page_id: str = "main", human_like: bool = True) -> bool:
        """Click element with human-like behavior"""
        try:
            page = await self.get_page(page_id=page_id)
            
            if human_like:
                # Add small random delay and mouse movement
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
            await page.click(selector)
            return True
            
        except Exception as e:
            logger.error(f"Click failed for {selector}: {e}")
            return False
    
    async def fill_input(self, selector: str, text: str, page_id: str = "main", human_like: bool = True) -> bool:
        """Fill input field with human-like typing"""
        try:
            page = await self.get_page(page_id=page_id)
            
            if human_like:
                # Type with random delays between characters
                await page.focus(selector)
                await page.fill(selector, "")  # Clear first
                
                for char in text:
                    await page.type(selector, char, delay=random.uniform(50, 150))
            else:
                await page.fill(selector, text)
                
            return True
            
        except Exception as e:
            logger.error(f"Fill input failed for {selector}: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get browser manager status"""
        return {
            "initialized": self.is_initialized,
            "browser_connected": self.browser is not None and self.browser.is_connected(),
            "active_contexts": len(self.contexts),
            "active_pages": len(self.pages)
        }
    
    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            # Close all pages
            for page in self.pages.values():
                await page.close()
            self.pages.clear()
            
            # Close all contexts
            for context in self.contexts.values():
                await context.close()
            self.contexts.clear()
            
            # Close browser
            if self.browser:
                await self.browser.close()
                
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
                
            self.is_initialized = False
            logger.info("Browser manager cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")