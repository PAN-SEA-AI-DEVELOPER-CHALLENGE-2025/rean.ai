import re
import json
from typing import Any, Union, List, Dict


def clean_llm_response(response_text: str) -> str:
    """
    Clean LLM response by removing code blocks, extra formatting, and unwanted characters
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Cleaned response text
    """
    if not response_text:
        return response_text
    
    # Remove code block markers (```json, ```, etc.)
    cleaned = re.sub(r'```(?:json|python|javascript|text)?\s*', '', response_text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    # Remove extra newlines and spaces
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    cleaned = re.sub(r'^\s+', '', cleaned, flags=re.MULTILINE)
    
    return cleaned


def parse_json_response(response_text: str) -> Union[Dict, List, str]:
    """
    Parse JSON response from LLM, handling common formatting issues
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Parsed JSON object, list, or original text if parsing fails
    """
    # First clean the response
    cleaned = clean_llm_response(response_text)
    
    try:
        # Try to parse as JSON
        return json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            # Try to find JSON content within the text
            json_match = re.search(r'(\[.*\]|\{.*\})', cleaned, re.DOTALL)
            if json_match:
                json_content = json_match.group(1)
                return json.loads(json_content)
        except json.JSONDecodeError:
            pass
    
    # If all JSON parsing fails, return the cleaned text
    return cleaned


def extract_list_from_response(response_text: str) -> List[str]:
    """
    Extract a list from LLM response, handling various formats
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        List of strings, empty list if extraction fails
    """
    parsed = parse_json_response(response_text)
    
    if isinstance(parsed, list):
        # Ensure all items are strings
        return [str(item) for item in parsed]
    elif isinstance(parsed, dict):
        # If it's a dict, try to extract values that might be lists
        for value in parsed.values():
            if isinstance(value, list):
                return [str(item) for item in value]
    elif isinstance(parsed, str):
        # Try to extract list-like content from string
        list_match = re.search(r'\[(.*?)\]', parsed, re.DOTALL)
        if list_match:
            items_text = list_match.group(1)
            # Split by commas and clean up
            items = [item.strip().strip('"\'') for item in items_text.split(',')]
            return [item for item in items if item]
    
    return []


def extract_dict_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract a dictionary from LLM response, handling various formats
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Dictionary object, empty dict if extraction fails
    """
    parsed = parse_json_response(response_text)
    
    if isinstance(parsed, dict):
        return parsed
    elif isinstance(parsed, str):
        # Try to extract dict-like content from string
        dict_match = re.search(r'\{(.*?)\}', parsed, re.DOTALL)
        if dict_match:
            try:
                return json.loads(f"{{{dict_match.group(1)}}}")
            except json.JSONDecodeError:
                pass
    
    return {}


def clean_and_validate_summary(response_text: str) -> Dict[str, Any]:
    """
    Clean and validate class summary response from LLM
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Validated summary dictionary with required fields
    """
    summary_dict = extract_dict_from_response(response_text)
    
    # Ensure required fields exist with proper defaults
    validated_summary = {
        "summary": summary_dict.get("summary", ""),
        "topics_discussed": summary_dict.get("topics_discussed", []),
        "learning_objectives": summary_dict.get("learning_objectives", []),
        "homework": summary_dict.get("homework", []),
        "announcements": summary_dict.get("announcements", []),
        "next_class_preview": summary_dict.get("next_class_preview")
    }
    
    # Ensure list fields are actually lists
    for field in ["topics_discussed", "learning_objectives", "homework", "announcements"]:
        if not isinstance(validated_summary[field], list):
            validated_summary[field] = []
    
    return validated_summary


def clean_and_validate_questions(response_text: str) -> List[str]:
    """
    Clean and validate study questions response from LLM
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        List of clean question strings
    """
    questions = extract_list_from_response(response_text)
    
    # Clean up each question
    cleaned_questions = []
    for question in questions:
        if question:
            # Remove any remaining formatting
            clean_question = clean_llm_response(question)
            # Remove category prefixes like "Knowledge & Comprehension:"
            clean_question = re.sub(r'^[^:]+:\s*', '', clean_question)
            if clean_question:
                cleaned_questions.append(clean_question)
    
    return cleaned_questions


def clean_and_validate_key_points(response_text: str) -> Dict[str, Any]:
    """
    Clean and validate key points response from LLM
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Dictionary with key points and related fields
    """
    # Try to extract full structured response first
    key_points_dict = extract_dict_from_response(response_text)
    
    # If we got a structured response, validate and clean it
    if key_points_dict and "key_points" in key_points_dict:
        validated_response = {
            "key_points": key_points_dict.get("key_points", []),
            "topics_discussed": key_points_dict.get("topics_discussed", []),
            "learning_objectives": key_points_dict.get("learning_objectives", []),
            "homework": key_points_dict.get("homework", []),
            "announcements": key_points_dict.get("announcements", []),
            "next_class_preview": key_points_dict.get("next_class_preview")
        }
        
        # Ensure list fields are actually lists and clean them
        for field in ["key_points", "topics_discussed", "learning_objectives", "homework", "announcements"]:
            if not isinstance(validated_response[field], list):
                validated_response[field] = []
            else:
                # Clean each item in the list
                cleaned_items = []
                for item in validated_response[field]:
                    if item:
                        clean_item = clean_llm_response(str(item))
                        if clean_item:
                            cleaned_items.append(clean_item)
                validated_response[field] = cleaned_items
        
        return validated_response
    
    # Fallback: try to extract just key points as list
    key_points = extract_list_from_response(response_text)
    
    # Clean up each key point
    cleaned_points = []
    for point in key_points:
        if point:
            clean_point = clean_llm_response(point)
            if clean_point:
                cleaned_points.append(clean_point)
    
    # Return in expected structure format
    return {
        "key_points": cleaned_points,
        "topics_discussed": [],
        "learning_objectives": [],
        "homework": [],
        "announcements": [],
        "next_class_preview": None
    }
