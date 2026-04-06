"""
Parsing utilities for extracting Thought, Action, and Final Answer from LLM responses.

This module provides functions to parse ReAct-formatted outputs from LLMs.
"""
import re
from typing import Optional, Dict, Any


def parse_thought(text: str) -> Optional[str]:
    """
    Extract Thought from LLM response.
    
    Expected format: "Thought: <reasoning>"
    
    Args:
        text: The LLM response text
        
    Returns:
        str: The thought content, or None if not found
        
    Examples:
        >>> parse_thought("Thought: I need to search\\nAction: search('test')")
        'I need to search'
    """
    pattern = r"Thought:\s*(.+?)(?:\n|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        thought = match.group(1).strip()
        # Stop at next section (Action or Final Answer)
        if '\nAction:' in thought:
            thought = thought.split('\nAction:')[0].strip()
        if '\nFinal Answer:' in thought:
            thought = thought.split('\nFinal Answer:')[0].strip()
        return thought
    return None


def parse_action(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract Action from LLM response.
    
    Expected formats:
    - "Action: tool_name(arguments)"
    - "Action: tool_name with arguments"
    
    Args:
        text: The LLM response text
        
    Returns:
        dict: {'tool': 'tool_name', 'args': 'arguments'} or None
        
    Examples:
        >>> parse_action("Action: search('Vietnam population')")
        {'tool': 'search', 'args': 'Vietnam population'}
        
        >>> parse_action("Action: calculate(100 + 200)")
        {'tool': 'calculate', 'args': '100 + 200'}
    """
    # Pattern 1: Action: tool_name(args)
    pattern1 = r"Action:\s*(\w+)\s*\((.*?)\)"
    match = re.search(pattern1, text, re.IGNORECASE)
    
    if match:
        tool_name = match.group(1).strip()
        args = match.group(2).strip()
        # Remove quotes if present
        args = args.strip('"').strip("'")
        return {'tool': tool_name, 'args': args}
    
    # Pattern 2: Action: tool_name (without parentheses)
    pattern2 = r"Action:\s*(\w+)\s*$"
    match = re.search(pattern2, text, re.IGNORECASE | re.MULTILINE)
    if match:
        return {'tool': match.group(1).strip(), 'args': ''}
    
    return None


def parse_final_answer(text: str) -> Optional[str]:
    """
    Extract Final Answer from LLM response.
    
    Expected format: "Final Answer: <answer>"
    
    Args:
        text: The LLM response text
        
    Returns:
        str: The final answer content, or None if not found
        
    Examples:
        >>> parse_final_answer("Final Answer: The capital is Hanoi")
        'The capital is Hanoi'
    """
    pattern = r"Final Answer:\s*(.+?)(?:\n\n|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def has_final_answer(text: str) -> bool:
    """
    Check if the response contains a Final Answer.
    
    Args:
        text: The LLM response text
        
    Returns:
        bool: True if Final Answer is present
    """
    return parse_final_answer(text) is not None


def parse_observation(text: str) -> Optional[str]:
    """
    Extract Observation from text (for testing purposes).
    
    Note: In actual agent flow, Observation is added by the system, not parsed.
    
    Args:
        text: The text containing observation
        
    Returns:
        str: The observation content, or None if not found
    """
    pattern = r"Observation:\s*(.+?)(?:\n(?:Thought|Action|Final Answer):|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

def test_parsers():
    """Test all parser functions with sample data"""
    print("="*60)
    print("TESTING PARSERS")
    print("="*60)
    
    # Test 1: Parse Thought
    sample1 = """
    Thought: I need to find the population of Vietnam
    Action: search("Vietnam population 2024")
    """
    thought = parse_thought(sample1)
    print(f"\nTest 1 - Parse Thought:")
    print(f"  Input: {sample1.strip()}")
    print(f"  Result: '{thought}'")
    assert thought == "I need to find the population of Vietnam", f"Expected 'I need to find...', got '{thought}'"
    print("  [OK]")
    
    # Test 2: Parse Action with parentheses
    action = parse_action(sample1)
    print(f"\nTest 2 - Parse Action:")
    print(f"  Input: {sample1.strip()}")
    print(f"  Result: {action}")
    assert action == {'tool': 'search', 'args': 'Vietnam population 2024'}, f"Action parsing failed"
    print("  [OK]")
    
    # Test 3: Parse Final Answer
    sample2 = """
    Thought: I have enough information now
    Final Answer: Vietnam has 98.5 million people in 2024
    """
    final = parse_final_answer(sample2)
    print(f"\nTest 3 - Parse Final Answer:")
    print(f"  Input: {sample2.strip()}")
    print(f"  Result: '{final}'")
    assert final == "Vietnam has 98.5 million people in 2024", f"Final answer parsing failed"
    print("  [OK]")
    
    # Test 4: Check has_final_answer
    print(f"\nTest 4 - Has Final Answer:")
    print(f"  sample1 has final answer: {has_final_answer(sample1)}")
    print(f"  sample2 has final answer: {has_final_answer(sample2)}")
    assert not has_final_answer(sample1), "sample1 should not have final answer"
    assert has_final_answer(sample2), "sample2 should have final answer"
    print("  [OK]")
    
    # Test 5: Action with calculation
    sample3 = "Action: calculate(100 + 200)"
    action3 = parse_action(sample3)
    print(f"\nTest 5 - Parse Action with Math:")
    print(f"  Input: {sample3}")
    print(f"  Result: {action3}")
    assert action3 == {'tool': 'calculate', 'args': '100 + 200'}, f"Math action parsing failed"
    print("  [OK]")
    
    # Test 6: Multiple sections
    sample4 = """
    Thought: First search
    Action: search("test")
    Observation: Found results
    Thought: Now I have the answer
    Final Answer: The result is 42
    """
    thought4 = parse_thought(sample4)
    action4 = parse_action(sample4)
    final4 = parse_final_answer(sample4)
    
    print(f"\nTest 6 - Complex Multi-section:")
    print(f"  Thought: '{thought4}'")
    print(f"  Action: {action4}")
    print(f"  Final Answer: '{final4}'")
    assert thought4 == "First search", f"Multi-section thought failed"
    assert action4 == {'tool': 'search', 'args': 'test'}, f"Multi-section action failed"
    assert final4 == "The result is 42", f"Multi-section final answer failed"
    print("  [OK]")
    
    print("\n" + "="*60)
    print("ALL PARSER TESTS PASSED!")
    print("="*60)
    print("\nParsers are ready to use in the agent.")
    

if __name__ == "__main__":
    test_parsers()
