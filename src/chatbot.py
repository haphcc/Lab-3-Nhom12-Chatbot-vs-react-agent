
from src.core.openai_provider import OpenAIProvider

class Chatbot:
    def __init__(self):
        self.llm = OpenAIProvider()

    def ask(self, question: str) -> str:
        prompt = f"""
        Answer the question directly.

        Question: {question}
        Answer:
        """
        return self.llm.generate(prompt)