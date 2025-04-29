from ollama import chat
from ollama import ChatResponse
import json

from .config import Config

class ContextAnalyser:
    """
    Context Analyser is a class that is used to analyse the context of the conversation.
    It is used to extract user profile information, key topics and summary from the conversation.
    It uses the chat model to extract the information.
    """
    def __init__(self, config: Config):
        self.config = config
        
    def extract_user_profile_info(self, message: str, current_info: dict) -> dict:
        """
        Extracts user profile information from the given data. It should take into account existent user's profile data.
        If something new or different is found, it should be updated.

        Example: 
            current_info = {
                "name": "John",
                "age": 30,
                "location": "New York",
                "interests": ["music", "sports"]
            }
        """
        system_hint = """
        You are a data extractor. Your task is to extract user information from the given data.
        We need to know who is the user, what he likes, what he does, what he is interested in.
        You should take into account existent user's profile data. If something new or different is found, it should be updated.
        List of keys is not mandatory. Deside keys yourself.
        Current user profile data is provided in the system message. It has to be taken into account and it has highter priority than the new data.
        Remember, the current user profile data is the result of analysis of the previous data.
        Your response should be in JSON format. The response should be clean JSON or text with JSON inside in ``` ``` format.
        If you don't find anything new, return the current user profile data. Do not remove any keys from the current user profile data without a reason.

        Example, return the data in the following format:
        {
            "name": "John",
            "age": 30,
            "location": "New York",
            "interests": ["music", "sports"]
        }
        or 
        {
            "name": "John"
        }
        or can be empty  
        {
        }
        """
        request = [
        {
            'role': 'system',
            'content': system_hint,
        },
        {
            'role': 'system',
            'content': f"Current users info:\n{current_info}",
        },
        {
            'role': 'user',
            'content': message,
        },
        ]
        response: ChatResponse = chat(model=self.config.extractor_model, messages=request)
        result = self.__extract_json_document(response['message']['content'])
        
        try:
            # The response 
            # Parse the result as JSON
            new_info = json.loads(result)

            if len(new_info) == 0:
                # If the result is empty, return the current info
                return current_info
            return new_info
        except json.JSONDecodeError:
            # If parsing fails, return the current info without changes
            print(f"Failed to parse JSON: {result}")
            return current_info

    def extract_key_topics(self, history: str, current_key_topics: dict) -> dict:
        """
        Extracts key topics from the given data. It should take into account existent key topics.
        If something new or different is found, it should be updated.

        Example: 
            current_key_topics = {
                "sports": 5,
                "music": 3,
                "travel": 2
            }
        """
        system_hint = """
        You are a data extractor. Your task is to extract key topics from the given data.
        You should take into account existent key topics. If something new or different is found, it should be updated.
        Topics can be anything, but they should be relevant to the data. It can be a phrase, a word or a sentence. 
        Take into account who provided the message, user or assistant. 
        If a topic is already present in the current key topics, increase its count by 1.

        Return the data in the following format:
        {
            "sports": 5,
            "music": 3,
            "travel": 2
        }
        """
        request = [
        {
            'role': 'system',
            'content': system_hint,
        },
        {
            'role': 'system',
            'content': f"Current key topics data:\n{current_key_topics}",
        },
        {
            'role': 'user',
            'content': f"Extract key topics from the following data:\n{history}",
        },
        ]
        
        response: ChatResponse = chat(model=self.config.extractor_model, messages=request)
        
        result = self.__extract_json_document(response['message']['content'])
        
        try:
            # Parse the result as JSON
            new_key_topics = json.loads(result)

            return new_key_topics
        except json.JSONDecodeError:
            # If parsing fails, return the current info without changes
            print(f"Failed to parse JSON: {result}")
            return current_key_topics
        
    def extract_summary(self, history: str, current_summary: str) -> str:
        """
        Extracts summary from the given data. It should take into account existent summary.
        If something new or different is found, it should be updated.
        """

        system_hint = f"""
        You are a context analyser. Your task is to extract summary from the given data.
        You should take into account existent summary. If something new or different is found, it should be updated.
        Existent summary is created based on previous data. 
        This is not the request from the user. You are indepentent and you can create your own summary based on communication of the user and assistant.
        The summary is needed for future context reference to know what was discussed.
        The final summary should not be longer than {self.config.summarizer_response_max_length} symbols.
        """
        request = [
        {
            'role': 'system',
            'content': system_hint,
        },
        {
            'role': 'system',
            'content': f"Current summary data:\n{current_summary}",
        },
        {
            'role': 'user',
            'content': f"Make the summary from the following data:\n{history}",
        },
        ]
        response: ChatResponse = chat(model=self.config.summarizer_model, messages=request)

        return response['message']['content']
    
    def __extract_json_document(self, data: str) -> dict:
        """
        Extracts JSON from the given data. It can be that a data is soe text and it has JSON inside in ``` ``` format.
        It should be extracted and returned as a dictionary.
        """
        # Find the start and end of the JSON block
        start = data.find("```")
        end = data.rfind("```")
        if start > -1 and end > 0:
            # Extract the JSON block
            data = data[start + 3:end].strip()
        if not data.startswith("{") and not data.startswith("["):
            if data.find("{") > -1:
                start = data.find("{")
                data = data[start:]
            elif data.find("[") > -1:
                start = data.find("[")
                data = data[start:]

        return data