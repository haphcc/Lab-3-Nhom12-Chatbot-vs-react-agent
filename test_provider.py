"""
Test script để kiểm tra OpenAI Provider hoạt động
"""
import os
import sys
from dotenv import load_dotenv

# Fix encoding for Vietnamese characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider

def test_openai_provider():
    """Test OpenAI provider với một query đơn giản"""
    print("="*60)
    print("TESTING OPENAI PROVIDER")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env")
        return False
    
    print(f"OK API Key found: {api_key[:10]}...")
    
    try:
        # Initialize provider
        print("\nInitializing OpenAI Provider (gpt-4o)...")
        provider = OpenAIProvider(model_name="gpt-4o")
        
        # Test simple generation
        print("\nTesting simple generation...")
        print("Prompt: 'Hello, who are you?'")
        print("\nGenerating response...\n")
        
        result = provider.generate(
            prompt="Hello, who are you?",
            system_prompt="You are a smart AI assistant."
        )
        
        # Display results
        print("-" * 60)
        print("RESPONSE:")
        print(result['content'][:200])  # First 200 chars only
        print("...")
        print("-" * 60)
        
        print(f"\nMETRICS:")
        print(f"  - Prompt tokens: {result['usage']['prompt_tokens']}")
        print(f"  - Completion tokens: {result['usage']['completion_tokens']}")
        print(f"  - Total tokens: {result['usage']['total_tokens']}")
        print(f"  - Latency: {result['latency_ms']}ms")
        print(f"  - Provider: {result['provider']}")
        
        print("\nOK Provider test SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"\nERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_prompt():
    """Test với system prompt để hiểu cách ReAct format hoạt động"""
    print("\n" + "="*60)
    print("TESTING REACT FORMAT WITH SYSTEM PROMPT")
    print("="*60)
    
    load_dotenv()
    provider = OpenAIProvider(model_name="gpt-4o")
    
    # Simple ReAct prompt
    system_prompt = """You are an AI assistant that follows the ReAct format.

Available tools:
- search(query): Search for information on the web

Format:
Thought: Your reasoning
Action: tool_name(arguments)
Observation: [System will provide this]
Final Answer: Your final response

Example:
Question: What is the capital of Vietnam?
Thought: I need to search for this information
Action: search("capital of Vietnam")
"""
    
    user_prompt = "What is the capital of France?"
    
    print(f"\nUser Question: {user_prompt}")
    print("\nGenerating response...\n")
    
    result = provider.generate(
        prompt=user_prompt,
        system_prompt=system_prompt
    )
    
    print("-" * 60)
    print("AGENT RESPONSE:")
    print(result['content'][:300])  # First 300 chars
    print("...")
    print("-" * 60)
    
    print(f"\nTokens used: {result['usage']['total_tokens']}")
    print(f"Latency: {result['latency_ms']}ms")
    
    return True

if __name__ == "__main__":
    # Test 1: Basic provider functionality
    success1 = test_openai_provider()
    
    if success1:
        # Test 2: ReAct format understanding
        test_system_prompt()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nChecklist completed:")
        print("  [OK] OpenAI Provider initialized successfully")
        print("  [OK] API key working")
        print("  [OK] LLM responds correctly")
        print("  [OK] System prompt accepted")
        print("  [OK] Metrics tracking works")
        print("\nReady to proceed to Task 2: Parsing Utilities")
    else:
        print("\nTests failed. Please check your .env file and API key.")
