# Agent Factory - Mission Control Architecture
## Open Source Team-Oriented AI Agent Factory

## Repository Structure (Open Source Ready)

```
~/Repos/agent-factory/
├── README.md                 # Public documentation
├── LICENSE                   # MIT License
├── CONTRIBUTING.md           # Contribution guidelines
├── CODE_OF_CONDUCT.md
├── SECURITY.md              # Security reporting
├── docs/
│   ├── ARCHITECTURE.md      # This file
│   ├── DEPLOYMENT.md
│   ├── API.md
│   └── TUTORIALS/
├── src/
│   ├── core/                # Core engine
│   │   ├── __init__.py
│   │   ├── task_manager.py
│   │   ├── state_machine.py
│   │   ├── model_router.py
│   │   └── cost_tracker.py
│   ├── skills/              # OpenClaw skill adapters
│   │   ├── task_create/
│   │   ├── task_implement/
│   │   ├── task_review/
│   │   └── task_delegate/
│   ├── plugins/             # OpenClaw plugin integrations
│   │   ├── discord_bot/
│   │   ├── web_dashboard/
│   │   ├── slack_bridge/
│   │   └── github_bridge/   # Optional
│   ├── providers/           # LLM providers
│   │   ├── ollama.py
│   │   ├── anthropic.py
│   │   ├── openai.py
│   │   ├── google.py
│   │   ├── huggingface.py
│   │   ├── groq.py
│   │   └── base.py
│   ├── storage/
│   │   ├── markdown_store.py
│   │   ├── git_tracker.py
│   │   └── sqlite_cache.py
│   └── web/
│       ├── __init__.py
│       ├── app.py           # FastAPI app
│       ├── static/
│       └── templates/
├── config/
│   ├── default.yaml          # Default config (no secrets)
│   └── example.secrets.yaml  # Template for secrets
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evals/
├── scripts/
│   ├── install.sh
│   └── dev-setup.sh
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

## Runtime Data Structure

```
~/Repos/agent-factory-data/     # Runtime data (not in git)
├── tasks/
│   ├── 0001-init-project.md
│   ├── 0002-implement-auth.md
│   └── 0003-review-code.md
├── state/
│   ├── task-queue.json
│   ├── active-context.json
│   └── user-sessions.json
├── learnings/
│   ├── patterns/
│   │   └── auth-flow-v1.json
│   └── mistakes.md
├── reviews/
│   └── pr-001.md
├── logs/
│   └── 2026-05-14/
└── cache/
    └── model-responses/
```

## OpenClaw Plugin Integration

### Discord Plugin
```python
# src/plugins/discord_bot/plugin.py
from openclaw.plugins import Plugin

class DiscordAgentFactoryPlugin(Plugin):
    """Discord integration for Agent Factory"""
    
    async def on_task_created(self, task):
        """Notify Discord when task created"""
        await self.send_embed(
            channel="#agent-factory",
            title=f"🆕 Task #{task.id}: {task.title}",
            description=task.summary,
            fields=[
                {"name": "Priority", "value": task.priority, "inline": True},
                {"name": "Model", "value": task.assigned_model, "inline": True},
                {"name": "Est. Cost", "value": f"${task.estimated_cost}", "inline": True}
            ]
        )
    
    async def on_approval_needed(self, task, gate):
        """Request human approval via Discord"""
        buttons = [
            Button(label="✅ Approve", style="success", custom_id=f"approve_{task.id}"),
            Button(label="❌ Reject", style="danger", custom_id=f"reject_{task.id}"),
            Button(label="📝 Request Changes", style="secondary", custom_id=f"changes_{task.id}")
        ]
        
        message = await self.send_message(
            channel="#approvals",
            content=f"⏳ Approval needed for Task #{task.id}",
            embed=task.to_embed(),
            components=buttons
        )
        
        # Wait for response (timeout after configured duration)
        response = await self.wait_for_interaction(
            custom_id=f"approve_{task.id}",
            timeout=task.approval_timeout
        )
        
        return response.action
```

### Web Dashboard Plugin
```python
# src/plugins/web_dashboard/plugin.py
from openclaw.plugins import Plugin
from fastapi import FastAPI, WebSocket

