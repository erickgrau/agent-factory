# Agent Factory - OpenClaw Skill

## Description

Mission Control for AI Agent Teams. Create, manage, and track tasks across local and cloud LLMs with cost tracking and team collaboration.

## Capabilities

- **task-create**: Create tasks from natural language
- **task-implement**: Execute implementation tasks
- **task-review**: Review completed work
- **task-delegate**: Delegate to appropriate model

## Installation

```bash
git clone https://github.com/your-org/agent-factory.git ~/Repos/agent-factory
cd ~/Repos/agent-factory
pip install -e .
```

## Usage

```python
# Create a task
"Create a task to implement user authentication with JWT"

# Check status
"Show me the task queue"

# Get stats
"What are today's costs?"
```

## Configuration

See `config/example.secrets.yaml` for required environment variables.

## Architecture

See `ARCHITECTURE.md` for full documentation.
