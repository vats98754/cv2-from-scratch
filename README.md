# Browser Automation Platform

A comprehensive platform for browser automation, CAPTCHA bypassing, social media account creation, and task orchestration with LLM-powered natural language processing.

## Features

✅ **Browser Automation Library**
- Robust browser automation using Playwright
- Stealth mode with anti-detection features
- Human-like interaction patterns
- Multi-context and multi-page support

✅ **Cloudflare (Turnstile) and CAPTCHA Bypassing**
- Support for various CAPTCHA types (reCAPTCHA, hCaptcha, Turnstile)
- Integration with solving services (2captcha, AntiCaptcha)
- Automatic CAPTCHA detection and solving
- Cloudflare challenge bypass

✅ **Automated Account Creation**
- Support for major social media platforms:
  - Twitter/X
  - Instagram
  - Facebook
  - LinkedIn
  - Reddit
- Automatic form filling with human-like typing
- Email and username generation
- Rate limiting and anti-detection measures

✅ **Cron Job Scheduling**
- Full cron expression support
- Built-in task types (navigation, scraping, account creation)
- Job monitoring and status tracking
- Automatic restart on failure
- Custom task registration

✅ **Background Processes**
- Render.com-style background process management
- Process monitoring and health checks
- Automatic restart on failure
- Resource usage tracking
- Log management

✅ **LLM-Based Text-to-Orchestration**
- Natural language task description parsing
- Automatic schedule extraction
- Task dependency management
- Execution plan generation
- Support for OpenAI and Anthropic models

✅ **Quick Response Times**
- FastAPI-based REST API
- Async/await throughout
- Efficient resource management
- Connection pooling

## Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start the Platform**
```bash
python main.py
```

4. **Access the API**
- Web interface: http://localhost:8000
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## API Endpoints

### Core Services
- `GET /` - Platform overview
- `GET /health` - Health check
- `GET /browser/status` - Browser status
- `POST /browser/navigate` - Navigate browser
- `POST /captcha/solve` - Solve CAPTCHA
- `POST /account/create` - Create social media account

### Scheduling
- `GET /jobs/status` - Job status
- `POST /jobs/schedule` - Schedule cron job
- `POST /orchestrate` - LLM-powered orchestration

## Example Usage

### 1. Create Social Media Account
```python
import requests

response = requests.post('http://localhost:8000/account/create', json={
    'platform': 'twitter',
    'account_data': {
        'email': 'test@example.com',
        'username': 'testuser123',
        'password': 'SecurePass123!',
        'first_name': 'Test',
        'last_name': 'User'
    }
})
```

### 2. Schedule Automated Tasks
```python
response = requests.post('http://localhost:8000/jobs/schedule', json={
    'cron_expression': '0 9 * * *',  # Daily at 9 AM
    'task_name': 'account_create',
    'task_params': {
        'platform': 'instagram',
        'account_data': {...}
    }
})
```

### 3. Natural Language Orchestration
```python
response = requests.post('http://localhost:8000/orchestrate', json={
    'text_description': 'Create 5 Twitter accounts every day at 9 AM and scrape trending topics every hour'
})
```

## Supported Platforms

### Social Media
- **Twitter/X** - Account creation, posting, following
- **Instagram** - Account creation, posting, stories
- **Facebook** - Account creation, posting, groups
- **LinkedIn** - Account creation, networking, posting
- **Reddit** - Account creation, posting, commenting

### CAPTCHA Services
- **Google reCAPTCHA** (v2, v3)
- **hCaptcha**
- **Cloudflare Turnstile**
- **Image-based CAPTCHAs**

## Configuration

Key configuration options in `.env`:

```bash
# API Keys
OPENAI_API_KEY=your_key_here
CAPTCHA_SERVICE_API_KEY=your_key_here

# Browser Settings
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30000

# Rate Limiting
ACCOUNT_CREATION_DELAY_MIN=5
ACCOUNT_CREATION_DELAY_MAX=15
```

## Task Types

### Built-in Tasks
- `browser_navigate` - Navigate to URLs
- `account_create` - Create social media accounts
- `data_scrape` - Scrape data from websites
- `health_check` - System health monitoring
- `cleanup` - Clean temporary files
- `backup` - Backup important data

### Custom Tasks
Register custom tasks:
```python
def my_custom_task(params):
    # Your task logic here
    pass

cron_manager.register_task('my_task', my_custom_task)
```

## Background Processes

Start long-running processes:
```python
# Web scraper
response = requests.post('/background/start', json={
    'name': 'web_scraper',
    'params': {
        'urls': ['http://example.com'],
        'interval': 3600
    }
})

# Account manager
response = requests.post('/background/start', json={
    'name': 'account_manager',
    'params': {
        'platforms': ['twitter', 'instagram'],
        'check_interval': 1800
    }
})
```

## Legacy CV Code

The original computer vision code has been preserved in the `cv_legacy/` directory and remains fully functional for image processing tasks.

## Security & Ethics

⚠️ **Important**: This platform is for educational and legitimate automation purposes only. Always:
- Respect platform terms of service
- Use appropriate rate limiting
- Obtain proper permissions for data scraping
- Follow local laws and regulations
- Use responsibly and ethically

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is for educational purposes. Please use responsibly and in accordance with platform terms of service and applicable laws.

## Troubleshooting

### Common Issues

1. **Playwright browser not installed**
```bash
python -m playwright install chromium
```

2. **CAPTCHA solving fails**
- Check API key configuration
- Verify service credits/balance
- Review CAPTCHA service status

3. **Rate limiting issues**
- Increase delays between requests
- Use proxy rotation
- Implement better session management

### Support

For issues and questions:
1. Check the documentation
2. Review error logs
3. Test with simpler configurations
4. Submit GitHub issues with detailed logs