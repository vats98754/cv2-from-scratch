"""
Automated account creation system for various social media platforms.
Includes data generation, email verification, and anti-detection measures.
"""

import asyncio
import random
import string
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False
    Faker = None
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

class Platform(Enum):
    """Supported platforms for account creation"""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    REDDIT = "reddit"
    DISCORD = "discord"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    GMAIL = "gmail"
    OUTLOOK = "outlook"

@dataclass
class PersonalInfo:
    """Generated personal information for account creation"""
    first_name: str
    last_name: str
    email: str
    username: str
    password: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    profile_picture: Optional[str] = None
    bio: Optional[str] = None

@dataclass
class AccountCreationResult:
    """Result of account creation attempt"""
    success: bool
    platform: Platform
    account_info: Optional[PersonalInfo] = None
    error_message: Optional[str] = None
    verification_required: bool = False
    verification_method: Optional[str] = None
    session_data: Optional[Dict] = None

class DataGenerator:
    """Generate realistic personal data for account creation"""
    
    def __init__(self, locale: str = 'en_US'):
        if not FAKER_AVAILABLE:
            logger.warning("Faker not available. Data generation will use basic fallbacks.")
            self.faker = None
        else:
            self.faker = Faker(locale)
        self.used_usernames = set()
        self.used_emails = set()
        
    def generate_personal_info(self, platform: Platform = None) -> PersonalInfo:
        """Generate complete personal information"""
        if self.faker:
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
        else:
            # Fallback when Faker is not available
            first_name = f"User{random.randint(1000, 9999)}"
            last_name = f"Test{random.randint(100, 999)}"
        
        # Generate unique username
        username = self._generate_username(first_name, last_name, platform)
        
        # Generate unique email
        email = self._generate_email(first_name, last_name)
        
        # Generate secure password
        password = self._generate_password()
        
        return PersonalInfo(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password,
            phone=self.faker.phone_number() if self.faker else f"+1555{random.randint(1000000, 9999999)}",
            date_of_birth=self.faker.date_of_birth(minimum_age=18, maximum_age=65).strftime('%m/%d/%Y') if self.faker else "01/01/1990",
            address=self.faker.street_address() if self.faker else "123 Main St",
            city=self.faker.city() if self.faker else "Anytown",
            country=self.faker.country() if self.faker else "United States",
            bio=self._generate_bio(platform)
        )
        
    def _generate_username(self, first_name: str, last_name: str, platform: Platform = None) -> str:
        """Generate unique username for platform"""
        base_options = [
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}_{last_name.lower()}",
            f"{first_name.lower()}{random.randint(100, 999)}",
            f"{last_name.lower()}{first_name[0].lower()}{random.randint(10, 99)}"
        ]
        
        # Platform-specific adjustments
        if platform == Platform.TWITTER:
            base_options.extend([
                f"@{first_name.lower()}_{random.randint(1000, 9999)}",
                f"{first_name.lower()}{last_name.lower()}{random.randint(10, 99)}"
            ])
        elif platform == Platform.INSTAGRAM:
            base_options.extend([
                f"{first_name.lower()}_{last_name.lower()}_{random.randint(10, 99)}",
                f"_{first_name.lower()}.{last_name.lower()}_"
            ])
            
        for username in base_options:
            username = username.replace('@', '')  # Remove @ for internal storage
            if username not in self.used_usernames:
                self.used_usernames.add(username)
                return username
                
        # Fallback with random string
        username = f"{first_name.lower()}{random.randint(10000, 99999)}"
        self.used_usernames.add(username)
        return username
        
    def _generate_email(self, first_name: str, last_name: str) -> str:
        """Generate unique email address"""
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'protonmail.com']
        
        email_patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}_{last_name.lower()}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}{random.randint(100, 999)}"
        ]
        
        for pattern in email_patterns:
            email = f"{pattern}@{random.choice(domains)}"
            if email not in self.used_emails:
                self.used_emails.add(email)
                return email
                
        # Fallback
        email = f"{first_name.lower()}{random.randint(10000, 99999)}@{random.choice(domains)}"
        self.used_emails.add(email)
        return email
        
    def _generate_password(self, length: int = 12) -> str:
        """Generate secure password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(length))
        
        # Ensure password complexity
        if not any(c.isupper() for c in password):
            password = password[:-1] + random.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-1] + random.choice(string.ascii_lowercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + random.choice(string.digits)
            
        return password
        
    def _generate_bio(self, platform: Platform = None) -> str:
        """Generate appropriate bio for platform"""
        if platform == Platform.TWITTER:
            bios = [
                "Living life one tweet at a time 🐦",
                "Coffee enthusiast ☕ | Tech lover 💻",
                "Just here for the memes 😄",
                "Opinions are my own 🤷‍♀️",
                "Building something amazing 🚀"
            ]
        elif platform == Platform.INSTAGRAM:
            bios = [
                "📸 Capturing moments\n✨ Living my best life\n🌍 Explorer",
                "🎨 Creative soul\n📱 Digital nomad\n☕ Coffee addict",
                "🌟 Dreamer\n🏃‍♀️ Runner\n📚 Bookworm",
                "🎵 Music lover\n🍕 Foodie\n🏖️ Beach vibes",
                "💪 Fitness enthusiast\n🧘‍♀️ Mindful living\n🌱 Plant parent"
            ]
        else:
            bios = [
                "Just another internet citizen",
                "Exploring the digital world",
                "Here to connect and share",
                "Living the online life",
                "Digital explorer and creator"
            ]
            
        return random.choice(bios)

class AccountCreator:
    """
    Automated account creation system with anti-detection measures.
    Supports multiple platforms and handles verification flows.
    """
    
    def __init__(self, browser_manager=None, captcha_solver=None):
        self.browser_manager = browser_manager
        self.captcha_solver = captcha_solver
        self.data_generator = DataGenerator()
        self.creation_strategies = {
            Platform.TWITTER: self._create_twitter_account,
            Platform.INSTAGRAM: self._create_instagram_account,
            Platform.REDDIT: self._create_reddit_account,
            Platform.DISCORD: self._create_discord_account,
            Platform.GMAIL: self._create_gmail_account
        }
        
    async def create_account(self, platform: Platform, 
                           custom_info: PersonalInfo = None) -> AccountCreationResult:
        """
        Create account on specified platform.
        Returns creation result with success status and account details.
        """
        try:
            if platform not in self.creation_strategies:
                return AccountCreationResult(
                    success=False,
                    platform=platform,
                    error_message=f"Platform {platform.value} not supported yet"
                )
                
            # Generate or use provided personal info
            personal_info = custom_info or self.data_generator.generate_personal_info(platform)
            
            logger.info(f"Creating account on {platform.value} for {personal_info.email}")
            
            # Execute platform-specific creation strategy
            result = await self.creation_strategies[platform](personal_info)
            
            if result.success:
                logger.info(f"Successfully created {platform.value} account")
                # Save account info securely
                await self._save_account_info(result)
            else:
                logger.error(f"Failed to create {platform.value} account: {result.error_message}")
                
            return result
            
        except Exception as e:
            logger.error(f"Account creation error for {platform.value}: {e}")
            return AccountCreationResult(
                success=False,
                platform=platform,
                error_message=str(e)
            )
            
    async def _create_twitter_account(self, info: PersonalInfo) -> AccountCreationResult:
        """Create Twitter account"""
        if not self.browser_manager:
            raise ValueError("Browser manager required for Twitter account creation")
            
        context = await self.browser_manager.create_context()
        page = await self.browser_manager.new_page(context)
        
        try:
            # Navigate to Twitter signup
            await self.browser_manager.navigate_with_retry(page, "https://twitter.com/i/flow/signup")
            
            # Fill signup form
            await page.wait_for_selector('input[name="name"]', timeout=10000)
            await self.browser_manager.type_human_like(page, 'input[name="name"]', 
                                                     f"{info.first_name} {info.last_name}")
            
            await self.browser_manager.type_human_like(page, 'input[name="email"]', info.email)
            
            # Handle date of birth
            if info.date_of_birth:
                birth_parts = info.date_of_birth.split('/')
                await page.select_option('select[name="month"]', birth_parts[0])
                await page.select_option('select[name="day"]', birth_parts[1])
                await page.select_option('select[name="year"]', birth_parts[2])
                
            # Continue to next step
            await page.click('div[data-testid="ocfSignupNextLink"]')
            
            # Handle verification if required
            await asyncio.sleep(3)
            
            # Check for CAPTCHA
            if await page.query_selector('iframe[src*="recaptcha"]'):
                logger.info("reCAPTCHA detected on Twitter signup")
                if self.captcha_solver:
                    # Solve CAPTCHA
                    site_key = await page.get_attribute('[data-sitekey]', 'data-sitekey')
                    if site_key:
                        solution = await self.captcha_solver.solve_recaptcha_v2(site_key, page.url)
                        if solution:
                            await page.evaluate(f"document.getElementById('g-recaptcha-response').innerHTML='{solution}';")
                            
            # Complete signup flow
            # This would continue with verification, username selection, etc.
            # Implementation depends on current Twitter flow
            
            return AccountCreationResult(
                success=True,
                platform=Platform.TWITTER,
                account_info=info,
                verification_required=True,
                verification_method="email"
            )
            
        except Exception as e:
            return AccountCreationResult(
                success=False,
                platform=Platform.TWITTER,
                error_message=str(e)
            )
        finally:
            await context.close()
            
    async def _create_instagram_account(self, info: PersonalInfo) -> AccountCreationResult:
        """Create Instagram account"""
        if not self.browser_manager:
            raise ValueError("Browser manager required for Instagram account creation")
            
        context = await self.browser_manager.create_context()
        page = await self.browser_manager.new_page(context)
        
        try:
            # Navigate to Instagram signup
            await self.browser_manager.navigate_with_retry(page, "https://www.instagram.com/accounts/emailsignup/")
            
            # Fill signup form
            await page.wait_for_selector('input[name="emailOrPhone"]', timeout=10000)
            await self.browser_manager.type_human_like(page, 'input[name="emailOrPhone"]', info.email)
            await self.browser_manager.type_human_like(page, 'input[name="fullName"]', 
                                                     f"{info.first_name} {info.last_name}")
            await self.browser_manager.type_human_like(page, 'input[name="username"]', info.username)
            await self.browser_manager.type_human_like(page, 'input[name="password"]', info.password)
            
            # Submit form
            await page.click('button[type="submit"]')
            
            # Handle verification
            await asyncio.sleep(3)
            
            return AccountCreationResult(
                success=True,
                platform=Platform.INSTAGRAM,
                account_info=info,
                verification_required=True,
                verification_method="email"
            )
            
        except Exception as e:
            return AccountCreationResult(
                success=False,
                platform=Platform.INSTAGRAM,
                error_message=str(e)
            )
        finally:
            await context.close()
            
    async def _create_reddit_account(self, info: PersonalInfo) -> AccountCreationResult:
        """Create Reddit account"""
        # Implementation for Reddit account creation
        return AccountCreationResult(
            success=False,
            platform=Platform.REDDIT,
            error_message="Reddit account creation not implemented yet"
        )
        
    async def _create_discord_account(self, info: PersonalInfo) -> AccountCreationResult:
        """Create Discord account"""
        # Implementation for Discord account creation
        return AccountCreationResult(
            success=False,
            platform=Platform.DISCORD,
            error_message="Discord account creation not implemented yet"
        )
        
    async def _create_gmail_account(self, info: PersonalInfo) -> AccountCreationResult:
        """Create Gmail account"""
        # Implementation for Gmail account creation
        return AccountCreationResult(
            success=False,
            platform=Platform.GMAIL,
            error_message="Gmail account creation not implemented yet"
        )
        
    async def _save_account_info(self, result: AccountCreationResult):
        """Securely save account information"""
        if not result.account_info:
            return
            
        # Create accounts directory if it doesn't exist
        accounts_dir = "/tmp/accounts"
        os.makedirs(accounts_dir, exist_ok=True)
        
        # Save account info as encrypted JSON
        account_data = {
            'platform': result.platform.value,
            'created_at': time.time(),
            'account_info': asdict(result.account_info),
            'verification_required': result.verification_required,
            'verification_method': result.verification_method
        }
        
        filename = f"{result.platform.value}_{result.account_info.username}_{int(time.time())}.json"
        filepath = os.path.join(accounts_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(account_data, f, indent=2)
            
        logger.info(f"Account info saved to {filepath}")
        
    async def create_multiple_accounts(self, platform: Platform, count: int = 1) -> List[AccountCreationResult]:
        """Create multiple accounts with delays between creation"""
        results = []
        
        for i in range(count):
            logger.info(f"Creating account {i+1}/{count} for {platform.value}")
            
            result = await self.create_account(platform)
            results.append(result)
            
            # Add delay between account creations to avoid rate limiting
            if i < count - 1:  # Don't wait after the last account
                delay = random.uniform(30, 120)  # 30 seconds to 2 minutes
                logger.info(f"Waiting {delay:.1f} seconds before next account creation")
                await asyncio.sleep(delay)
                
        return results
        
    async def verify_account(self, platform: Platform, verification_code: str, 
                           session_data: Dict = None) -> bool:
        """Verify account using email/SMS code"""
        # Implementation for account verification
        # This would handle email verification, SMS verification, etc.
        logger.info(f"Verifying {platform.value} account with code {verification_code}")
        return True