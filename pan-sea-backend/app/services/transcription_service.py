import aiohttp
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for audio transcription using external Whisper API"""
    
    def __init__(self):
        self.base_url = settings.transcription_service_url
        self.timeout = aiohttp.ClientTimeout(total=settings.transcription_service_timeout)
    
    async def transcribe_audio(
        self, 
        file_path: str, 
        language: str = "english",
        task: str = "transcribe"
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using external API
        
        Args:
            file_path: Path to the audio file
            language: "english" or "khmer"
            task: Task type (default: "transcribe")
        
        Returns:
            Dict containing transcription result or None if failed
        """
        try:
            # Validate language
            if language not in ["english", "khmer"]:
                raise ValueError(f"Unsupported language: {language}. Use 'english' or 'khmer'")
            
            # Construct endpoint URL
            endpoint = f"{self.base_url}/transcribe/{language}"
            
            # Prepare file for upload
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            
            logger.info(f"Starting transcription for {file_path} in {language}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                with open(file_path, 'rb') as audio_file:
                    # Prepare multipart form data
                    data = aiohttp.FormData()
                    data.add_field('file', audio_file, 
                                 filename=file_path_obj.name,
                                 content_type='audio/mpeg')
                    data.add_field('task', task)
                    
                    logger.info(f"Sending request to {endpoint}")
                    
                    async with session.post(endpoint, data=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Transcription successful for {file_path}")
                            
                            # Extract transcription text from response
                            # Assuming the API returns a structure with transcription text
                            transcription_text = self._extract_transcription_text(result)
                            
                            return {
                                "success": True,
                                "language": language,
                                "transcription": transcription_text,
                                "raw_response": result
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"Transcription API error {response.status}: {error_text}")
                            return {
                                "success": False,
                                "error": f"API returned status {response.status}: {error_text}",
                                "language": language
                            }
                            
        except aiohttp.ClientError as e:
            logger.error(f"Network error during transcription: {str(e)}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "language": language
            }
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "language": language
            }
    
    def _extract_transcription_text(self, api_response: Dict[str, Any]) -> str:
        """
        Extract transcription text from API response
        
        This method handles different possible response formats from the Whisper API
        """
        try:
            # Common response formats for Whisper APIs:
            # Format 1: {"text": "transcription here"}
            if "text" in api_response:
                return api_response["text"]
            
            # Format 2: {"transcription": "transcription here"}
            if "transcription" in api_response:
                return api_response["transcription"]
            
            # Format 3: {"result": {"text": "transcription here"}}
            if "result" in api_response and isinstance(api_response["result"], dict):
                if "text" in api_response["result"]:
                    return api_response["result"]["text"]
            
            # Format 4: {"segments": [{"text": "part1"}, {"text": "part2"}]}
            if "segments" in api_response and isinstance(api_response["segments"], list):
                segments_text = []
                for segment in api_response["segments"]:
                    if isinstance(segment, dict) and "text" in segment:
                        segments_text.append(segment["text"])
                return " ".join(segments_text)
            
            # If none of the expected formats, try to find any text field
            for key, value in api_response.items():
                if isinstance(value, str) and len(value) > 10:  # Likely transcription text
                    logger.warning(f"Using fallback text extraction from key: {key}")
                    return value
            
            # If all else fails, return the raw response as string
            logger.warning("Could not extract transcription text, returning raw response")
            return str(api_response)
            
        except Exception as e:
            logger.error(f"Error extracting transcription text: {str(e)}")
            return str(api_response)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the transcription service is available"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Try a simple health check endpoint if available
                async with session.get(f"{self.base_url}/health", timeout=10) as response:
                    if response.status == 200:
                        return {"status": "healthy", "service": "transcription"}
                    else:
                        return {"status": "unhealthy", "error": f"Status code: {response.status}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global instance
transcription_service = TranscriptionService()
