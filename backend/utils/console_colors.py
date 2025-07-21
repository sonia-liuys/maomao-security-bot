#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Console color utilities for logging and terminal output formatting.
"""

# ANSI escape sequences for terminal colors
COLORS = {
    # Regular colors
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    
    # Bold/bright colors
    "BOLD": "\033[1m",
    "BRIGHT_BLACK": "\033[90m",
    "BRIGHT_RED": "\033[91m",
    "BRIGHT_GREEN": "\033[92m",
    "BRIGHT_YELLOW": "\033[93m",
    "BRIGHT_BLUE": "\033[94m",
    "BRIGHT_MAGENTA": "\033[95m",
    "BRIGHT_CYAN": "\033[96m",
    "BRIGHT_WHITE": "\033[97m",
    
    # Other formatting
    "RESET": "\033[0m",
    "UNDERLINE": "\033[4m",
    "INVERSE": "\033[7m",
}

def colorize(text, color):
    """
    Wrap text with the specified color.
    
    Args:
        text (str): Text to colorize
        color (str): Color name as defined in COLORS
        
    Returns:
        str: Colorized text
    """
    if color not in COLORS:
        return text
    return f"{COLORS[color]}{text}{COLORS['RESET']}"
