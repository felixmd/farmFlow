# FarmBot Logging Guide

## Overview
FarmBot uses comprehensive logging to track all user interactions, agent decisions, and errors. Logs are written to both console and a persistent log file.

## Log File Location
```
telegram_bot.log
```

Located in the project root directory.

## Viewing Logs

### Real-time Monitoring (Tail)
```bash
# View last 50 lines
tail -50 telegram_bot.log

# Follow logs in real-time
tail -f telegram_bot.log

# Follow with grep filter (errors only)
tail -f telegram_bot.log | grep ERROR

# Follow with grep filter (specific user)
tail -f telegram_bot.log | grep "user_12345"
```

### Search Logs
```bash
# Search for specific user
grep "user_12345" telegram_bot.log

# Search for errors
grep "ERROR" telegram_bot.log

# Search for a specific agent
grep "\[agronomist\]" telegram_bot.log

# Search for tool usage
grep "Tool called" telegram_bot.log

# Search for image uploads
grep "Photo: True" telegram_bot.log
```

### View Specific Time Range
```bash
# View logs from specific date
grep "2025-11-25" telegram_bot.log

# View logs from specific hour
grep "2025-11-25 04:" telegram_bot.log
```

## Log Structure

### Message Flow Pattern
Every user message follows this 5-step pattern:

```
[STEP 1/5] Getting/creating session
[STEP 1/5] ✓ Session ID: abc-123-def

[STEP 2/5] No image attached
# OR
[STEP 2/5] Downloading image from user 12345
[STEP 2/5] ✓ Image downloaded: 50000 bytes

[STEP 3/5] Querying orchestrator for routing decision
[STEP 3/5] ✓ Orchestrator response received

[STEP 4/5] Parsing routing decision
[STEP 4/5] ✓ Route: AGRONOMY_QUERY -> agronomist

[STEP 5/5] Executing routing decision: AGRONOMY_QUERY
[STEP 5/5] ✓ Response sent successfully
```

### Agent-Specific Logs
Each agent interaction is tagged:
- `[Orchestrator]` - Routing decisions
- `[agronomist]` - Crop advice queries
- `[market_analyst]` - Financial calculations

### Success Indicators
- `✓` - Step completed successfully
- `✗` - Step failed with error
- `⚠` - Warning condition

## Common Debugging Patterns

### Finding Failed Requests
```bash
# Find all errors
grep "✗" telegram_bot.log

# Find which step failed
grep "\[STEP.*✗" telegram_bot.log

# Find full error traces
grep -A 10 "ERROR" telegram_bot.log
```

### Tracking User Sessions
```bash
# Find all activity for a specific user
grep "user_12345" telegram_bot.log

# Find session creation
grep "Session Created" telegram_bot.log

# Find session IDs
grep "Session ID:" telegram_bot.log
```

### Agent Performance
```bash
# Find tool usage
grep "Tool called" telegram_bot.log

# Find code execution
grep "code_execution" telegram_bot.log

# Find Google Search calls
grep "google_search" telegram_bot.log

# See event counts
grep "Processed.*events total" telegram_bot.log
```

### Image Upload Tracking
```bash
# Find image uploads
grep "Photo: True" telegram_bot.log

# Find image download size
grep "Image downloaded:" telegram_bot.log

# Find image processing in agents
grep "Adding image data" telegram_bot.log
```

## Log Rotation

The log file grows over time. For production, consider rotating logs:

```bash
# Manually rotate logs
mv telegram_bot.log telegram_bot.log.$(date +%Y%m%d_%H%M%S)

# Or use logrotate (Linux)
# Create /etc/logrotate.d/farmbot:
/path/to/FarmFlow/telegram_bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Debugging Workflow

### 1. User Reports Error
```bash
# Get user's Telegram ID from their message
# Then search for their activity
grep "user_<TELEGRAM_ID>" telegram_bot.log | tail -50
```

### 2. Find Exact Failure Point
```bash
# Look for the ✗ symbol in their recent activity
grep "user_<TELEGRAM_ID>" telegram_bot.log | grep "✗"
```

### 3. Get Full Stack Trace
```bash
# Find ERROR lines with context
grep -A 20 "ERROR.*user_<TELEGRAM_ID>" telegram_bot.log
```

### 4. Check Which Agent Failed
```bash
# See which agent was processing the request
grep "user_<TELEGRAM_ID>" telegram_bot.log | grep "Routing to specialist"
```

### 5. Verify Tool Usage
```bash
# Check if tools were called successfully
grep "user_<TELEGRAM_ID>" telegram_bot.log | grep "Tool called"
```

## Example Log Analysis

### Success Case
```
2025-11-25 04:52:00,100 - __main__ - INFO - Received from 12345 (John): What are tomato prices? [Photo: False]
2025-11-25 04:52:00,101 - __main__ - INFO - [STEP 1/5] ✓ Session ID: abc-123
2025-11-25 04:52:00,102 - __main__ - INFO - [STEP 2/5] No image attached
2025-11-25 04:52:00,103 - __main__ - INFO - [STEP 3/5] ✓ Orchestrator response received
2025-11-25 04:52:00,104 - __main__ - INFO - [STEP 4/5] ✓ Route: AGRONOMY_QUERY -> agronomist
2025-11-25 04:52:00,105 - __main__ - INFO - [agronomist] Tool called: google_search
2025-11-25 04:52:01,200 - __main__ - INFO - [STEP 5/5] ✓ Response sent successfully
```

### Error Case
```
2025-11-25 04:53:00,100 - __main__ - INFO - Received from 67890 (Jane): Calculate profit [Photo: False]
2025-11-25 04:53:00,101 - __main__ - INFO - [STEP 1/5] ✓ Session ID: def-456
2025-11-25 04:53:00,102 - __main__ - INFO - [STEP 2/5] No image attached
2025-11-25 04:53:00,103 - __main__ - INFO - [STEP 3/5] ✓ Orchestrator response received
2025-11-25 04:53:00,104 - __main__ - INFO - [STEP 4/5] ✓ Route: FINANCIAL_QUERY -> market_analyst
2025-11-25 04:53:00,105 - __main__ - ERROR - [STEP 5/5] ✗ Specialist query failed: API rate limit exceeded
Traceback (most recent call last):
  File "telegram_bot.py", line 305, in handle_message
    specialist_response = await self.query_specialist(...)
  ...
```

## Best Practices

1. **Monitor log file size**: Check regularly and rotate if needed
2. **Search before debugging**: Use grep to find patterns quickly
3. **Use tail -f during demos**: Keep logs visible in a separate terminal
4. **Backup logs after demos**: Save successful demo logs for reference
5. **Clear old logs periodically**: Keep only recent logs (7-30 days)

## Integration with External Tools

### Send logs to logging service
```bash
# Example: Ship logs to external service
tail -f telegram_bot.log | your-logging-service
```

### Parse logs for analytics
```python
import re
from collections import Counter

# Count routing decisions
with open('telegram_bot.log') as f:
    routes = re.findall(r'Route: (\w+)', f.read())
    print(Counter(routes))

# Count tool usage
with open('telegram_bot.log') as f:
    tools = re.findall(r'Tool called: (\w+)', f.read())
    print(Counter(tools))
```

## Troubleshooting

### Log file not created
- Check file permissions
- Ensure bot has write access to project directory
- Verify Path is correct in telegram_bot.py:41

### Log file too large
- Implement log rotation
- Reduce logging level (change INFO to WARNING)
- Clear old entries regularly

### Can't find specific logs
- Ensure correct timestamp format
- Use broader grep patterns
- Check if bot was restarted (creates new session IDs)
