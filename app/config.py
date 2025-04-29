import os
from dotenv import load_dotenv

class Config:
    
    def __init__(self, env_file_path = "") -> None:
        self.error_traceback = False

        self.database_file_path = "memories.db"
        self.extractor_model = "mistral-nemo"
        self.summarizer_model = "qwen2.5:3b"
        self.summarizer_request_max_length = 30000 # symbols
        self.summarizer_response_max_length = 3000

        self.auto_patch_when_num_of_messages_is_greater_then = 4

        if env_file_path != "":
            load_dotenv(env_file_path)
        
        # ENV has highest priority. It can overwrite values from static .env file
        self.__parseEnv()

    def __parseEnv(self) -> None:
        """
            Set values from ENV. Overwrite values for config
        """
        for attr, _ in vars(self).items():
            if os.environ.get(attr.upper()) is not None:
                setattr(self, attr, os.environ.get(attr.upper()))