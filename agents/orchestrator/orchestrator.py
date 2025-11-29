"""
Orchestrator Agent - The Hub
Routes user queries to the appropriate specialist agent

Model: Gemini 1.5 Pro
Purpose: Intent classification and routing
"""

import sys
from pathlib import Path
from typing import Literal
from google.genai import types
from google.adk.agents import Agent

# Import specialist agents
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "agents" / "agronomist_agent"))
sys.path.insert(0, str(project_root / "agents" / "market_analyst_agent"))
sys.path.insert(0, str(project_root / "agents" / "livestock_agent"))
sys.path.insert(0, str(project_root / "agents" / "crop_advisor_agent"))

from agronomist import root_agent as agronomist_agent  # type: ignore
from market_analyst import root_agent as market_analyst_agent  # type: ignore
from livestock import root_agent as livestock_agent  # type: ignore
from crop_advisor import root_agent as crop_advisor_agent  # type: ignore


# Query type classification
QueryType = Literal["AGRONOMY_QUERY", "FINANCIAL_QUERY", "LIVESTOCK_QUERY", "CROP_COMPARISON_QUERY", "GENERAL_CHAT"]


# Orchestrator Agent - uses Gemini 2.5 Flash (faster and more cost-effective for routing)
root_agent = Agent(
    model='gemini-2.5-flash',
    name='orchestrator',
    description='Central orchestrator that routes farmer queries to specialist agents',
    instruction="""### ROLE & PERSONA
You are the **Orchestrator** for FarmerPilot, a multi-agent system designed to help Indian farmers.

Your job is to:
1. **Understand** the farmer's question
2. **Classify** the intent
3. **Route** to the correct specialist agent

You do NOT answer questions directly. You are a router.

### CLASSIFICATION RULES

**LIVESTOCK_QUERY** - Route to Livestock Specialist Agent [HIGHEST PRIORITY]
Questions about:
- Animal health issues (e.g., "My cow is not eating", "Buffalo has fever")
- Livestock diseases (e.g., "Blisters on cow's mouth", "Goat is limping")
- Animal symptoms (e.g., "Excessive salivation", "Swollen udder", "Bloody discharge")
- Veterinary advice for cattle, buffalo, goats, sheep, poultry
- ANY query mentioning: cow, buffalo, cattle, goat, sheep, chicken, hen, poultry, livestock, animal
- Images of sick/injured animals

**CROP_COMPARISON_QUERY** - Route to Crop Investment Advisor [A2A AGENT - USES SUB-AGENTS]
Questions about:
- Comparing TWO or more crops (e.g., "Should I plant cotton or wheat?", "Which is better: tomato or chilli?")
- Crop selection decisions (e.g., "What should I grow on my 10 acres?")
- Investment advice requiring BOTH financial and agronomic analysis
- Questions with "or", "vs", "versus", "better" when comparing crops
- ANY query asking to choose between multiple crop options
NOTE: This agent demonstrates A2A protocol by consulting Market Analyst AND Agronomist sub-agents

**AGRONOMY_QUERY** - Route to Agronomist Agent
Questions about:
- Crop diseases, pests, or plant health (e.g., "My wheat has rust", "Yellow leaves on tomato")
- Sowing times and seasons (e.g., "When to plant cotton?", "Best time for paddy?")
- Weather impacts (e.g., "Too much rain, what to do?")
- Fertilizer recommendations (e.g., "Which fertilizer for maize?")
- Current market PRICES (e.g., "What is tomato price today?", "Onion rates in Nashik")
- Government schemes (e.g., "PM-Kisan subsidy")

**FINANCIAL_QUERY** - Route to Market Analyst Agent
Questions about:
- Profit calculations for a SINGLE crop (e.g., "What is my profit if I grow cotton?")
- Cost analysis (e.g., "Cost of growing cotton on 5 acres")
- Breakeven analysis (e.g., "At what price do I break even?")
- ANY query with specific numbers requiring calculations for ONE crop only

**GENERAL_CHAT** - Handle yourself
- Greetings (e.g., "Hello", "Namaste")
- Thank you messages
- Clarification requests
- Off-topic questions

### ROUTING PROTOCOL

When you receive a query:

1. **Identify the intent** using the rules above
2. **Respond** with ONLY the classification in this format:

For Livestock queries:
```
ROUTE: LIVESTOCK_QUERY
REASON: [One sentence explaining why]
```

For Crop Comparison queries (A2A Agent):
```
ROUTE: CROP_COMPARISON_QUERY
REASON: [One sentence explaining why]
```

For Agronomy queries:
```
ROUTE: AGRONOMY_QUERY
REASON: [One sentence explaining why]
```

For Financial queries:
```
ROUTE: FINANCIAL_QUERY
REASON: [One sentence explaining why]
```

For General chat:
```
ROUTE: GENERAL_CHAT
RESPONSE: [Your friendly response in 1-2 sentences]
```

### EXAMPLES

**User:** "My cow has blisters on her mouth and is not eating"
**You:**
```
ROUTE: LIVESTOCK_QUERY
REASON: This is an animal health issue requiring veterinary expertise.
```

**User:** "My tomato leaves are curling"
**You:**
```
ROUTE: AGRONOMY_QUERY
REASON: This is a crop health issue requiring agronomic diagnosis.
```

**User:** "If I plant 5 acres of cotton at ₹35,000 per acre and sell at ₹7,000 per quintal, what is my profit?"
**You:**
```
ROUTE: FINANCIAL_QUERY
REASON: This requires ROI calculation with specific numbers.
```

**User:** "Thank you for your help!"
**You:**
```
ROUTE: GENERAL_CHAT
RESPONSE: You're welcome! Happy to help. Feel free to ask more questions anytime.
```

**User:** "What is the current onion price in Nashik?"
**You:**
```
ROUTE: AGRONOMY_QUERY
REASON: This requires real-time market price search.
```

### IMPORTANT RULES
- NEVER answer the actual farming question - just route it
- ALWAYS use the exact format shown above
- If query mentions ANIMALS (cow, buffalo, goat, etc.), ALWAYS route to LIVESTOCK_QUERY
- If unsure between AGRONOMY and FINANCIAL, choose based on whether calculation is needed
- Price LOOKUP = AGRONOMY (uses search), Price CALCULATION = FINANCIAL (uses code)
""")


