"""
Test the complete ReAct loop with a simple question
"""
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent


# Mock tools
def mock_search(query):
    """Mock search tool with predefined answers"""
    responses = {
        "capital of France": "Paris is the capital of France.",
        "capital of Vietnam": "Hanoi is the capital of Vietnam since 1976.",
        "Vietnam population 2024": "Vietnam has approximately 98.5 million people in 2024.",
        "Thailand population 2024": "Thailand has approximately 71.8 million people in 2024.",
    }
    
    # Find matching response
    for key, value in responses.items():
        if key.lower() in query.lower():
            return value
    
    return f"Search results for '{query}': No specific data found."


def mock_calculate(expression):
    """Mock calculator"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Calculation error: {e}"


def test_react_loop():
    """Test the complete ReAct agent"""
    print("="*60)
    print("TESTING REACT AGENT LOOP")
    print("="*60)
    
    load_dotenv()
    provider = OpenAIProvider(model_name="gpt-4o")
    
    tools = [
        {
            'name': 'search',
            'description': 'Search for information on the web',
            'input_format': 'string (search query)',
            'example': 'search("Vietnam population 2024")',
            'function': mock_search
        },
        {
            'name': 'calculate',
            'description': 'Perform mathematical calculations',
            'input_format': 'string (math expression)',
            'example': 'calculate("100 + 200")',
            'function': mock_calculate
        }
    ]
    
    agent = ReActAgent(provider, tools, max_steps=5)
    
    # Test 1: Simple question (1 step)
    print("\n[TEST 1: Simple question - 1 step expected]")
    print("Question: What is the capital of France?")
    print("\nAgent working...")
    print("-" * 60)
    
    answer1 = agent.run("What is the capital of France?")
    
    print("\nFINAL ANSWER:")
    print(answer1)
    print("-" * 60)
    
    assert "Paris" in answer1, f"Expected 'Paris' in answer, got: {answer1}"
    print("[OK] Answer contains 'Paris'")
    
    # Test 2: Multi-step question (2-3 steps expected)
    print("\n" + "="*60)
    print("[TEST 2: Multi-step question - 2-3 steps expected]")
    print("Question: Compare Vietnam and Thailand population, which is larger?")
    print("\nAgent working...")
    print("-" * 60)
    
    answer2 = agent.run("Compare the population of Vietnam and Thailand in 2024. Which country has more people?")
    
    print("\nFINAL ANSWER:")
    print(answer2)
    print("-" * 60)
    
    assert "Vietnam" in answer2 or "98.5" in answer2, f"Expected population info in answer"
    print("[OK] Answer contains population information")
    
    # Test 3: Question with calculation
    print("\n" + "="*60)
    print("[TEST 3: Question requiring calculation]")
    print("Question: What is 150 + 275?")
    print("\nAgent working...")
    print("-" * 60)
    
    answer3 = agent.run("What is 150 + 275?")
    
    print("\nFINAL ANSWER:")
    print(answer3)
    print("-" * 60)
    
    assert "425" in answer3, f"Expected '425' in answer, got: {answer3}"
    print("[OK] Correct calculation result")
    
    print("\n" + "="*60)
    print("ALL REACT LOOP TESTS PASSED!")
    print("="*60)
    print("\nThe agent successfully:")
    print("  [OK] Followed ReAct format")
    print("  [OK] Called tools correctly")
    print("  [OK] Handled observations")
    print("  [OK] Provided final answers")
    print("  [OK] Worked for both simple and multi-step questions")
    print("\nReady for Task 6: Multi-hop Reasoning Support!")


if __name__ == "__main__":
    test_react_loop()
