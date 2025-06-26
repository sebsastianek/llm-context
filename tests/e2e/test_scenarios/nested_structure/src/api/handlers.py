"""
API request handlers
"""

from ..core.engine import Engine
from ..utils.helpers import get_timestamp, load_json_config

class APIHandler:
    def __init__(self):
        self.engine = Engine()
        self.config = load_json_config('config.json')
        
    def handle_get(self, path, params=None):
        """Handle GET request"""
        return {
            'method': 'GET',
            'path': path,
            'params': params,
            'timestamp': get_timestamp(),
            'status': 'success'
        }
        
    def handle_post(self, path, data=None):
        """Handle POST request"""
        if data:
            processed = self.engine.process(data)
            return {
                'method': 'POST',
                'path': path,
                'processed_data': processed,
                'timestamp': get_timestamp(),
                'status': 'success'
            }
        return {'status': 'error', 'message': 'No data provided'}