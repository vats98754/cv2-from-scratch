"""
Browser automation module with Playwright and Selenium support.
Provides stealth capabilities and anti-detection measures.
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    BrowserContext = None
    Page = None

try:
    from fake_useragent import UserAgent
    FAKE_USERAGENT_AVAILABLE = True
except ImportError:
    FAKE_USERAGENT_AVAILABLE = False
    UserAgent = None

try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    uc = None
    webdriver = None
import logging

logger = logging.getLogger(__name__)

@dataclass
class BrowserConfig:
    """Browser configuration settings"""
    headless: bool = True
    stealth_mode: bool = True
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    viewport: Dict[str, int] = None
    timeout: int = 30000
    retries: int = 3
    delay_range: tuple = (1, 3)

class BrowserManager:
    """
    Advanced browser automation manager with stealth capabilities.
    Supports both Playwright and Selenium with anti-detection measures.
    """
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        
        if FAKE_USERAGENT_AVAILABLE:
            self.ua = UserAgent()
        else:
            self.ua = None
            
        self.playwright = None
        self.browser = None
        self.contexts: List = []
        self.selenium_driver = None
        
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available. Browser automation features will be limited.")
        if not SELENIUM_AVAILABLE:
            logger.warning("Selenium not available. Legacy browser support will be unavailable.")
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start(self):
        """Initialize the browser automation system"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available. Install with: pip install playwright")
            
        try:
            self.playwright = await async_playwright().start()
            
            # Configure browser options
            browser_args = [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
            
            if self.config.stealth_mode:
                browser_args.extend([
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor'
                ])
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                args=browser_args
            )
            
            logger.info("Browser automation system started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
            
    async def create_context(self, **kwargs):
        """Create a new browser context with stealth settings"""
        if not self.browser:
            await self.start()
            
        context_options = {
            'viewport': self.config.viewport or {'width': 1920, 'height': 1080},
            'user_agent': self.config.user_agent or (self.ua.random if self.ua else 'Mozilla/5.0 (compatible)'),
            'locale': 'en-US',
            'timezone_id': 'America/New_York'
        }
        
        if self.config.proxy:
            context_options['proxy'] = {'server': self.config.proxy}
            
        context_options.update(kwargs)
        
        context = await self.browser.new_context(**context_options)
        
        # Add stealth scripts
        if self.config.stealth_mode:
            await self._apply_stealth_mode(context)
            
        self.contexts.append(context)
        return context
        
    async def _apply_stealth_mode(self, context):
        """Apply stealth mode scripts to avoid detection"""
        stealth_script = """
        // Override webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override chrome property
        window.chrome = {
            runtime: {},
        };
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Override plugins length
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        """
        
        await context.add_init_script(stealth_script)
        
    async def new_page(self, context = None):
        """Create a new page with robust error handling"""
        if not context:
            context = await self.create_context()
            
        page = await context.new_page()
        
        # Set default timeout
        page.set_default_timeout(self.config.timeout)
        
        # Add page-level error handling
        page.on("pageerror", lambda exc: logger.error(f"Page error: {exc}"))
        page.on("crash", lambda: logger.error("Page crashed"))
        
        return page
        
    async def navigate_with_retry(self, page, url: str, **kwargs) -> bool:
        """Navigate to URL with retry logic and anti-detection delays"""
        for attempt in range(self.config.retries):
            try:
                # Random delay to avoid detection
                await asyncio.sleep(random.uniform(*self.config.delay_range))
                
                await page.goto(url, wait_until='domcontentloaded', **kwargs)
                
                # Verify page loaded successfully
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                logger.info(f"Successfully navigated to {url}")
                return True
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    
        logger.error(f"Failed to navigate to {url} after {self.config.retries} attempts")
        return False
        
    async def wait_for_element(self, page, selector: str, timeout: int = None) -> bool:
        """Wait for element with robust error handling"""
        try:
            await page.wait_for_selector(
                selector, 
                timeout=timeout or self.config.timeout
            )
            return True
        except Exception as e:
            logger.error(f"Element not found: {selector} - {e}")
            return False
            
    async def type_human_like(self, page, selector: str, text: str):
        """Type text with human-like delays"""
        element = await page.wait_for_selector(selector)
        await element.click()
        
        for char in text:
            await element.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))
            
    async def close(self):
        """Clean up browser resources"""
        try:
            for context in self.contexts:
                await context.close()
            
            if self.browser:
                await self.browser.close()
                
            if self.playwright:
                await self.playwright.stop()
                
            if self.selenium_driver:
                self.selenium_driver.quit()
                
            logger.info("Browser resources cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    def create_selenium_driver(self, **kwargs):
        """Create undetected Chrome driver for legacy support"""
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium not available. Install with: pip install selenium undetected-chromedriver")
            
        options = uc.ChromeOptions()
        
        if self.config.headless:
            options.add_argument('--headless')
            
        if self.config.stealth_mode:
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
        if self.config.user_agent:
            options.add_argument(f'--user-agent={self.config.user_agent}')
            
        self.selenium_driver = uc.Chrome(options=options, **kwargs)
        
        if self.config.stealth_mode:
            self.selenium_driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
        return self.selenium_driver