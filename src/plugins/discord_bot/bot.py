"""Discord Bot for Agent Factory Mission Control"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ui import Button, View


class ApprovalView(View):
    """Discord view for approval buttons"""
    
    def __init__(self, task_id: str, timeout: float = 86400):
        super().__init__(timeout=timeout)
        self.task_id = task_id
        self.result = None
    
    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success, custom_id="approve")
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        self.result = "approved"
        await interaction.response.send_message(f"✅ Task {self.task_id} approved by {interaction.user.name}")
        self.stop()
    
    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger, custom_id="reject")
    async def reject_button(self, interaction: discord.Interaction, button: Button):
        self.result = "rejected"
        await interaction.response.send_message(f"❌ Task {self.task_id} rejected by {interaction.user.name}")
        self.stop()
    
    @discord.ui.button(label="📝 Request Changes", style=discord.ButtonStyle.secondary, custom_id="changes")
    async def changes_button(self, interaction: discord.Interaction, button: Button):
        self.result = "changes_requested"
        await interaction.response.send_message(f"📝 Changes requested for Task {self.task_id} by {interaction.user.name}")
        self.stop()


class DiscordAgentFactoryBot:
    """Discord bot for Agent Factory notifications and approvals"""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv("DISCORD_BOT_TOKEN")
        self.client = discord.Client(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self.client)
        self.approval_callbacks = {}
        
        self._setup_events()
        self._setup_commands()
    
    def _setup_events(self):
        @self.client.event
        async def on_ready():
            print(f"🤖 {self.client.user} is online!")
            await self.tree.sync()
    
    def _setup_commands(self):
        @self.tree.command(name="tasks", description="List active tasks")
        async def tasks_command(interaction: discord.Interaction):
            await interaction.response.send_message("📋 Fetching tasks...")
            # TODO: Integrate with TaskManager
    
    async def start(self):
        """Start the bot"""
        await self.client.start(self.token)
    
    async def notify_task_created(self, channel_id: int, task: dict):
        """Send task creation notification"""
        channel = self.client.get_channel(channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title=f"🆕 Task #{task['id']}: {task['title']}",
            description=task.get('description', 'No description')[:200],
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Priority", value=task.get('priority', 'normal'), inline=True)
        embed.add_field(name="Complexity", value=str(task.get('complexity', 3)), inline=True)
        embed.add_field(name="Est. Cost", value=f"${task.get('estimated_cost', 0)}", inline=True)
        
        await channel.send(embed=embed)
    
    async def request_approval(self, channel_id: int, task: dict, timeout: float = 86400) -> Optional[str]:
        """Request human approval via Discord"""
        channel = self.client.get_channel(channel_id)
        if not channel:
            return None
        
        embed = discord.Embed(
            title=f"⏳ Approval Needed: Task #{task['id']}",
            description=task.get('description', 'No description')[:500],
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Action Required", value="Please approve, reject, or request changes", inline=False)
        
        view = ApprovalView(task['id'], timeout=timeout)
        message = await channel.send(embed=embed, view=view)
        
        await view.wait()
        return view.result
    
    async def notify_task_completed(self, channel_id: int, task: dict):
        """Notify task completion"""
        channel = self.client.get_channel(channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title=f"✅ Task #{task['id']} Completed",
            description=f"**{task['title']}**",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Actual Cost", value=f"${task.get('actual_cost', 0)}", inline=True)
        embed.add_field(name="Time Taken", value=task.get('duration', 'N/A'), inline=True)
        
        await channel.send(embed=embed)
    
    async def send_cost_alert(self, channel_id: int, budget_status: dict):
        """Send budget alert"""
        channel = self.client.get_channel(channel_id)
        if not channel:
            return
        
        embed = discord.Embed(
            title="⚠️ Budget Alert",
            description=f"Daily budget at {budget_status['daily_percent']}%",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Spent", value=f"${budget_status['daily_cost']}", inline=True)
        embed.add_field(name="Remaining", value=f"${budget_status['daily_remaining']}", inline=True)
        embed.add_field(name="Budget", value=f"${budget_status['daily_budget']}", inline=True)
        
        await channel.send(embed=embed)


# Standalone runner
if __name__ == "__main__":
    bot = DiscordAgentFactoryBot()
    asyncio.run(bot.start())
