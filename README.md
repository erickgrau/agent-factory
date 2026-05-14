# Agent Factory 🏭

Mission Control for AI Agent Teams

> A local-first, open-source platform for managing AI agents across multiple LLM providers with cost tracking, team collaboration, and human-in-the-loop approval gates.

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/agent-factory.git ~/Repos/agent-factory
cd ~/Repos/agent-factory
pip install -e .

# Set environment variables
export ANTHROPIC_API_KEY=your_key_here
export DISCORD_BOT_TOKEN=your_token_here

# Start using
python -m agent_factory create "Implement user authentication with JWT"
```

## ✨ Features

- 🤖 **Multi-Model Support** — Ollama (local), Claude, Codex, Gemini, HuggingFace, Groq
- 💰 **Cost Tracking** — Daily/task budgets with alerts
- 👥 **Team Collaboration** — Discord integration, role-based permissions
- 🔄 **Human-in-the-Loop** — Approval gates at critical transitions
- 📊 **Mission Control Dashboard** — Real-time task queue and metrics
- 🔌 **OpenClaw Integration** — Skills for seamless AI assistant workflow

## 🏗️ Architecture

```
Agent Factory
├── Core Engine
│   ├── Task Manager (Markdown storage)
│   ├── State Machine (7 states, approval gates)
│   ├── Model Router (cost-aware selection)
│   └── Cost Tracker (budgets & alerts)
├── Plugins
│   └── Discord Bot (notifications & approvals)
├── Skills
│   ├── task-create
│   ├── task-implement
│   └── task-review
└── Web Dashboard (Phase 3)
```

## 📋 Task States

```
backlog → spec-defined → plan-approved → in-progress → needs-review → approved → done
   ↑_________↓______________↓________________↓_________________↓____________↓
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Ollama (optional, for local models)
- Discord bot token (optional, for notifications)

### Environment Variables

Create `.env` file:

```bash
# LLM Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Discord (optional)
DISCORD_BOT_TOKEN=...
DISCORD_CHANNEL_ID=...

# Storage
AGENT_FACTORY_DATA_PATH=~/Repos/agent-factory-data
```

## 🎯 Usage

### Command Line

```bash
# Create a task
agent-factory create "Implement payment gateway with Stripe"

# List tasks
agent-factory list --state in-progress

# Check costs
agent-factory costs --today

# Start dashboard
agent-factory dashboard
```

### Python API

```python
from agent_factory import TaskManager, ModelRouter

tasks = TaskManager()
router = ModelRouter()

# Create task
task = tasks.create_task(
    title="Implement auth",
    description="Add JWT authentication",
    acceptance_criteria=["Login works", "Tokens refresh"]
)

# Select best model
model_id = router.select_model(
    complexity=4,
    budget_remaining=5.0
)
```

### OpenClaw Integration

```python
# In OpenClaw:
"Create a task to refactor the database layer"
"What's the status of task #0001?"
"Show me today's costs"
```

## 📁 Repository Structure

```
agent-factory/
├── src/
│   ├── core/           # Core engine
│   ├── plugins/        # Discord, Slack, etc.
│   ├── skills/         # OpenClaw skills
│   └── providers/      # LLM adapters
├── config/             # Configuration
├── tests/              # Test suite
└── docs/               # Documentation
```

## 🗺️ Roadmap

- [x] Phase 1: Core Engine (Task Manager, State Machine, Model Router, Cost Tracker)
- [x] Phase 2: Discord Integration, Human Approval Gates
- [ ] Phase 3: Web Dashboard (Mission Control UI)
- [ ] Phase 4: Team Features (Multi-user, roles, permissions)
- [ ] Phase 5: Open Source Release

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Inspired by GitHub Agentic Workflows (gh-aw)
- Built for teams using OpenClaw and multiple LLM providers
- Mission Control UI concept from NASA/JPL operations

---

**Built with 🖖 by the Agent Factory team**
