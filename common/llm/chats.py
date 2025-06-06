from abc import ABC
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.messages.base import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from common.utils.llm import create_sys_message, geminiAPIKey, getOpenAIKey

rate_limiter = InMemoryRateLimiter(
    requests_per_second=1/6,  # 6 seconds per request
    max_bucket_size=2,
    check_every_n_seconds=1
)

class LLMChat(ABC):
    def __init__(self):
        self.llm = None
        self.model_name = None
        self.system_instruction = None
        self.chat = []
        self.clear_chat()

    def send_message(self, message: BaseMessage):
        self.__checkInitilization()
        self.chat.append(message)
        answer = self.llm.invoke(self.chat)
        self.chat.append(answer)
        return answer.content

    def generate(self, message):
        self.__checkInitilization()
        return self.llm.invoke(message).content

    def get_model_name(self):
        self.__checkInitilization()
        return self.model_name

    def set_system_instruction(self, system_instruction: str):
        self.__checkInitilization()
        self.system_instruction = system_instruction
        self.clear_chat()

    def clear_system_instruction(self):
        self.__checkInitilization()
        self.system_instruction = None
        self.clear_chat()    
    
    def get_system_instruction(self):
        self.__checkInitilization()
        return self.system_instruction
    
    def clear_chat(self):
        if self.system_instruction is not None:
            self.chat = [create_sys_message(self.system_instruction)]
        else:
            self.chat = []

    def __checkInitilization(self):
        if not self.llm:
            raise Exception("LLM not initialized")

class GeminiChat(LLMChat):
    def __init__(self, model_name="gemini-2.0-flash"):
        super().__init__()
        self.model_name = model_name
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=geminiAPIKey(),
            rate_limiter=rate_limiter
        )

class OllamaChat(LLMChat):
    def __init__(self, model_name="llava"):
        super().__init__()
        self.model_name = model_name
        self.llm = ChatOllama(
            model=model_name,
            temperature=0,
        )       

class OpenAIChat(LLMChat):
    def __init__(self, model_name="gpt-4o-mini"):
        super().__init__()
        self.model_name = model_name
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=getOpenAIKey()
        )
