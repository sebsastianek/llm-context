#!/usr/bin/env python3
"""
Simple Python project main file for testing llmcontext
"""

def hello_world():
    """Print hello world message"""
    print("Hello, World!")

def calculate_sum(a, b):
    """Calculate sum of two numbers"""
    return a + b

if __name__ == "__main__":
    hello_world()
    result = calculate_sum(5, 3)
    print(f"Sum: {result}")