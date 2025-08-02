# Web Automation Platform

A comprehensive platform for browser automation, social media automation, CAPTCHA bypassing, and task scheduling. This platform transforms natural language descriptions into automated workflows.

## Features

### ✅ 1. Browser Automation Library
- **Playwright** integration with stealth mode
- **Selenium** support with undetected ChromeDriver
- Anti-detection measures and human-like interactions
- Retry mechanisms and robust error handling
- Session management and connection pooling

### ✅ 2. Cloudflare and CAPTCHA Bypassing
- **Turnstile** bypass support
- **reCAPTCHA v2/v3** solving
- **hCAPTCHA** integration
- Multiple solver services (2captcha, AntiCaptcha)
- Automatic challenge detection and handling

### ✅ 3. Automated Account Creation
- **Social media platforms**: Twitter, Instagram, Facebook, Reddit, Discord, LinkedIn
- **Email providers**: Gmail, Outlook
- Realistic data generation with Faker
- Email/SMS verification handling
- Anti-detection measures and delays

### ✅ 4. Cron Job Scheduling
- **APScheduler** integration for robust scheduling
- Cron expressions and interval triggers
- Job persistence and monitoring
- Execution history and error tracking
- Dependency management between jobs

### ✅ 5. Background Process Management
- **Process lifecycle** management (start, stop, restart)
- Health checks and monitoring
- Resource usage tracking (CPU, memory)
- Auto-restart on crashes
- Similar to render.com process management

### ✅ 6. LLM-based Task Orchestration
- **Natural language** to task conversion
- **OpenAI/Claude** integration for text parsing
- Workflow creation from descriptions
- Task dependency resolution
- Pattern-based fallback parsing

### ✅ 7. Robust Browser Automation
- **Stealth mode** with anti-detection
- Retry mechanisms and timeout handling
- Human-like delays and interactions
- Deterministic automation patterns
- Error recovery and fallback strategies

### ✅ 8. Performance Optimizations
- **Async/await** patterns throughout
- Connection pooling and resource reuse
- Fast response times with FastAPI
- Background task processing
- Efficient resource management

## Installation

1. **Install core dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install automation dependencies:**
```bash
pip install -r automation_requirements.txt
```

3. **Install Playwright browsers:**
```bash
playwright install
```

4. **Set up environment variables:**
```bash
export CAPTCHA_2CAPTCHA_API_KEY="your_2captcha_key"
export CAPTCHA_ANTICAPTCHA_API_KEY="your_anticaptcha_key"
export OPENAI_API_KEY="your_openai_key"  # Optional for LLM features
```

## Quick Start

### 1. Web Server Mode
```bash
python main.py
```
Access the API at `http://localhost:8000`

### 2. CLI Mode
```bash
python main.py cli
```

### 3. API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## Usage Examples

### Natural Language Task Creation
```python
# Example: Create workflow from text
POST /orchestrate
{
    "text": "Create 5 Twitter accounts every day at 9 AM and scrape trending topics",
    "workflow_name": "Daily Twitter Automation"
}
```

### Direct Account Creation
```python
# Example: Create Instagram accounts
POST /accounts/create
{
    "platform": "instagram",
    "count": 3
}
```

### Schedule Background Jobs
```python
# Example: Schedule web scraping
POST /jobs
{
    "job_id": "daily_scraping",
    "name": "Daily Data Collection",
    "function": "example_web_scraping",
    "cron_expression": "0 9 * * *"
}
```

### Process Management
```python
# Example: Add background process
POST /processes
{
    "process_id": "data_processor",
    "name": "Data Processing Service",
    "command": "python data_processor.py",
    "process_type": "background_job",
    "auto_restart": true
}
```

## Architecture

```
┌─────────────────────────────────────────────┐
│                 FastAPI Server              │
├─────────────────────────────────────────────┤
│              Task Orchestrator              │
│         (Natural Language → Tasks)          │
├─────────────────────────────────────────────┤
│  Browser Manager  │  Account Creator       │
│  CAPTCHA Solver   │  Job Scheduler         │
│  Process Manager  │  LLM Integration       │
└─────────────────────────────────────────────┘
```

