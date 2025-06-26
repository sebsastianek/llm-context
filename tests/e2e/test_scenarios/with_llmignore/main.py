"""
Project with LLM-specific ignore patterns
"""

def main():
    print("This is the main application")
    
def helper_function():
    """This function helps with processing"""
    return "helper result"

def calculate_metrics():
    """Calculate some metrics"""
    metrics = {
        'users': 1000,
        'sessions': 5000,
        'conversion_rate': 0.15
    }
    return metrics

if __name__ == "__main__":
    main()
    result = helper_function()
    metrics = calculate_metrics()
    print(f"Helper result: {result}")
    print(f"Metrics: {metrics}")