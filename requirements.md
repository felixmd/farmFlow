FarmerPilot: Hackathon Requirements Document
Project: FarmerPilot (Google Agents Hackathon)

Goal: A multi-agent system aiding farmers with real-time agronomic advice and market analysis using Google Gemini.

Tech Stack: Python, Google Gen AI SDK, Telegram Bot API, FastHTML, DaisyUI, Google Cloud Run.

1. High-Level Architecture
The system follows a Hub-and-Spoke Multi-Agent architecture.

Primary Interface: Telegram Bot (mobile-first for farmers).

Admin Dashboard: FastHTML web interface (Python-based) styled with DaisyUI.

Orchestrator (The Hub): A central agent that routes user queries.

Specialist Agents (The Spokes):

Agronomist: Uses Google Search to find real-time pest/crop info.

Market Analyst: Uses Code Execution to calculate complex profit margins/Risk ROI.

Infrastructure: Deployed on Google Cloud Run as a containerized service.

2. Functional Requirements (FR)
FR-1: The User Interface

FR-1.1 (Primary): Telegram Bot interface for farmers
  - Mobile-first access via Telegram app
  - /start command with welcome message
  - Session memory per user
  - Typing indicators during processing
  - Markdown formatting for responses

FR-1.2 (Secondary): Web-based admin dashboard using FastHTML
  - Monitor agent conversations
  - Test agent functionality
  - Styled via DaisyUI (clean, responsive)

FR-1.3: Chat history display (Session memory) maintained per user.

FR-2: The Orchestrator Agent (The Brain)

Model: Gemini 1.5 Pro.

FR-2.1: Must classify user intent into: AGRONOMY_QUERY, FINANCIAL_QUERY, or GENERAL_CHAT.

FR-2.2: Must maintain conversation history (Session Memory) to handle follow-up questions.

FR-2.3: Routes the formatted query to the correct Sub-Agent.

FR-3: The Agronomist Agent (The Researcher)

Model: Gemini 1.5 Flash (for speed).

Tool: Google Search Tool (Built-in ADK/GenAI SDK).

FR-3.1: Receives queries about pests, weather impacts, or sowing times.

FR-3.2: Must use the Search Tool to find current real-world data (e.g., "Current tomato prices in Maharashtra").

FR-3.3: Synthesizes search results into a simple advice paragraph.

FR-4: The Market Analyst Agent (The Calculator)

Model: Gemini 1.5 Flash.

Tool: Code Execution Tool (Built-in ADK/GenAI SDK).

FR-4.1: Receives queries involving numbers (e.g., "If I plant 5 acres of cotton at ₹5000 cost, what is my ROI?").

FR-4.2: Must write and execute Python code to perform the calculation (ensures math accuracy).

FR-4.3: Returns the calculated result and the logic used.

FR-5: Agent Evaluation (Winning Criteria)

FR-5.1: Automated evaluation suite using adk eval or simple unit tests.

FR-5.2: Must test at least 10 scenarios (5 Agronomy, 5 Financial) to grade response quality.

3. Non-Functional Requirements (NFR)
NFR-1 (Deployment): Must be deployed to Google Cloud Run via a Docker container.

NFR-2 (Latency): Agents must respond within 10 seconds.

NFR-3 (Simplicity): No external databases. Use InMemorySession for the hackathon demo.

4. "Winnability" Checklist (Strict Adherence)
[ ] Multi-Agent: Yes (Orchestrator + 2 Sub-agents).

[ ] Tools: Yes (Google Search + Code Execution).

[ ] Gemini Powered: Yes (Pro & Flash).

[ ] Evaluations: Yes (Automated testing included).

[ ] Deployment: Yes (Cloud Run).