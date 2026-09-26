# ResolveFlow ⚖️

> **Autonomous Multi-Agent Dispute Resolution & Reconciliation Engine with Enterprise Human-in-the-Loop (HITL) Governance.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00.svg?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Validation-Pydantic%20v2-E92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![PostgreSQL](https://img.shields.io/badge/State%20Persistence-PostgreSQL%20%2B%20PgSaver-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Slack Block Kit](https://img.shields.io/badge/HITL-Slack%20Block%20Kit-4A154B.svg?logo=slack&logoColor=white)](https://api.slack.com/block-kit)
[![Region](https://img.shields.io/badge/Deployment-AWS%20ap--southeast--2%20(Sydney)-232F3E.svg?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

---

## 🎯 Executive Summary & Market Fit

Australian FinTech scale-ups (e.g., **Airwallex**, **Afterpay / Block**, **Zip**) and tier-1 e-commerce platforms process tens of thousands of customer disputes, transaction reconciliations, and chargebacks weekly.

Resolving a single dispute typically requires an operations analyst to pivot across multiple disjointed systems:
- **Payment Gateways:** Stripe, Adyen, Basiq (Payment intents, refunds, card dispute logs)
- **Logistics & Delivery:** Australia Post, StarTrack API (Proof of delivery, transit milestones, signature receipts)
- **CRM & Case Management:** Zendesk, Salesforce, HubSpot (Customer lifetime value, prior dispute history)
- **Core Banking / Internal Databases:** PostgreSQL/Aurora ledger records

While multi-agent automation can save millions in operational overhead, **no Australian bank or regulated enterprise will allow an AI to unilaterally issue a $1,000 AUD refund or suspend an account without human governance**. 

**ResolveFlow** bridges this enterprise dilemma by orchestrating autonomous investigation while enforcing deterministic **Human-in-the-Loop (HITL) state interrupts** via persistent LangGraph checkpointers and Slack Ops approvals before any destructive action is taken.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A([📩 Incoming Dispute Ticket / Email]) --> B[1. Triager Agent<br/><i>Pydantic v2 Parsing & Intent Extraction</i>]
    B --> C[2. Forensics Agent<br/><i>Stripe, AusPost & Core DB Integration</i>]
    C --> D[3. Risk & Policy Agent<br/><i>Dispute Policy Matrix & Scoring</i>]
    
    D --> E{Is Refund > AUD $100<br/>OR High Risk?}
    
    E -- YES --> F[⏸️ <b>LangGraph Checkpointer Interrupt</b><br/><i>State Persisted to PostgreSQL</i>]
    F --> G[💬 Interactive Slack Block Kit Card<br/><i>Sent to #ops-approvals</i>]
    G --> H([👤 Operations Manager Review<br/>Approve | Reject | Modify])
    H --> I[⚡ FastAPI Webhook Listener<br/><i>graph.update_state and resume</i>]
    I --> J[5. Settlement Agent<br/><i>Executes Stripe Refund & DB Ledger Update</i>]
    
    E -- NO (Safe Auto-Policy) --> J
    
    J --> K([📤 Customer Communication & Ticket Resolution])

    classDef agent fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#fff;
    classDef hitl fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#fff;
    classDef decision fill:#312e81,stroke:#818cf8,stroke-width:2px,color:#fff;
    classDef io fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#fff;

    class B,C,D,J agent;
    class F,G,H,I hitl;
    class E decision;
    class A,K io;
```

---

## 🤖 Agent Roles & Responsibilities

| # | Agent Name | Core Responsibilities | Tool Integrations & Schemas |
|---|---|---|---|
| **1** | **Intake & Triage Agent** | Ingests raw dispute emails, Zendesk webhooks, or API requests. Sanitizes PII and parses unstructured claims into strictly typed schemas. | `DisputeTicket` Pydantic model (`transaction_id`, `customer_email`, `claim_type`, `amount_aud`, `evidence_notes`) |
| **2** | **Forensics & Tool Agent** | Queries payment rails, postal logistics, and customer ledger databases concurrently to build a comprehensive dispute evidence package. | `get_transaction_status(transaction_id)`<br/>`get_delivery_proof(tracking_number)`<br/>`get_customer_lifetime_value(customer_id)` |
| **3** | **Risk & Policy Evaluator** | Applies internal risk matrices and business policies against forensics data. Computes risk scores and proposes an action (`REJECT`, `PARTIAL_REFUND`, `FULL_REFUND`). | Policy Evaluation Matrix, chargeback velocity tracking, anomalous delivery location analysis |
| **4** | **HITL Gatekeeper** *(The Showstopper)* | Enforces deterministic breakpoints if proposed action exceeds financial thresholds (> $100 AUD) or flags high risk. Suspends execution graph and dispatches Slack interactive actions. | LangGraph `interrupt_before=["execute_settlement"]`, PostgreSQL Checkpointer, Slack Block Kit |
| **5** | **Settlement & Communication Agent** | Resumes graph execution post-approval. Triggers payment gateway refund APIs, updates database ledger, and drafts empathetic, legally compliant customer correspondence. | `stripe.Refund.create()`, PostgreSQL status updates, localized email/ticket response generator |

---

## 🛡️ The HITL Gatekeeper: How Pause & Resume Works

When high-value or high-risk claims are processed, ResolveFlow's LangGraph pipeline executes an interrupt:

1. **State Freezing:** LangGraph halts at `interrupt_before=["execute_settlement"]`. The execution thread state is written into PostgreSQL via `PostgresSaver`.
2. **Slack Block Kit Notification:** A rich card is pushed to `#ops-approvals`:
   ```text
   🚨 Dispute Approval Request #DISP-9821
   ──────────────────────────────────────────────────────
   Customer:      Jane Doe (CLV: $3,450 AUD | 4 orders)
   Claim Amount:  $285.00 AUD (Claim: "Never received goods")
   Forensics:     AusPost confirms delivery to 3000 Melbourne with signature.
   Risk Finding:  High risk - Signature matched delivery profile.
   AI Suggestion: REJECT DISPUTE
   ──────────────────────────────────────────────────────
   [ Approve Refund ]   [ Reject Dispute ]   [ Request More Info ]
   ```
3. **Deterministic Resumption:** The manager clicks an action in Slack. The Slack interaction webhook hits FastAPI (`/api/v1/slack/interactions`), which invokes:
   ```python
   graph.update_state(config, {"human_decision": "REJECT", "reviewer_id": "U123456"})
   graph.invoke(None, config=config)  # Resumes from checkpoint
   ```

---

## 🔒 Enterprise Data Privacy & APP Compliance

Operating in Australia requires strict adherence to the **Australian Privacy Principles (APP)** under the *Privacy Act 1988*:

- **PII Masking & Sanitization:** Credit card numbers (PAN), CVVs, and raw customer address lines are scrubbed before LLM prompt assembly.
- **Data Sovereignty:** Deployed to AWS Region `ap-southeast-2` (Sydney) with PostgreSQL encryption-at-rest (`AES-256`) and TLS 1.3 in transit.
- **Full Auditability:** Every tool invocation, LLM completion, and human review decision is recorded with deterministic replay hashes for regulatory compliance.

---

## 🧰 Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Agent Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) | State-graph orchestration with native checkpointing and interrupt mechanisms |
| **Data Schemas** | [Pydantic v2](https://docs.pydantic.dev/) | Strict typing, schema validation, and tool argument contracts |
| **API Layer** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn | Async REST API for ticket ingestion and Slack interactive webhooks |
| **State Persistence** | PostgreSQL + `PostgresSaver` | Thread checkpointing ensuring state persistence across restarts |
| **Payment Integration** | Stripe Python SDK | Mock/Test mode transaction forensics and refund execution |
| **Logistics Integration** | Australia Post Mock API | AusPost delivery milestones, tracking events, and signature verification |
| **Observability** | [Langfuse](https://langfuse.com/) / [Arize Phoenix](https://phoenix.arize.com/) | Trace logs, token cost accounting, latency profiling, and evaluation |
| **Containerization & Cloud** | Docker, AWS ECS / App Runner | Sydney (`ap-southeast-2`) containerized deployment |

---

## 📂 Repository Structure

```text
ResolveFlow/
├── api/                        # FastAPI endpoints and webhook handlers
│   ├── routes/
│   │   ├── disputes.py         # Ingestion endpoints
│   │   └── slack.py            # Slack Block Kit interaction webhooks
│   └── main.py                 # FastAPI application factory
├── agents/                     # LangGraph agent nodes & graph definition
│   ├── triage_agent.py         # Ticket intake and Pydantic parsing
│   ├── forensics_agent.py      # Multi-tool evidence gatherer
│   ├── policy_agent.py         # Risk policy matrix evaluator
│   ├── hitl_gatekeeper.py      # Slack dispatch and checkpoint manager
│   ├── settlement_agent.py     # Stripe refund and customer response
│   └── graph.py                # LangGraph StateGraph assembly
├── core/                       # Core configuration & persistence
│   ├── config.py               # Pydantic BaseSettings
│   ├── database.py             # PostgreSQL async connection
│   └── checkpointer.py         # PostgresSaver configuration
├── schemas/                    # Pydantic v2 data models
│   ├── ticket.py               # DisputeTicket & Claim schemas
│   ├── forensics.py            # AusPost & Stripe response models
│   └── state.py                # GraphState definition
├── tools/                      # Tool definitions & API integrations
│   ├── auspost_tool.py         # Australia Post tracking & signature mock
│   ├── stripe_tool.py          # Stripe payment forensics & refund mock
│   └── crm_tool.py             # Customer lifetime value & history tool
├── tests/                      # Pytest suite with end-to-end graph tests
│   ├── test_triage.py
│   ├── test_forensics.py
│   └── test_hitl_workflow.py
├── docker-compose.yml          # Local PostgreSQL, Mock APIs, and App stack
├── Dockerfile                  # Production container image
├── pyproject.toml              # Dependencies and project metadata
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Docker & Docker Compose**
- **PostgreSQL 15+** (or run via docker-compose)
- OpenAI / Anthropic API Key
- Slack App with incoming webhooks and interactive components enabled (optional for mock mode)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/KumarDhananjaya/ResolveFlow.git
cd ResolveFlow

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```ini
# App Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# PostgreSQL State Persistence
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resolveflow

# Slack Integration (HITL)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_OPS_CHANNEL=C0123456789

# Payment Rails & Logistics
STRIPE_API_KEY=sk_test_mock
AUSPOST_API_KEY=mock_auspost_key

# Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### 3. Run with Docker Compose

```bash
docker-compose up --build -d
```

### 4. Ingest a Test Dispute

```bash
curl -X POST http://localhost:8000/api/v1/disputes/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "jane.doe@example.com.au",
    "transaction_id": "ch_3N8au82eZvKYlo2C1g9X8xYz",
    "tracking_number": "AP982347102AU",
    "amount_aud": 285.00,
    "claim_type": "ITEM_NOT_RECEIVED",
    "evidence_notes": "Customer states parcel was not delivered to their Melbourne address."
  }'
```

---

## 📊 Observability & Traceability

ResolveFlow integrates with **Langfuse** / **Arize Phoenix** to provide deep telemetry across every step of agent execution:
- **Trace Graphs:** Full step-by-step visibility into tool inputs, outputs, and intermediate thoughts.
- **Latency & Token Tracking:** Real-time visibility into prompt/completion token usage and cost per dispute.
- **HITL Latency Metrics:** Tracking operational review turnaround times from pause to resume.

---

## 📄 License

Distributed under the Apache 2.0 License. See `LICENSE` for more information.
