"""
title: Dashboard Filter
author: Antigravity
author_url: https://github.com/open-webui
version: 1.3.0
"""

from pydantic import BaseModel, Field
from typing import Optional

class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Priority level for the filter operations.")

    def __init__(self):
        self.valves = self.Valves()

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # The dashboard button is now injected globally via index.html
        # This filter can be used for other outgoing message modifications if needed.
        return body
