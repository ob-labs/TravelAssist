"""
Prompt module for OBMMS.

Contains prompt templates for all agents.
"""

from .prompt_list import (
    consult_prompt,
    extract_info_prompt,
    plan_prompt,
    summary_prompt,
)

__all__ = [
    "extract_info_prompt",
    "consult_prompt",
    "summary_prompt",
    "plan_prompt",
]
