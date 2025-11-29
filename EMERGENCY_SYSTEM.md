# Human-in-the-Loop Livestock Emergency System

## Overview

The FarmBot emergency system enables expert veterinary review for serious livestock diseases that require immediate professional attention. When the AI detects a critical condition like FMD (Foot-and-Mouth Disease), it automatically pauses the farmer's interaction, escalates the case to expert veterinarians, and resumes the conversation once expert guidance is received.

## Architecture

### Components

1. **Livestock Specialist Agent** (`agents/livestock_agent/livestock.py`)
   - Expert veterinarian AI specializing in cattle, buffalo, goats, poultry
   - Vision-capable for analyzing animal images
   - Detects critical diseases requiring expert review
   - Returns structured emergency markers when serious conditions are found

2. **Emergency Case Manager** (`emergency_case_manager.py`)
   - Manages state machine for emergency cases
   - Persistent JSON storage (`emergency_cases.json`)
   - Tracks cases through: `pending_review` → `awaiting_vet` → `vet_responded` → `completed`

3. **Emergency Handler** (`emergency_handler.py`)
   - Detects `[EMERGENCY_VET_REVIEW_REQUIRED]` markers in livestock agent responses
   - Creates cases and posts to vet group
   - Extracts farmer-facing instructions
   - Manages case-to-session mapping

4. **Emergency Vet Bot** (`emergency_vet_bot.py`)
   - Separate Telegram bot posting to "Livestock Emergency" group
   - Listens for vet responses (via message replies or `/respond` command)
   - Updates case manager when vets provide guidance

5. **Main Bot Integration** (`telegram_bot.py`)
   - Emergency detection after livestock specialist responses
   - Background polling task (every 30s) checking for vet responses
   - Automatic farmer notification when vet responds

## Workflow

### Step 1: Farmer Interaction
```
Farmer: [Sends image of cow with blisters] "My cow is not eating"
Main Bot: Routes to Livestock Specialist Agent
```

### Step 2: AI Detection
```
Livestock Agent analyzes image:
- Detects blisters on mouth and tongue
- Identifies as Foot-and-Mouth Disease (FMD)
- High confidence critical disease
- Returns emergency marker in response
```

### Step 3: Case Creation & Pause
```
Main Bot:
1. Detects [EMERGENCY_VET_REVIEW_REQUIRED] marker
2. Extracts disease data (FMD, CRITICAL severity)
3. Creates case in emergency_case_manager.py
4. Notifies farmer: "Your case is under expert review"
5. Does NOT send full AI response
```

### Step 4: Vet Group Notification
```
Emergency Bot posts to vet group:
🚨 LIVESTOCK EMERGENCY CASE
Case #ABC123
Disease: Foot-and-Mouth Disease (FMD)
[Image of affected animal]
Farmer: John (ID: 123456)
Query: "My cow is not eating"

AI Analysis: Characteristic blisters on tongue...
```

### Step 5: Vet Response
```
Vet (in group): [Replies to case message]
"This is confirmed FMD. Immediate actions:
1. Isolate all animals
2. Report to district animal husbandry office
3. Do not move any animals for 21 days
4. Disinfect premises with 2% caustic soda..."
```

### Step 6: Automatic Farmer Notification
```
Background polling task (runs every 30s):
- Detects vet has responded to case ABC123
- Retrieves farmer's user ID and session
- Sends vet's guidance to farmer

Main Bot → Farmer:
"✅ Expert Veterinary Guidance Received
Case #ABC123
Expert Vet: Dr. Kumar

[Vet's full response]"
```

### Step 7: Case Completion
```
Case manager marks case as "completed"
Farmer can continue normal conversation
```

## Setup Instructions

### 1. Create Vet Emergency Group

1. Create a new Telegram group called "Livestock Emergency" (or any name)
2. Add expert veterinarians to the group
3. Add the Emergency Bot (`@YourEmergencyBotName`) to the group
4. Make the bot an admin (optional, for better reliability)

### 2. Get Vet Group Chat ID

**Method 1: Using @userinfobot**
```
1. Add @userinfobot to your vet group
2. It will show the group chat ID (e.g., -1001234567890)
3. Copy this ID
```

**Method 2: From bot logs**
```
1. Send any message in the vet group
2. Check emergency_vet_bot.py logs
3. The chat_id will be logged
```

### 3. Update .env File

```bash
# Add to .env
VET_GROUP_CHAT_ID=-1001234567890
```

### 4. Start Both Bots

**Terminal 1: Main Farmer Bot**
```bash
source .venv/bin/activate
python telegram_bot.py
```

**Terminal 2: Emergency Vet Bot**
```bash
source .venv/bin/activate
python emergency_vet_bot.py
```

