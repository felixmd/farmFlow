# FarmFlow: AI-Powered Agricultural Assistant
**Track:** Agents for Good

## Problem
Smallholder farmers often lack access to timely, expert advice. Critical decisions about crop selection, pest management, and livestock health are often made with incomplete information, leading to financial loss and food insecurity. Traditional extension services are resource-constrained and cannot provide 24/7 personalized support.

## Solution
FarmFlow is a multi-agent AI system accessible via Telegram, the platform farmers already use. It orchestrates specialized AI agents to provide expert-level guidance on agronomy, market economics, and veterinary care. Unlike simple chatbots, FarmFlow uses a **Human-in-the-Loop** architecture for critical emergencies and **Agent-to-Agent (A2A)** protocols for complex decision-making.

## Architecture

### High-Level System Design
The system uses a hub-and-spoke architecture where an **Orchestrator Agent** routes user queries to specialized agents.

```mermaid
graph TD
    User((User)) -->|Telegram| Bot[Telegram Bot]
    Bot -->|Session| Orch[Orchestrator Agent]
    
    Orch -->|Routing| Router{Query Type}
    
    Router -->|Crop Disease| Agro[Agronomist Agent]
    Router -->|Prices/ROI| Market[Market Analyst Agent]
    Router -->|Animal Health| Vet[Livestock Specialist]
    Router -->|Strategy| CropAdv[Crop Advisor Agent]
    
    Agro -->|Tool| Memory[Memory Bank\nPesticide Safety]
    Market -->|Tool| Code[Code Execution\nFinancial Math]
    
    Vet -->|Emergency| Emergency[Emergency Handler]
    Emergency -->|Firestore| DB[(Firestore)]
    Emergency -->|Alert| HumanVet[Vet Group]
```

## Key Technical Features

### 1. Agent-to-Agent (A2A) Protocol
For complex strategic questions (e.g., "Should I plant cotton or wheat?"), a single agent is insufficient. We implemented an **A2A** pattern where the `Crop Advisor` acts as a manager, delegating sub-tasks to other agents.

*   **Scenario**: User asks for a crop recommendation.
*   **Flow**:
    1.  `Crop Advisor` receives the query.
    2.  Calls `Market Analyst` (via tool) to get current prices and ROI.
    3.  Calls `Agronomist` (via tool) to check soil/climate suitability.
    4.  Synthesizes both responses into a final recommendation.

```mermaid
sequenceDiagram
    participant User
    participant Advisor as Crop Advisor
    participant Market as Market Analyst
    participant Agro as Agronomist
    
    User->>Advisor: "Cotton vs Wheat?"
    Advisor->>Market: get_market_data(cotton, wheat)
    Market-->>Advisor: ROI Analysis (Cotton +60%)
    Advisor->>Agro: get_growing_reqs(cotton, wheat)
    Agro-->>Advisor: Soil/Climate Data
    Advisor->>User: Synthesized Recommendation
```

### 2. Tools & Code Execution
LLMs are notoriously bad at math. To ensure accurate financial advice, the `Market Analyst` agent does not calculate ROI in its head. Instead, it uses a **Code Execution Tool** (Python REPL) to perform arithmetic operations, ensuring 100% accuracy for profit/loss projections.

### 3. Human-in-the-Loop (Emergency Escalation)
AI should not handle life-or-death situations alone. We implemented a robust escalation flow for livestock emergencies.

*   **Detection**: The `Livestock Specialist` analyzes queries for severity markers (e.g., "bleeding", "not eating").
*   **Persistence**: Emergency cases are stored in **Google Cloud Firestore** to ensure state survives container restarts.
*   **Escalation**: High-severity cases are automatically posted to a dedicated **Vet Group** on Telegram.
*   **Feedback Loop**: When a human vet replies in the group, the bot polls the update, matches it to the case ID, and forwards the expert advice back to the farmer.

### 4. Memory & Context Management
*   **Memory Bank**: The `Agronomist` agent has access to a static "Memory Bank" of pesticide safety guidelines, ensuring it always provides safe chemical handling advice without hallucinations.
*   **Context Compaction**: To handle long conversations without hitting token limits or confusing the model, the `Market Analyst` uses **Context Compaction**, summarizing older turns while keeping recent financial context intact.

### 5. Deployment & Observability
*   **Compute**: Google Cloud Run (Serverless).
*   **Mode**: Webhooks (for low latency and scalability).
*   **Database**: Firestore (Native Mode).
*   **Observability**: All agent activities, tool calls, and routing decisions are logged to **Cloud Logging** using structured JSON logs.

