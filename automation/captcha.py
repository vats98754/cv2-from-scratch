"""
CAPTCHA and Cloudflare Turnstile bypassing module.
Supports multiple CAPTCHA solving services and anti-bot detection.
"""

import asyncio
import base64
import io
import time
from typing import Dict, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import requests
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
import logging

logger = logging.getLogger(__name__)

class CaptchaType(Enum):
    """Supported CAPTCHA types"""
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    IMAGE = "image"
    TEXT = "text"
    FUNCAPTCHA = "funcaptcha"

@dataclass
class CaptchaTask:
    """CAPTCHA task configuration"""
    captcha_type: CaptchaType
    site_key: Optional[str] = None
    site_url: Optional[str] = None
    image_data: Optional[bytes] = None
    instruction: Optional[str] = None
    min_score: Optional[float] = None
    action: Optional[str] = None
    proxy: Optional[str] = None

class CaptchaSolver:
    """
    Multi-service CAPTCHA solver with support for major providers.
    Includes Cloudflare Turnstile and anti-bot detection bypass.
    """
    
    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        self.services = {
            '2captcha': self._solve_2captcha,
            'anticaptcha': self._solve_anticaptcha,
            'capsolver': self._solve_capsolver,
            'manual': self._solve_manual
        }
        self.default_service = '2captcha'
        
    async def solve(self, task: CaptchaTask, service: str = None) -> Optional[str]:
        """
        Solve CAPTCHA using specified service or fallback chain.
        Returns solution token or None if failed.
        """
        service = service or self.default_service
        
        try:
            if service in self.services:
                return await self.services[service](task)
            else:
                logger.error(f"Unknown CAPTCHA service: {service}")
                return None
                
        except Exception as e:
            logger.error(f"CAPTCHA solving failed with {service}: {e}")
            
            # Try fallback services
            for fallback_service in self.services:
                if fallback_service != service:
                    try:
                        logger.info(f"Trying fallback service: {fallback_service}")
                        return await self.services[fallback_service](task)
                    except Exception as fallback_error:
                        logger.warning(f"Fallback {fallback_service} failed: {fallback_error}")
                        continue
                        
            return None
            
    async def solve_turnstile(self, site_key: str, site_url: str, 
                            service: str = None, proxy: str = None) -> Optional[str]:
        """Solve Cloudflare Turnstile CAPTCHA"""
        task = CaptchaTask(
            captcha_type=CaptchaType.TURNSTILE,
            site_key=site_key,
            site_url=site_url,
            proxy=proxy
        )
        return await self.solve(task, service)
        
    async def solve_recaptcha_v2(self, site_key: str, site_url: str,
                               service: str = None, proxy: str = None) -> Optional[str]:
        """Solve reCAPTCHA v2"""
        task = CaptchaTask(
            captcha_type=CaptchaType.RECAPTCHA_V2,
            site_key=site_key,
            site_url=site_url,
            proxy=proxy
        )
        return await self.solve(task, service)
        
    async def solve_recaptcha_v3(self, site_key: str, site_url: str, action: str = "submit",
                               min_score: float = 0.3, service: str = None, proxy: str = None) -> Optional[str]:
        """Solve reCAPTCHA v3"""
        task = CaptchaTask(
            captcha_type=CaptchaType.RECAPTCHA_V3,
            site_key=site_key,
            site_url=site_url,
            action=action,
            min_score=min_score,
            proxy=proxy
        )
        return await self.solve(task, service)
        
    async def solve_image_captcha(self, image_data: bytes, instruction: str = None,
                                service: str = None) -> Optional[str]:
        """Solve image-based CAPTCHA"""
        task = CaptchaTask(
            captcha_type=CaptchaType.IMAGE,
            image_data=image_data,
            instruction=instruction
        )
        return await self.solve(task, service)
        
    async def _solve_2captcha(self, task: CaptchaTask) -> Optional[str]:
        """Solve CAPTCHA using 2captcha service"""
        api_key = self.api_keys.get('2captcha')
        if not api_key:
            raise ValueError("2captcha API key not provided")
            
        base_url = "http://2captcha.com"
        
        # Submit CAPTCHA
        if task.captcha_type == CaptchaType.RECAPTCHA_V2:
            submit_data = {
                'key': api_key,
                'method': 'userrecaptcha',
                'googlekey': task.site_key,
                'pageurl': task.site_url,
                'json': 1
            }
        elif task.captcha_type == CaptchaType.TURNSTILE:
            submit_data = {
                'key': api_key,
                'method': 'turnstile',
                'sitekey': task.site_key,
                'pageurl': task.site_url,
                'json': 1
            }
        elif task.captcha_type == CaptchaType.IMAGE:
            submit_data = {
                'key': api_key,
                'method': 'base64',
                'body': base64.b64encode(task.image_data).decode(),
                'json': 1
            }
            if task.instruction:
                submit_data['textinstructions'] = task.instruction
        else:
            raise ValueError(f"Unsupported CAPTCHA type for 2captcha: {task.captcha_type}")
            
        if task.proxy:
            submit_data.update({
                'proxy': task.proxy,
                'proxytype': 'HTTP'
            })
            
        # Submit task
        response = requests.post(f"{base_url}/in.php", data=submit_data)
        result = response.json()
        
        if result['status'] != 1:
            raise Exception(f"2captcha submission failed: {result.get('error_text', 'Unknown error')}")
            
        task_id = result['request']
        
        # Poll for result
        for attempt in range(60):  # 5 minutes max
            await asyncio.sleep(5)
            
            check_response = requests.get(f"{base_url}/res.php", params={
                'key': api_key,
                'action': 'get',
                'id': task_id,
                'json': 1
            })
            
            check_result = check_response.json()
            
            if check_result['status'] == 1:
                return check_result['request']
            elif check_result['error_text'] == 'CAPCHA_NOT_READY':
                continue
            else:
                raise Exception(f"2captcha solving failed: {check_result.get('error_text', 'Unknown error')}")
                
        raise TimeoutError("2captcha solving timeout")
        
    async def _solve_anticaptcha(self, task: CaptchaTask) -> Optional[str]:
        """Solve CAPTCHA using AntiCaptcha service"""
        api_key = self.api_keys.get('anticaptcha')
        if not api_key:
            raise ValueError("AntiCaptcha API key not provided")
            
        base_url = "https://api.anti-captcha.com"
        
        # Prepare task data
        if task.captcha_type == CaptchaType.RECAPTCHA_V2:
            task_data = {
                "type": "NoCaptchaTaskProxyless",
                "websiteURL": task.site_url,
                "websiteKey": task.site_key
            }
        elif task.captcha_type == CaptchaType.TURNSTILE:
            task_data = {
                "type": "TurnstileTaskProxyless",
                "websiteURL": task.site_url,
                "websiteKey": task.site_key
            }
        else:
            raise ValueError(f"Unsupported CAPTCHA type for AntiCaptcha: {task.captcha_type}")
            
        # Create task
        create_response = requests.post(f"{base_url}/createTask", json={
            "clientKey": api_key,
            "task": task_data
        })
        
        create_result = create_response.json()
        if create_result.get('errorId') != 0:
            raise Exception(f"AntiCaptcha task creation failed: {create_result.get('errorDescription')}")
            
        task_id = create_result['taskId']
        
        # Poll for result
        for attempt in range(60):
            await asyncio.sleep(5)
            
            result_response = requests.post(f"{base_url}/getTaskResult", json={
                "clientKey": api_key,
                "taskId": task_id
            })
            
            result_data = result_response.json()
            
            if result_data.get('errorId') != 0:
                raise Exception(f"AntiCaptcha error: {result_data.get('errorDescription')}")
                
            if result_data['status'] == 'ready':
                return result_data['solution']['gRecaptchaResponse']
            elif result_data['status'] == 'processing':
                continue
            else:
                raise Exception(f"AntiCaptcha unexpected status: {result_data['status']}")
                
        raise TimeoutError("AntiCaptcha solving timeout")
        
    async def _solve_capsolver(self, task: CaptchaTask) -> Optional[str]:
        """Solve CAPTCHA using CapSolver service"""
        # Placeholder for CapSolver implementation
        raise NotImplementedError("CapSolver integration not implemented yet")
        
    async def _solve_manual(self, task: CaptchaTask) -> Optional[str]:
        """Manual CAPTCHA solving (for development/testing)"""
        logger.info("Manual CAPTCHA solving requested")
        print(f"Please solve the CAPTCHA manually:")
        print(f"Type: {task.captcha_type.value}")
        print(f"Site: {task.site_url}")
        print(f"Site Key: {task.site_key}")
        
        if task.captcha_type == CaptchaType.IMAGE and task.image_data:
            # Save image for manual viewing
            image = Image.open(io.BytesIO(task.image_data))
            image.show()
            
        # In a real implementation, this could open a web interface
        # or integrate with a human solver service
        solution = input("Enter CAPTCHA solution: ").strip()
        return solution if solution else None
        
    async def detect_cloudflare_challenge(self, page_content: str) -> bool:
        """Detect if page contains Cloudflare challenge"""
        cf_indicators = [
            "challenge-platform",
            "cf-challenge",
            "cloudflare",
            "ray id:",
            "_cf_chl_opt",
            "checking your browser"
        ]
        
        content_lower = page_content.lower()
        return any(indicator in content_lower for indicator in cf_indicators)
        
    async def bypass_cloudflare_challenge(self, browser_manager, page, max_wait: int = 30) -> bool:
        """
        Attempt to bypass Cloudflare challenge automatically.
        Returns True if bypass successful, False otherwise.
        """
        logger.info("Attempting Cloudflare challenge bypass")
        
        try:
            # Wait for challenge to complete automatically (JS challenge)
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                # Check if we're still on challenge page
                current_content = await page.content()
                
                if not await self.detect_cloudflare_challenge(current_content):
                    logger.info("Cloudflare challenge passed automatically")
                    return True
                    
                # Look for Turnstile widget
                turnstile_widget = await page.query_selector('iframe[src*="turnstile"]')
                if turnstile_widget:
                    logger.info("Turnstile CAPTCHA detected, attempting to solve")
                    
                    # Extract site key and solve
                    site_key = await page.get_attribute('[data-sitekey]', 'data-sitekey')
                    if site_key:
                        solution = await self.solve_turnstile(site_key, page.url)
                        if solution:
                            # Inject solution (implementation depends on site structure)
                            await page.evaluate(f"""
                                window.turnstileCallback && window.turnstileCallback('{solution}');
                            """)
                            await asyncio.sleep(2)
                            continue
                            
                await asyncio.sleep(2)
                
            logger.warning("Cloudflare challenge bypass timeout")
            return False
            
        except Exception as e:
            logger.error(f"Cloudflare bypass error: {e}")
            return False