class WebDashboardPlugin(Plugin):
    """Mission Control web dashboard"""
    
    def __init__(self):
        self.app = FastAPI(title="Agent Factory - Mission Control")
        self.active_connections = []
        
    async def broadcast_task_update(self, task):
        """Push updates to all connected dashboards"""
        message = {
            "type": "task_update",
            "task": task.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for connection in self.active_connections:
            await connection.send_json(message)
    
    async def on_task_state_change(self, task, old_state, new_state):
        """Broadcast state changes to dashboard"""
        await self.broadcast_task_update(task)
        
        # Also update metrics
        await self.metrics_collector.record_state_transition(
            task, old_state, new_state
        )
```

## Mission Control Dashboard Features

### Real-Time Views

#### 1. Task Queue View
```
┌─────────────────────────────────────────────────────────────┐
│  AGENT FACTORY - MISSION CONTROL                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📋 BACKLOG (5)          🔄 IN PROGRESS (2)      ✅ DONE (8) │
│  ┌─────────────┐         ┌─────────────┐                    │
│  │ #0012 Auth  │         │ #0010 API   │                    │
│  │ #0013 Tests │         │ #0011 Docs  │                    │
│  │ #0014 Refac │         └─────────────┘                    │
│  │ ...         │                                           │
│  └─────────────┘                                           │
│                                                             │
│  ⏳ WAITING FOR APPROVAL (1)                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ #0009 Implement payment gateway - Claude Sonnet     │  │
│  │ [Review Plan] [Approve] [Request Changes]           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  💰 TODAY'S COST: $2.34  |  💵 ESTIMATED: $5.67           │
│  🔄 ACTIVE AGENTS: 2    |  ⏱️ AVG TIME: 4.2 min          │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Agent Activity Stream
```
┌─────────────────────────────────────────────────────────────┐
│ LIVE ACTIVITY                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  14:32:05  🤖 Claude-Opus completed Task #0010 (4m 12s)    │
│  14:31:42  📤 Task #0012 assigned to Kimi-K2.5            │
│  14:28:19  ✅ Approved Task #0009 by @erick                │
│  14:25:03  💡 Pattern match: "Auth flow" similar to #0005  │
│  14:22:11  ⚠️  Cost alert: Task #0008 exceeded $1.00      │
│  14:20:55  🔍 Review complete for Task #0007              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3. Model Performance Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ MODEL PERFORMANCE (Last 7 Days)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Model               Tasks   Success   Avg Time   Cost      │
│  ─────────────────────────────────────────────────────────  │
│  Claude-Sonnet       45     93%       3.2m      $12.34    │
│  Kimi-K2.5           23     91%       4.1m      $0.00     │
│  Qwen3.5             67     87%       2.8m      $0.00     │
│  GPT-4o              12     96%       2.1m      $8.92     │
│                                                             │
│  [Success Rate Chart]   [Cost Per Task Chart]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 4. Team Collaboration View
```
┌─────────────────────────────────────────────────────────────┐
│ TEAM ACTIVITY                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  👤 @erick (You)                                           │
│     Approved: 5 tasks | Rejected: 1 | Pending: 2            │
│                                                             │
│  🤖 Active Agents                                           │
│     ├── Claude-Opus: Task #0010 (payment gateway)           │
│     └── Kimi-K2.5: Task #0012 (auth implementation)        │
│                                                             │
│  📊 Your Queue                                              │
│     2 tasks awaiting your approval                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Security & Secrets Management

### No Secrets in Code

```yaml
# config/default.yaml - Safe to commit
models:
  providers:
    anthropic:
      enabled: true
      base_url: "https://api.anthropic.com"
      # API key loaded from environment
    
    ollama:
      enabled: true
      base_url: "http://localhost:11434"
      # No auth needed
    
    openai:
      enabled: false  # Disabled by default
      base_url: "https://api.openai.com"

# Environment variables needed:
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
# HUGGINGFACE_TOKEN=
# GROQ_API_KEY=
# DISCORD_BOT_TOKEN=
# SLACK_BOT_TOKEN=
```

### Secret Validation Script
```bash
#!/bin/bash
# scripts/check-secrets.sh - CI/CD safety check

if grep -r "api_key\|apikey\|token" --include="*.py" src/ | grep -v "os.environ" | grep -v "getenv"; then
    echo "❌ ERROR: Potential hardcoded secrets found"
    exit 1
fi

echo "✅ No hardcoded secrets detected"
```

## OpenClaw Skill Adapters

### Skill: task-create
```python
# src/skills/task_create/adapter.py
"""
OpenClaw Skill Adapter for Task Creation
"""
from agent_factory.core import TaskManager
from agent_factory.core.models import ModelRouter

class TaskCreateSkill:
    """Create new tasks from natural language requests"""
    
    def __init__(self, config):
        self.task_manager = TaskManager(config.storage_path)
        self.model_router = ModelRouter(config.models)
    
    async def execute(self, request: str, context: dict = None) -> dict:
        """
        OpenClaw calls this when user says:
        "Create a task to implement user authentication"
        """
        # Select appropriate model
        model = await self.model_router.select(
            task_type="task_creation",
            complexity="medium",
            priority="normal"
        )
        
        # Generate task specification
        prompt = f"""
        Analyze this request and create a detailed task specification:
        
        Request: {request}
        Context: {context or 'None'}
        
        Provide:
        1. Clear title
        2. Detailed description
        3. Acceptance criteria
        4. Estimated complexity (1-5)
        5. Recommended model tier
        """
        
        response = await model.generate(prompt)
        
        # Create task object
        task = self.task_manager.create_task(
            title=response.title,
            description=response.description,
            acceptance_criteria=response.criteria,
            complexity=response.complexity,
            recommended_model=response.recommended_model
        )
        
        return {
            "task_id": task.id,
            "title": task.title,
            "next_step": "Awaiting human approval or auto-start",
            "dashboard_url": f"http://localhost:8080/tasks/{task.id}"
        }
```

## Team Features

### Multi-User Support
```python
class TeamManager:
    """Manage team members and permissions"""
    
    def __init__(self):
        self.members = {}
        self.roles = {
            "admin": ["*"],  # All permissions
            "lead": ["approve", "review", "override"],
            "developer": ["create", "view"],
            "viewer": ["view"]
        }
    
    async def can_approve(self, user_id: str, task_id: str) -> bool:
        """Check if user can approve this task"""
        user = self.members.get(user_id)
        if not user:
            return False
        
        # Check role permissions
        role_perms = self.roles.get(user.role, [])
        return "approve" in role_perms or "*" in role_perms
    
    async def assign_task(self, task_id: str, user_id: str):
        """Assign task to specific team member"""
        task = await self.task_manager.get(task_id)
        task.assignee = user_id
        await self.notify_user(user_id, f"Task #{task_id} assigned to you")
```

### Notifications
```python
class NotificationService:
    """Multi-channel notifications"""
    
    async def notify_task_created(self, task):
        # Discord
        if self.discord_enabled:
            await self.discord.send_task_embed(task)
        
        # Slack
        if self.slack_enabled:
            await self.slack.send_message(
                channel="#agent-factory",
                text=f"New task: #{task.id} - {task.title}"
            )
        
        # Dashboard (real-time WebSocket)
        await self.dashboard.broadcast({
            "type": "new_task",
            "task": task.to_dict()
        })
        
        # Browser notification (if enabled)
        await self.push_notification(
            title="New Task Created",
            body=task.title,
            url=f"/tasks/{task.id}"
        )
```

## Implementation Phases

### Phase 1: Core Engine (Week 1)
- Task storage (markdown)
- State machine
- Basic model routing
- Cost tracking
- 3 core skills

### Phase 2: OpenClaw Integration (Week 2)
- Skill adapters
- Discord plugin
- Config system
- Secret management

### Phase 3: Web Dashboard (Week 3)
- FastAPI backend
- Real-time updates (WebSockets)
- React frontend
- Mission Control UI

### Phase 4: Team Features (Week 4)
- Multi-user support
- Role-based permissions
- Team activity feed
- Collaboration features

### Phase 5: Polish & Open Source (Week 5)
- Documentation
- Tests
- CI/CD
- GitHub release

## Next Steps

1. **Initialize repository at ~/Repos/agent-factory/**
2. **Set up core task manager**
3. **Build OpenClaw skill adapters**
4. **Create Discord bot**
5. **Build Mission Control dashboard**

Ready to start Phase 1?
