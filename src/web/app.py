"""FastAPI Web Dashboard for Agent Factory"""
import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

import sys
sys.path.insert(0, os.path.expanduser('~/Repos/agent-factory/src'))

from core.task_manager import TaskManager
from core.state_machine import StateMachine, TaskState
from core.model_router import ModelRouter
from core.cost_tracker import CostTracker


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


class MissionControl:
    """Real-time Mission Control dashboard data"""
    
    def __init__(self):
        self.task_manager = TaskManager()
        self.state_machine = StateMachine()
        self.model_router = ModelRouter()
        self.cost_tracker = CostTracker()
        self.manager = ConnectionManager()
        
        # Activity log
        self.activity_log: List[dict] = []
        self.max_log_entries = 100
    
    def get_task_queue(self) -> Dict:
        """Get task queue organized by state"""
        states = {
            "backlog": [],
            "spec-defined": [],
            "plan-approved": [],
            "in-progress": [],
            "needs-review": [],
            "approved": [],
            "done": [],
            "blocked": []
        }
        
        tasks = self.task_manager.list_tasks()
        for task in tasks:
            if task.state in states:
                states[task.state].append({
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority,
                    "complexity": task.complexity,
                    "assigned_model": task.assigned_model,
                    "assignee": task.assignee
                })
        
        return states
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        stats = self.task_manager.get_stats()
        cost_stats = self.cost_tracker.get_stats(days=1)
        model_stats = self.model_router.get_stats()
        
        return {
            "total_tasks": stats["total"],
            "by_state": stats["by_state"],
            "today_cost": cost_stats["total"],
            "total_calls": model_stats["total_calls"],
            "by_model": model_stats.get("by_model", {})
        }
    
    def log_activity(self, action: str, task_id: str, details: dict = None):
        """Log activity for activity stream"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "task_id": task_id,
            "details": details or {}
        }
        
        self.activity_log.insert(0, entry)
        
        # Trim log
        if len(self.activity_log) > self.max_log_entries:
            self.activity_log = self.activity_log[:self.max_log_entries]
    
    async def broadcast_update(self, task):
        """Broadcast task update to all connected clients"""
        await self.manager.broadcast({
            "type": "task_update",
            "task": task.to_dict() if hasattr(task, 'to_dict') else task,
            "timestamp": datetime.now().isoformat()
        })


# Global mission control instance
mission_control = MissionControl()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan events"""
    # Startup
    print("🚀 Mission Control starting...")
    yield
    # Shutdown
    print("🛑 Mission Control shutting down...")


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="Agent Factory - Mission Control",
        description="Real-time dashboard for AI Agent Teams",
        version="0.3.0",
        lifespan=lifespan
    )
    
    # Static files
    app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Main dashboard page"""
        return HTMLResponse(content=get_dashboard_html())
    
    @app.get("/api/tasks")
    async def get_tasks(state: Optional[str] = None):
        """Get tasks, optionally filtered by state"""
        tasks = mission_control.task_manager.list_tasks(state)
        return {"tasks": [t.to_dict() for t in tasks]}
    
    @app.get("/api/queue")
    async def get_queue():
        """Get task queue by state"""
        return mission_control.get_task_queue()
    
    @app.get("/api/metrics")
    async def get_metrics():
        """Get current metrics"""
        return mission_control.get_metrics()
    
    @app.get("/api/activity")
    async def get_activity(limit: int = 50):
        """Get recent activity"""
        return {"activity": mission_control.activity_log[:limit]}
    
    @app.post("/api/tasks/{task_id}/approve")
    async def approve_task(task_id: str):
        """Approve a task"""
        task = mission_control.task_manager.get_task(task_id)
        if not task:
            return {"error": "Task not found"}
        
        if mission_control.state_machine.transition(task, "approve", approved=True):
            mission_control.task_manager.update_task(task)
            mission_control.log_activity("approved", task_id)
            await mission_control.broadcast_update(task)
            return {"success": True, "state": task.state}
        
        return {"error": "Cannot approve task"}
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket for real-time updates"""
        await mission_control.manager.connect(websocket)
        try:
            # Send initial data
            await websocket.send_json({
                "type": "init",
                "queue": mission_control.get_task_queue(),
                "metrics": mission_control.get_metrics()
            })
            
            # Keep connection alive and handle client messages
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle ping/pong
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            mission_control.manager.disconnect(websocket)
    
    return app