## Testing the System

### Test Case 1: Simulated FMD Emergency

1. Send this message to the main bot with an animal image:
   ```
   My cow has blisters on her mouth and is drooling excessively
   ```

2. **Expected Flow:**
   - Livestock agent detects potential FMD
   - Returns `[EMERGENCY_VET_REVIEW_REQUIRED]` marker
   - Main bot creates case (e.g., #ABC123)
   - Main bot notifies you: "🚨 URGENT: Serious Condition Detected..."
   - Emergency bot posts to vet group with case details

3. **Vet Response:**
   - In vet group, reply to the bot's message:
     ```
     Confirmed FMD. Isolate immediately and report to authorities.
     ```

4. **Automatic Farmer Notification:**
   - Within 30 seconds, you receive:
     ```
     ✅ Expert Veterinary Guidance Received
     Case ID: #ABC123
     Expert Vet: Dr. [Name]
     [Vet's response]
     ```

### Test Case 2: Non-Emergency Livestock Query

1. Send:
   ```
   My buffalo's milk production has decreased slightly
   ```

2. **Expected:**
   - Livestock agent provides standard advice
   - No emergency marker
   - Normal response sent to farmer

## Emergency Diseases (Auto-Escalation)

The livestock agent is configured to escalate these diseases:

- **Foot-and-Mouth Disease (FMD)** - Highly contagious, reportable
- **Anthrax** - Fatal, zoonotic
- **Blackleg (Black Quarter)** - Rapidly fatal
- **Brucellosis** - Zoonotic, causes abortions
- **Rabies** - Fatal, zoonotic
- **Bluetongue** - Viral, can be fatal

## Monitoring & Debugging

### View Active Cases

**Using Emergency Vet Bot:**
```
/stats - Show all case statistics
/active - Show active emergency cases
```

### Check Case Storage
```bash
cat emergency_cases.json | python -m json.tool
```

### View Logs
```bash
# Main bot logs
tail -f telegram_bot.log | grep EMERGENCY

# Vet bot logs (if running in terminal)
# Check terminal output for vet bot
```

### Common Issues

**Issue: Vet group not receiving cases**
```
Solution:
1. Verify VET_GROUP_CHAT_ID is correct
2. Ensure emergency bot is in the group
3. Check emergency_vet_bot.py logs for errors
```

**Issue: Farmer not getting vet responses**
```
Solution:
1. Check main bot logs for polling errors
2. Verify case status in emergency_cases.json
3. Ensure vet replied to the bot's message (not a new message)
```

**Issue: Emergency not detected**
```
Solution:
1. Check if query mentions animal keywords
2. Verify orchestrator routes to livestock_specialist
3. Check livestock agent response for emergency marker
```

## Vet Commands

Vets in the emergency group can respond in two ways:

**Method 1: Reply to Message** (Recommended)
```
[Reply directly to the case message with diagnosis]
```

**Method 2: Use Command**
```
/respond ABC123 This is FMD. Isolate immediately...
```

## Session Persistence

- Cases are stored in `emergency_cases.json`
- Survives bot restarts
- Farmers can be notified even if they restart their conversation
- Uses farmer's `user_id` for reliable delivery

## Limitations

1. **No True Pause/Resume**: Google ADK doesn't support native pause/resume, so we simulate it with state storage
2. **Manual Polling**: Checks every 30 seconds for vet responses (not real-time)
3. **Single Vet Group**: Currently supports one vet group; multiple groups would require configuration changes
4. **In-Memory Sessions**: Session service is in-memory; long-running cases might lose context if bot restarts

## Future Enhancements

- [ ] Multiple vet groups by disease type
- [ ] Vet acknowledgment tracking
- [ ] Case escalation if no vet response in X minutes
- [ ] SMS/WhatsApp notifications for critical cases
- [ ] Persistent session storage (database)
- [ ] Case analytics and reporting
- [ ] Vet response time SLAs

## File Reference

| File | Purpose |
|------|---------|
| `agents/livestock_agent/livestock.py` | Livestock specialist AI agent |
| `emergency_case_manager.py` | State machine & persistent storage |
| `emergency_handler.py` | Emergency detection & vet posting |
| `emergency_vet_bot.py` | Vet group Telegram bot |
| `telegram_bot.py` | Main bot with emergency integration |
| `emergency_cases.json` | Case storage (gitignored) |
| `agents/orchestrator/orchestrator.py` | Updated with livestock routing |

## Support

For issues or questions:
1. Check logs: `telegram_bot.log`
2. Review case storage: `emergency_cases.json`
3. Test emergency bot separately: `python emergency_vet_bot.py`
4. Verify environment variables in `.env`
