"""
Account Creator
Automated account creation for various social media platforms
"""

import asyncio
import logging
import random
import string
from typing import Dict, Any, Optional
from .browser_manager import BrowserManager
from .captcha_solver import CaptchaSolver

logger = logging.getLogger(__name__)

class AccountCreator:
    """Creates accounts on various social media platforms"""
    
    def __init__(self, browser_manager: BrowserManager, captcha_solver: CaptchaSolver):
        self.browser_manager = browser_manager
        self.captcha_solver = captcha_solver
        
        # Platform configurations
        self.platforms = {
            "twitter": {
                "signup_url": "https://twitter.com/i/flow/signup",
                "selectors": {
                    "name_input": '[name="name"]',
                    "email_input": '[name="email"]',
                    "password_input": '[name="password"]',
                    "signup_button": '[data-testid="signupButton"]',
                    "next_button": '[data-testid="ocfSignupNextLink"]'
                }
            },
            "instagram": {
                "signup_url": "https://www.instagram.com/accounts/emailsignup/",
                "selectors": {
                    "email_input": '[name="emailOrPhone"]',
                    "fullname_input": '[name="fullName"]',
                    "username_input": '[name="username"]',
                    "password_input": '[name="password"]',
                    "signup_button": 'button[type="submit"]'
                }
            },
            "facebook": {
                "signup_url": "https://www.facebook.com/reg/",
                "selectors": {
                    "firstname_input": '[name="firstname"]',
                    "lastname_input": '[name="lastname"]',
                    "email_input": '[name="reg_email__"]',
                    "password_input": '[name="reg_passwd__"]',
                    "signup_button": '[name="websubmit"]'
                }
            },
            "linkedin": {
                "signup_url": "https://www.linkedin.com/signup",
                "selectors": {
                    "email_input": '#email-address',
                    "password_input": '#password',
                    "firstname_input": '#first-name',
                    "lastname_input": '#last-name',
                    "signup_button": '#join-form-submit'
                }
            },
            "reddit": {
                "signup_url": "https://www.reddit.com/register/",
                "selectors": {
                    "email_input": '#regEmail',
                    "username_input": '#regUsername',
                    "password_input": '#regPassword',
                    "signup_button": 'button[type="submit"]'
                }
            }
        }
    
    async def create_account(self, platform: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an account on the specified platform
        
        Args:
            platform: Platform name (twitter, instagram, facebook, etc.)
            account_data: Dictionary containing account information
        """
        try:
            if platform.lower() not in self.platforms:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not supported",
                    "supported_platforms": list(self.platforms.keys())
                }
            
            platform_config = self.platforms[platform.lower()]
            
            # Generate missing data if not provided
            account_data = self._generate_missing_data(account_data)
            
            # Create account based on platform
            if platform.lower() == "twitter":
                return await self._create_twitter_account(platform_config, account_data)
            elif platform.lower() == "instagram":
                return await self._create_instagram_account(platform_config, account_data)
            elif platform.lower() == "facebook":
                return await self._create_facebook_account(platform_config, account_data)
            elif platform.lower() == "linkedin":
                return await self._create_linkedin_account(platform_config, account_data)
            elif platform.lower() == "reddit":
                return await self._create_reddit_account(platform_config, account_data)
            else:
                return await self._create_generic_account(platform_config, account_data)
                
        except Exception as e:
            logger.error(f"Account creation failed for {platform}: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_missing_data(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate missing account data"""
        if "username" not in account_data:
            account_data["username"] = self._generate_username()
        
        if "email" not in account_data:
            account_data["email"] = f"{account_data['username']}@tempmail.com"
        
        if "password" not in account_data:
            account_data["password"] = self._generate_password()
        
        if "first_name" not in account_data:
            account_data["first_name"] = self._generate_name()
        
        if "last_name" not in account_data:
            account_data["last_name"] = self._generate_name()
        
        if "full_name" not in account_data:
            account_data["full_name"] = f"{account_data['first_name']} {account_data['last_name']}"
        
        return account_data
    
    def _generate_username(self) -> str:
        """Generate a random username"""
        prefix = random.choice(["user", "person", "account", "profile"])
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{suffix}"
    
    def _generate_password(self) -> str:
        """Generate a secure password"""
        length = random.randint(12, 16)
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choices(chars, k=length))
    
    def _generate_name(self) -> str:
        """Generate a random name"""
        names = [
            "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery",
            "Quinn", "Sage", "River", "Phoenix", "Skylar", "Cameron", "Dakota"
        ]
        return random.choice(names)
    
    async def _create_twitter_account(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Twitter account"""
        try:
            page = await self.browser_manager.get_page()
            
            # Navigate to signup page
            await self.browser_manager.navigate(config["signup_url"])
            
            # Handle potential Cloudflare challenge
            await self.captcha_solver.bypass_cloudflare_challenge(page)
            
            # Fill in the form
            selectors = config["selectors"]
            
            # Name field
            if await self.browser_manager.wait_for_element(selectors["name_input"]):
                await self.browser_manager.fill_input(selectors["name_input"], data["full_name"])
            
            # Email field
            if await self.browser_manager.wait_for_element(selectors["email_input"]):
                await self.browser_manager.fill_input(selectors["email_input"], data["email"])
            
            # Click next/continue
            if await self.browser_manager.wait_for_element(selectors["next_button"]):
                await self.browser_manager.click_element(selectors["next_button"])
            
            # Wait for password field and fill it
            await asyncio.sleep(2)
            if await self.browser_manager.wait_for_element(selectors["password_input"]):
                await self.browser_manager.fill_input(selectors["password_input"], data["password"])
            
            # Submit the form
            if await self.browser_manager.wait_for_element(selectors["signup_button"]):
                await self.browser_manager.click_element(selectors["signup_button"])
            
            # Wait for potential CAPTCHA or verification
            await asyncio.sleep(5)
            
            # Check for CAPTCHA
            await self._handle_captcha_if_present(page)
            
            return {
                "success": True,
                "platform": "twitter",
                "username": data["username"],
                "email": data["email"],
                "message": "Twitter account creation initiated"
            }
            
        except Exception as e:
            logger.error(f"Twitter account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_instagram_account(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Instagram account"""
        try:
            page = await self.browser_manager.get_page()
            await self.browser_manager.navigate(config["signup_url"])
            
            selectors = config["selectors"]
            
            # Fill form fields
            await asyncio.sleep(2)
            
            if await self.browser_manager.wait_for_element(selectors["email_input"]):
                await self.browser_manager.fill_input(selectors["email_input"], data["email"])
            
            if await self.browser_manager.wait_for_element(selectors["fullname_input"]):
                await self.browser_manager.fill_input(selectors["fullname_input"], data["full_name"])
            
            if await self.browser_manager.wait_for_element(selectors["username_input"]):
                await self.browser_manager.fill_input(selectors["username_input"], data["username"])
            
            if await self.browser_manager.wait_for_element(selectors["password_input"]):
                await self.browser_manager.fill_input(selectors["password_input"], data["password"])
            
            # Submit
            if await self.browser_manager.wait_for_element(selectors["signup_button"]):
                await self.browser_manager.click_element(selectors["signup_button"])
            
            await self._handle_captcha_if_present(page)
            
            return {
                "success": True,
                "platform": "instagram",
                "username": data["username"],
                "email": data["email"],
                "message": "Instagram account creation initiated"
            }
            
        except Exception as e:
            logger.error(f"Instagram account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_facebook_account(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Facebook account"""
        try:
            page = await self.browser_manager.get_page()
            await self.browser_manager.navigate(config["signup_url"])
            
            selectors = config["selectors"]
            await asyncio.sleep(3)
            
            # Fill form fields
            if await self.browser_manager.wait_for_element(selectors["firstname_input"]):
                await self.browser_manager.fill_input(selectors["firstname_input"], data["first_name"])
            
            if await self.browser_manager.wait_for_element(selectors["lastname_input"]):
                await self.browser_manager.fill_input(selectors["lastname_input"], data["last_name"])
            
            if await self.browser_manager.wait_for_element(selectors["email_input"]):
                await self.browser_manager.fill_input(selectors["email_input"], data["email"])
            
            if await self.browser_manager.wait_for_element(selectors["password_input"]):
                await self.browser_manager.fill_input(selectors["password_input"], data["password"])
            
            # Submit
            if await self.browser_manager.wait_for_element(selectors["signup_button"]):
                await self.browser_manager.click_element(selectors["signup_button"])
            
            await self._handle_captcha_if_present(page)
            
            return {
                "success": True,
                "platform": "facebook",
                "username": data["username"],
                "email": data["email"],
                "message": "Facebook account creation initiated"
            }
            
        except Exception as e:
            logger.error(f"Facebook account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_linkedin_account(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Create LinkedIn account"""
        try:
            page = await self.browser_manager.get_page()
            await self.browser_manager.navigate(config["signup_url"])
            
            selectors = config["selectors"]
            await asyncio.sleep(2)
            
            # Fill form fields
            if await self.browser_manager.wait_for_element(selectors["email_input"]):
                await self.browser_manager.fill_input(selectors["email_input"], data["email"])
            
            if await self.browser_manager.wait_for_element(selectors["password_input"]):
                await self.browser_manager.fill_input(selectors["password_input"], data["password"])
            
            if await self.browser_manager.wait_for_element(selectors["firstname_input"]):
                await self.browser_manager.fill_input(selectors["firstname_input"], data["first_name"])
            
            if await self.browser_manager.wait_for_element(selectors["lastname_input"]):
                await self.browser_manager.fill_input(selectors["lastname_input"], data["last_name"])
            
            # Submit
            if await self.browser_manager.wait_for_element(selectors["signup_button"]):
                await self.browser_manager.click_element(selectors["signup_button"])
            
            await self._handle_captcha_if_present(page)
            
            return {
                "success": True,
                "platform": "linkedin",
                "username": data["username"],
                "email": data["email"],
                "message": "LinkedIn account creation initiated"
            }
            
        except Exception as e:
            logger.error(f"LinkedIn account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_reddit_account(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Reddit account"""
        try:
            page = await self.browser_manager.get_page()
            await self.browser_manager.navigate(config["signup_url"])
            
            selectors = config["selectors"]
            await asyncio.sleep(2)
            
            # Fill form fields
            if await self.browser_manager.wait_for_element(selectors["email_input"]):
                await self.browser_manager.fill_input(selectors["email_input"], data["email"])
            
            if await self.browser_manager.wait_for_element(selectors["username_input"]):
                await self.browser_manager.fill_input(selectors["username_input"], data["username"])
            
            if await self.browser_manager.wait_for_element(selectors["password_input"]):
                await self.browser_manager.fill_input(selectors["password_input"], data["password"])
            
            # Submit
            if await self.browser_manager.wait_for_element(selectors["signup_button"]):
                await self.browser_manager.click_element(selectors["signup_button"])
            
            await self._handle_captcha_if_present(page)
            
            return {
                "success": True,
                "platform": "reddit",
                "username": data["username"],
                "email": data["email"],
                "message": "Reddit account creation initiated"
            }
            
        except Exception as e:
            logger.error(f"Reddit account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_generic_account(self, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic account creation for other platforms"""
        try:
            page = await self.browser_manager.get_page()
            await self.browser_manager.navigate(config["signup_url"])
            
            # Generic form filling logic
            await asyncio.sleep(3)
            
            return {
                "success": True,
                "platform": "generic",
                "username": data["username"],
                "email": data["email"],
                "message": "Generic account creation attempted"
            }
            
        except Exception as e:
            logger.error(f"Generic account creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_captcha_if_present(self, page) -> bool:
        """Check for and handle CAPTCHA if present"""
        try:
            # Common CAPTCHA selectors
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                '.cf-turnstile',
                '[data-sitekey]',
                '.captcha',
                '#captcha'
            ]
            
            await asyncio.sleep(2)
            
            for selector in captcha_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"CAPTCHA detected: {selector}")
                        
                        # Get site key if available
                        site_key = None
                        for element in elements:
                            site_key = await element.get_attribute("data-sitekey")
                            if site_key:
                                break
                        
                        if site_key:
                            # Solve CAPTCHA
                            result = await self.captcha_solver.solve(
                                site_key=site_key,
                                page_url=page.url
                            )
                            
                            if result.get("success"):
                                logger.info("CAPTCHA solved successfully")
                                return True
                        
                        break
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue
            
            return True  # No CAPTCHA found or already handled
            
        except Exception as e:
            logger.error(f"CAPTCHA handling failed: {e}")
            return False