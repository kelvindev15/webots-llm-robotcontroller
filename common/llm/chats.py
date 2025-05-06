from abc import ABC, abstractmethod
from langchain_core.messages.base import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from common.utils.llm import create_sys_message, geminiAPIKey, getOpenAIKey


class LLMChat(ABC):
    def __init__(self, system_instruction: str = None):
        self.llm = None
        self.model_name = None
        self.system_message = create_sys_message(
            system_instruction) if system_instruction else None
        self.chat = [self.system_message] if self.system_message else []

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

    def get_system_instruction(self):
        self.__checkInitilization()
        return self.system_message.content

    def clear_chat(self):
        self.chat = [self.system_message] if self.system_message else []

    def __checkInitilization(self):
        if not self.llm:
            raise Exception("LLM not initialized")


class GeminiChat(LLMChat):
    def __init__(self, model_name="gemini-2.0-flash", system_instruction=None):
        super().__init__(system_instruction)
        self.model_name = model_name
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=geminiAPIKey()
        )


class LLavaChat(LLMChat):
    def __init__(self, model_name="llava", system_instruction=None):
        super().__init__(system_instruction)
        self.model_name = model_name
        self.llm = ChatOllama(
            model=model_name,
            temperature=0,
        )


class OpenAIChat(LLMChat):
    def __init__(self, model_name="gpt-4o-mini", system_instruction=None):
        super().__init__(system_instruction)
        self.model_name = model_name
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=getOpenAIKey()
        )