def get_dashboard_html() -> str:
    """Generate dashboard HTML"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Agent Factory - Mission Control</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f0f23;
            color: #fff;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(90deg, #1a1a3e 0%, #2a2a5e 100%);
            padding: 20px;
            border-bottom: 2px solid #4a4a8e;
        }
        .header h1 {
            font-size: 28px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metrics {
            display: flex;
            gap: 20px;
            padding: 20px;
        }
        .metric-card {
            background: #1a1a3e;
            border-radius: 8px;
            padding: 20px;
            min-width: 150px;
            border: 1px solid #3a3a6e;
        }
        .metric-card h3 {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }
        .metric-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #00d4ff;
        }
        .board {
            display: flex;
            gap: 20px;
            padding: 20px;
            overflow-x: auto;
        }
        .column {
            min-width: 280px;
            background: #1a1a3e;
            border-radius: 8px;
            padding: 15px;
        }
        .column h2 {
            font-size: 14px;
            color: #888;
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        .task-card {
            background: #2a2a5e;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 3px solid #4a4a8e;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .task-card:hover {
            transform: translateX(5px);
            border-left-color: #00d4ff;
        }
        .task-id {
            font-size: 12px;
            color: #888;
        }
        .task-title {
            font-size: 14px;
            margin: 5px 0;
        }
        .task-meta {
            display: flex;
            gap: 10px;
            font-size: 11px;
            color: #666;
        }
        .activity {
            position: fixed;
            right: 20px;
            top: 100px;
            width: 300px;
            background: #1a1a3e;
            border-radius: 8px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
        }
        .activity h2 {
            font-size: 14px;
            color: #888;
            margin-bottom: 15px;
        }
        .activity-item {
            padding: 10px 0;
            border-bottom: 1px solid #2a2a5e;
            font-size: 12px;
        }
        .activity-item .time {
            color: #666;
        }
        .status-connected { color: #00ff88; }
        .status-disconnected { color: #ff4444; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Agent Factory - Mission Control</h1>
        <p id="connection-status" class="status-disconnected">● Connecting...</p>
    </div>
    
    <div class="metrics">
        <div class="metric-card">
            <h3>Total Tasks</h3>
            <div class="value" id="total-tasks">-</div>
        </div>
        <div class="metric-card">
            <h3>In Progress</h3>
            <div class="value" id="in-progress">-</div>
        </div>
        <div class="metric-card">
            <h3>Today's Cost</h3>
            <div class="value" id="today-cost">-</div>
        </div>
        <div class="metric-card">
            <h3>Active Models</h3>
            <div class="value" id="active-models">-</div>
        </div>
    </div>
    
    <div class="board" id="task-board">
        <!-- Columns will be populated by JavaScript -->
    </div>
    
    <div class="activity">
        <h2>📡 Live Activity</h2>
        <div id="activity-stream">
            <div class="activity-item">Waiting for connection...</div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onopen = function() {
            document.getElementById('connection-status').textContent = '● Connected';
            document.getElementById('connection-status').className = 'status-connected';
        };
        
        ws.onclose = function() {
            document.getElementById('connection-status').textContent = '● Disconnected';
            document.getElementById('connection-status').className = 'status-disconnected';
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'init') {
                updateQueue(data.queue);
                updateMetrics(data.metrics);
            } else if (data.type === 'task_update') {
                addActivity(`Task #${data.task.id} updated`);
                refreshData();
            }
        };
        
        function updateQueue(queue) {
            const board = document.getElementById('task-board');
            board.innerHTML = '';
            
            const columns = [
                { key: 'backlog', label: '📋 Backlog' },
                { key: 'spec-defined', label: '📝 Spec Defined' },
                { key: 'plan-approved', label: '✅ Plan Approved' },
                { key: 'in-progress', label: '🔄 In Progress' },
                { key: 'needs-review', label: '👀 Needs Review' },
                { key: 'approved', label: '✓ Approved' },
                { key: 'done', label: '🎉 Done' }
            ];
            
            columns.forEach(col => {
                const tasks = queue[col.key] || [];
                const columnDiv = document.createElement('div');
                columnDiv.className = 'column';
                columnDiv.innerHTML = `
                    <h2>${col.label} (${tasks.length})</h2>
                    ${tasks.map(task => `
                        <div class="task-card">
                            <div class="task-id">#${task.id}</div>
                            <div class="task-title">${task.title}</div>
                            <div class="task-meta">
                                <span>★ ${task.complexity}</span>
                                <span>${task.priority}</span>
                            </div>
                        </div>
                    `).join('')}
                `;
                board.appendChild(columnDiv);
            });
        }
        
        function updateMetrics(metrics) {
            document.getElementById('total-tasks').textContent = metrics.total_tasks || 0;
            document.getElementById('in-progress').textContent = metrics.by_state['in-progress'] || 0;
            document.getElementById('today-cost').textContent = '$' + (metrics.today_cost || 0).toFixed(2);
            document.getElementById('active-models').textContent = Object.keys(metrics.by_model || {}).length;
        }
        
        function addActivity(message) {
            const stream = document.getElementById('activity-stream');
            const item = document.createElement('div');
            item.className = 'activity-item';
            const time = new Date().toLocaleTimeString();
            item.innerHTML = `<span class="time">${time}</span> ${message}`;
            stream.insertBefore(item, stream.firstChild);
        }
        
        function refreshData() {
            // Fetch fresh data from API
            fetch('/api/queue').then(r => r.json()).then(updateQueue);
            fetch('/api/metrics').then(r => r.json()).then(updateMetrics);
        }
        
        // Refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
