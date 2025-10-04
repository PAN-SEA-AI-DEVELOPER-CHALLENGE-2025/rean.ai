from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import re


def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())


def convert_uuids_to_strings(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert UUID fields to strings for JSON serialization"""
    if 'id' in data and data['id'] is not None:
        data['id'] = str(data['id'])
    if 'teacher_id' in data and data['teacher_id'] is not None:
        data['teacher_id'] = str(data['teacher_id'])
    if 'students' in data:
        for student in data['students']:
            if 'id' in student and student['id'] is not None:
                student['id'] = str(student['id'])
    return data


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds}s"


def format_file_size(bytes_size: int) -> str:
    """Format file size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing/replacing invalid characters"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = f"file_{generate_uuid()[:8]}"
    
    return filename


def parse_time_range(start_time: str, end_time: Optional[str] = None) -> Dict[str, Any]:
    """Parse time range strings and validate"""
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            if end_dt <= start_dt:
                return {
                    "valid": False,
                    "error": "End time must be after start time"
                }
            duration = int((end_dt - start_dt).total_seconds())
        else:
            end_dt = None
            duration = None
        
        return {
            "valid": True,
            "start_time": start_dt,
            "end_time": end_dt,
            "duration": duration
        }
        
    except ValueError as e:
        return {
            "valid": False,
            "error": f"Invalid time format: {str(e)}"
        }


def extract_keywords(text: str, max_keywords: int = 10) -> list:
    """Extract keywords from text (simple implementation)"""
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out stop words
    keywords = [word for word in words if word not in stop_words]
    
    # Count frequency
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_keywords[:max_keywords]]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    # Try to break at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.7:  # If we can break at a reasonable word boundary
        truncated = truncated[:last_space]
    
    return truncated + suffix


def sanitize_s3_metadata(metadata: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitize metadata for S3 upload by removing or replacing non-ASCII characters.
    S3 metadata can only contain ASCII characters.
    """
    sanitized = {}
    
    for key, value in metadata.items():
        if isinstance(value, str):
            # Replace non-ASCII characters with ASCII equivalents or remove them
            # Keep basic punctuation and alphanumeric characters
            sanitized_value = ""
            for char in value:
                if ord(char) < 128:  # ASCII character
                    sanitized_value += char
                else:
                    # Replace common non-ASCII characters with ASCII equivalents
                    if char == '•':
                        sanitized_value += '-'
                    elif char == '"' or char == '"':
                        sanitized_value += '"'
                    elif char == '"' or char == '"':
                        sanitized_value += '"'
                    elif char == '' or char == '':
                        sanitized_value += "'"
                    elif char == '' or char == '':
                        sanitized_value += "'"
                    elif char == '–' or char == '—':
                        sanitized_value += '-'
                    elif char == '…':
                        sanitized_value += '...'
                    # For other non-ASCII characters, just skip them
                    # You could also use: sanitized_value += '?'
            
            sanitized[key] = sanitized_value.strip()
        else:
            # Convert non-string values to string and sanitize
            sanitized[key] = str(value)
    
    return sanitized
