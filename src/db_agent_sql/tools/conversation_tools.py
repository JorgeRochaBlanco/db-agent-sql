"""Tools for the Conversation Agent."""

import logging
from datetime import datetime
from agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
def get_current_time() -> str:
    """
    Get the current date and time.
    
    Returns:
        Current date and time formatted as a string
    """
    now = datetime.now()
    return f"Current time: {now.strftime('%I:%M %p')}, Date: {now.strftime('%B %d, %Y (%A)')}"