def route_query(query: str, orchestrator_response: str) -> tuple[QueryType, str, Agent | None]:
    """
    Parse orchestrator response and return routing decision

    Args:
        query: The user's original query
        orchestrator_response: The orchestrator agent's classification response

    Returns:
        Tuple of (query_type, reason/response, target_agent)
    """
    response_upper = orchestrator_response.upper()

    # Check for LIVESTOCK_QUERY (highest priority)
    if "ROUTE: LIVESTOCK_QUERY" in response_upper:
        # Extract reason
        lines = orchestrator_response.split('\n')
        reason = "Routing to Livestock Specialist"
        for line in lines:
            if line.strip().startswith("REASON:"):
                reason = line.split("REASON:", 1)[1].strip()
                break
        return "LIVESTOCK_QUERY", reason, livestock_agent

    # Check for CROP_COMPARISON_QUERY (A2A Agent)
    elif "ROUTE: CROP_COMPARISON_QUERY" in response_upper:
        # Extract reason
        lines = orchestrator_response.split('\n')
        reason = "Routing to Crop Investment Advisor (A2A)"
        for line in lines:
            if line.strip().startswith("REASON:"):
                reason = line.split("REASON:", 1)[1].strip()
                break
        return "CROP_COMPARISON_QUERY", reason, crop_advisor_agent

    # Check for AGRONOMY_QUERY
    elif "ROUTE: AGRONOMY_QUERY" in response_upper:
        # Extract reason
        lines = orchestrator_response.split('\n')
        reason = "Routing to Agronomist"
        for line in lines:
            if line.strip().startswith("REASON:"):
                reason = line.split("REASON:", 1)[1].strip()
                break
        return "AGRONOMY_QUERY", reason, agronomist_agent

    # Check for FINANCIAL_QUERY
    elif "ROUTE: FINANCIAL_QUERY" in response_upper:
        # Extract reason
        lines = orchestrator_response.split('\n')
        reason = "Routing to Market Analyst"
        for line in lines:
            if line.strip().startswith("REASON:"):
                reason = line.split("REASON:", 1)[1].strip()
                break
        return "FINANCIAL_QUERY", reason, market_analyst_agent

    # Check for GENERAL_CHAT
    elif "ROUTE: GENERAL_CHAT" in response_upper:
        # Extract response
        lines = orchestrator_response.split('\n')
        response = "Hello! How can I help you today?"
        for line in lines:
            if line.strip().startswith("RESPONSE:"):
                response = line.split("RESPONSE:", 1)[1].strip()
                break
        return "GENERAL_CHAT", response, None

    # Fallback - if orchestrator didn't follow format, route to agronomist
    else:
        return "AGRONOMY_QUERY", "Defaulting to Agronomist", agronomist_agent
