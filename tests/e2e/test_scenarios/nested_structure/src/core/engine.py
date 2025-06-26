"""
Core engine module for the application
"""

class Engine:
    def __init__(self, config=None):
        self.config = config or {}
        self.running = False
        
    def start(self):
        """Start the engine"""
        print("Engine starting...")
        self.running = True
        
    def stop(self):
        """Stop the engine"""
        print("Engine stopping...")
        self.running = False
        
    def process(self, data):
        """Process data through the engine"""
        if not self.running:
            raise RuntimeError("Engine not running")
        return f"Processed: {data}"