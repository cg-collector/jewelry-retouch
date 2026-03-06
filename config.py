import os
import ast

class Config:
    def __init__(self, env_path=".env"):
        self.models = []
        self.base_url = ""
        self.api_key = ""
        self.endpoint_map = {}
        self._load_env(env_path)

    def _load_env(self, env_path):
        if not os.path.exists(env_path):
            print(f"Warning: {env_path} not found.")
            return

        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse line by line to handle the custom format
        # format: key = value
        local_scope = {}
        try:
            # Using exec to parse python-like assignment safely if possible
            # Or manually parsing
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "models":
                        try:
                            self.models = ast.literal_eval(value)
                        except:
                            print(f"Failed to parse models list: {value}")
                    elif key == "base_url":
                        self.base_url = value.strip('"\'')
                    elif key == "api_keys":
                        self.api_key = value.strip('"\'')
                    elif key == "endpoint_map":
                        try:
                            self.endpoint_map = ast.literal_eval(value)
                        except:
                            print(f"Failed to parse endpoint_map: {value}")
        except Exception as e:
            print(f"Error parsing .env: {e}")

    def validate(self):
        if not self.api_key:
            raise ValueError("API Key is missing in .env file. Please set 'api_keys'.")
        if not self.base_url:
            raise ValueError("Base URL is missing in .env file.")
        if not self.models:
            print("Warning: No models found in .env, using default.")

    def get_endpoint_for_model(self, model: str) -> str:
        default_endpoint = "/v1/images/edits"
        return self.endpoint_map.get(model, default_endpoint)
