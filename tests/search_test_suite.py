
import json
from src.chatbot import Chatbot

class SearchTestSuite:
    def __init__(self):
        self.bot = Chatbot()

    def load_tests(self):
        with open("tests/test_cases.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def run(self):
        test_cases = self.load_tests()
        results = []

        for case in test_cases:
            question = case["question"]
            expected = case["expected"]

            answer = self.bot.ask(question)

            results.append({
                "category": case["category"],
                "question": question,
                "expected": expected,
                "answer": answer
            })

        return results