## API Endpoints

### Core Endpoints
- `GET /` - Platform information
- `GET /health` - Health check
- `GET /docs` - API documentation

### Task Orchestration
- `POST /orchestrate` - Create workflow from text
- `GET /workflows` - List workflows
- `POST /workflows/{id}/execute` - Execute workflow

### Account Management
- `POST /accounts/create` - Create social media accounts

### Job Scheduling
- `POST /jobs` - Add scheduled job
- `GET /jobs` - List jobs
- `POST /jobs/{id}/run` - Run job immediately
- `DELETE /jobs/{id}` - Remove job

### Process Management
- `POST /processes` - Add background process
- `GET /processes` - List processes
- `POST /processes/{id}/start` - Start process
- `POST /processes/{id}/stop` - Stop process
- `DELETE /processes/{id}` - Remove process

### CAPTCHA Solving
- `POST /captcha/solve` - Solve CAPTCHA

## Configuration

### Browser Configuration
```python
browser_config = BrowserConfig(
    headless=True,
    stealth_mode=True,
    proxy="http://proxy:8080",
    user_agent="custom_user_agent",
    timeout=30000,
    retries=3
)
```

### CAPTCHA Configuration
```python
api_keys = {
    '2captcha': 'your_api_key',
    'anticaptcha': 'your_api_key'
}
captcha_solver = CaptchaSolver(api_keys)
```

## Examples

### Example 1: Social Media Automation
```bash
curl -X POST "http://localhost:8000/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Create 3 Twitter accounts every Monday and post daily trending topics",
    "workflow_name": "Social Media Management"
  }'
```

### Example 2: Data Collection Pipeline
```bash
curl -X POST "http://localhost:8000/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Scrape news articles from example.com every hour and save to database",
    "workflow_name": "News Collection"
  }'
```

### Example 3: Account Monitoring
```bash
curl -X POST "http://localhost:8000/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Check all social media accounts every 30 minutes for messages and notifications",
    "workflow_name": "Account Monitoring"
  }'
```

## Advanced Features

### Custom Task Functions
Register your own functions for job execution:

```python
async def custom_task():
    # Your automation logic here
    return {"status": "completed"}

job_scheduler.register_function("custom_task", custom_task)
```

### Stealth Browser Automation
```python
async with BrowserManager(config) as browser:
    context = await browser.create_context()
    page = await browser.new_page(context)
    
    # Human-like typing
    await browser.type_human_like(page, "#username", "user@example.com")
    
    # Navigate with retries
    await browser.navigate_with_retry(page, "https://example.com")
```

### LLM Integration
```python
# Set up OpenAI client
import openai
task_orchestrator.set_llm_client(openai.AsyncClient())

# Parse natural language
tasks = await task_orchestrator.parse_natural_language(
    "Create 5 Reddit accounts and post in programming subreddits daily"
)
```

## Security Considerations

1. **API Keys**: Store sensitive API keys in environment variables
2. **Rate Limiting**: Implement rate limiting for account creation
3. **Proxy Rotation**: Use proxy services for large-scale operations
4. **User Agents**: Rotate user agents to avoid detection
5. **Delays**: Add random delays between operations

## Performance Tips

1. **Connection Pooling**: Reuse browser contexts when possible
2. **Async Operations**: Use async/await for concurrent operations
3. **Resource Limits**: Set memory and CPU limits for processes
4. **Monitoring**: Monitor resource usage and job execution times
5. **Cleanup**: Properly clean up browser resources

## Troubleshooting

### Common Issues
1. **Browser not found**: Run `playwright install`
2. **CAPTCHA failures**: Check API keys and service status
3. **Job not executing**: Verify function registration
4. **Process crashes**: Check logs and resource limits

### Logging
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and legitimate automation purposes only. Users are responsible for complying with terms of service of target platforms and applicable laws.