## Tool Usage & Scenarios
The following diagram illustrates how different agents leverage specific tools to solve distinct user problems.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'edgeLabelBackground': '#ffffff', 'tertiaryColor': '#ffffff', 'clusterBkg': '#ffffff', 'clusterBorder': '#bdc3c7', 'lineColor': '#7f8c8d'}}}%%
graph TD
    %% Force vertical layout with invisible edges
    Financial ~~~ Safety ~~~ Emergency ~~~ Strategy

    subgraph Financial["1. Profit Calculation"]
        direction LR
        MA[Market Analyst] -->|Generates Python| Code[Code Execution Tool]
        Code -->|Returns Result| MA
    end

    subgraph Safety["2. Pesticide Advice"]
        direction LR
        Agro[Agronomist] -->|Queries| Mem[Memory Bank]
        Mem -->|Returns Guidelines| Agro
    end

    subgraph Emergency["3. Livestock Disease"]
        direction LR
        Vet[Livestock Specialist] -->|Detects Severity| Handler[Emergency Handler]
        Handler -->|Persists| DB[(Firestore)]
        Handler -->|Alerts| Group[Vet Group Chat]
    end
    
    subgraph Strategy["4. Crop Selection"]
        direction LR
        Advisor[Crop Advisor] -->|Delegates| T1[Tool: Market Analyst]
        Advisor -->|Delegates| T2[Tool: Agronomist]
    end
    
    %% Corporate Styling
    classDef agent fill:#ffffff,stroke:#2c3e50,stroke-width:2px;
    classDef tool fill:#ecf0f1,stroke:#7f8c8d,stroke-width:1px;
    classDef db fill:#ffffff,stroke:#e67e22,stroke-width:2px;
    classDef ext fill:#ffffff,stroke:#27ae60,stroke-width:2px;
    
    class MA,Agro,Vet,Advisor,Handler agent;
    class Code,Mem,T1,T2 tool;
    class DB db;
    class Group ext;
    
    %% Subgraph Styling
    style Financial fill:#ffffff,stroke:#bdc3c7,stroke-width:1px,stroke-dasharray: 5 5
    style Safety fill:#ffffff,stroke:#bdc3c7,stroke-width:1px,stroke-dasharray: 5 5
    style Emergency fill:#ffffff,stroke:#bdc3c7,stroke-width:1px,stroke-dasharray: 5 5
    style Strategy fill:#ffffff,stroke:#bdc3c7,stroke-width:1px,stroke-dasharray: 5 5

    %% Connector Styling
    linkStyle default stroke:#7f8c8d,stroke-width:1px;
```

## Evaluations
We used `google-adk` to rigorously evaluate our agents before deployment.
*   **Rubrics**: Defined specific criteria (e.g., "Financial Accuracy", "Safety Compliance").
*   **EvalSets**: Created dataset of test cases (`evals/data/`).
*   **Results**:
    *   Market Analyst: **PASSED** (Verified math accuracy).
    *   Agronomist: **PASSED** (Verified safety guidelines).
    *   Crop Advisor (A2A): **PASSED** (Verified tool usage and synthesis).

## Setup & Reproduction

### Prerequisites
*   Python 3.11+
*   Google Cloud Project with Vertex AI enabled
*   Telegram Bot Token

### Local Development
1.  Clone the repository.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Set environment variables in `.env`:
    ```bash
    TELEGRAM_TOKEN=your_main_bot_token
    TELEGRAM_TOKEN_EMERGENCY_BOT=your_emergency_bot_token
    GOOGLE_API_KEY=your_gemini_key
    GOOGLE_CLOUD_PROJECT=your_project
    GOOGLE_CLOUD_LOCATION=us-central1
    VET_GROUP_CHAT_ID=-100xxxxxxxxx  # Group ID for vet alerts
    GOOGLE_GENAI_USE_VERTEXAI=true
    AGENT_ENGINE_ID=your_agent_engine_id
    ```
4.  Run the bot: `python telegram_bot.py`

### Cloud Deployment
1.  **Build**: `gcloud builds submit --tag gcr.io/PROJECT_ID/farmflow`
2.  **Deploy**:
    ```bash
    gcloud run deploy farmflow \
      --image gcr.io/PROJECT_ID/farmflow \
      --set-env-vars "MODE=WEBHOOK,WEBHOOK_URL=https://your-service-url" \
      --set-env-vars "TELEGRAM_TOKEN=...,TELEGRAM_TOKEN_EMERGENCY_BOT=..." \
      --set-env-vars "GOOGLE_API_KEY=...,GOOGLE_CLOUD_PROJECT=..." \
      --set-env-vars "VET_GROUP_CHAT_ID=...,GOOGLE_GENAI_USE_VERTEXAI=true"
    ```
