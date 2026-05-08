"""
title: Dashboard Action
author: Antigravity
author_url: https://github.com/open-webui
version: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Dict, Any

class Action:
    class Valves(BaseModel):
        show_always: bool = Field(default=False, description="Show the action button even if no dashboard is detected.")

    def __init__(self):
        self.valves = self.Valves()

    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
    ) -> Optional[dict]:
        # This is called when the action button is clicked
        messages = body.get("messages", [])
        if not messages:
            return None

        # Find the content of the message the action was clicked on
        # The 'body' in an action usually contains the specific message
        content = body.get("message", {}).get("content", "")
        
        # If the current message doesn't have it, look through history
        if not ("<!DOCTYPE html>" in content or "ApexCharts" in content):
            for msg in reversed(messages):
                if "<!DOCTYPE html>" in msg.get("content", ""):
                    content = msg.get("content", "")
                    break

        if "<!DOCTYPE html>" in content or "ApexCharts" in content:
            # Extract the HTML code block
            import re
            match = re.search(r"```html\n(.*?)\n```", content, re.DOTALL)
            html = match.group(1) if match else content
            
            # We use the event_emitter to tell the frontend to open a new window
            # Open WebUI supports a special 'code_interpreter' or 'chat_completion' event 
            # but for opening a window, we can send a message that the user can click
            # OR we can use the 'status' event to show we are opening it.
            
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "Opening Dashboard...", "done": True}
                })
                
                # We can't directly open a window from Python, so we'll return
                # a message with a link or just inform the user.
                # HOWEVER, for a truly native feel, we can return a response 
                # that the frontend interprets.
            
            return {"content": "Dashboard link generated! (This is a placeholder - see instructions below)"}

        return None

    # This defines the button in the UI
    def buttons(self) -> list:
        return [
            {
                "id": "view-dashboard",
                "text": "View Dashboard",
                "icon": "M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z",
                "action": "view_dashboard"
            }
        ]
