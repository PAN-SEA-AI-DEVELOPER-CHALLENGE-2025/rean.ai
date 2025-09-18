from typing import List, Optional, Any
from openai import OpenAI
import json
import logging
from app.config import settings
from app.utils.prompt_template import generate_class_summary_prompt, generate_study_questions_prompt, generate_key_points_prompt
from app.utils.response_cleaner import (
    clean_and_validate_summary,
    clean_and_validate_questions, 
    clean_and_validate_key_points
)
# client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
# Initialize Sea Lion AI client using OpenAI-compatible client
client = OpenAI(
    api_key=settings.sea_lion_api_key,
    base_url=settings.sea_lion_base_url
) if settings.sea_lion_api_key else None

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered text processing and summarization"""
    
    def __init__(self):
        self.client = client
        # self.model = settings.openai_model
        self.model = settings.sea_lion_model
    
    async def generate_class_summary(
        self,
        transcription: str,
        subject: str = None,
    ) -> dict:
        """Generate a comprehensive class summary from transcription"""
        
        if not self.client:
            raise ValueError("Sea Lion AI API key not configured")

        prompt = generate_class_summary_prompt(
            transcription=transcription,
            subject=subject
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational assistant that creates detailed, structured summaries of class sessions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            summary_text = response.choices[0].message.content
            
            # Clean and validate the response
            return clean_and_validate_summary(summary_text)
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    async def extract_key_points(self, transcription: str, subject: str = None) -> dict:
        """Extract key points from transcription"""
        
        if not self.client:
            raise ValueError("Sea Lion AI API key not configured")

        prompt = generate_key_points_prompt(transcription=transcription, subject=subject)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting key educational points from class transcriptions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            key_points_text = response.choices[0].message.content
            
            # Clean and validate the response
            return clean_and_validate_key_points(key_points_text)
                
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return {
                "key_points": [],
                "topics_discussed": [],
                "learning_objectives": [],
                "homework": [],
                "announcements": [],
                "next_class_preview": None
            }
    
    async def generate_study_questions(self, summary: str, subject: str = None) -> List[str]:
        """Generate study questions based on the class summary"""
        
        if not self.client:
            raise ValueError("Sea Lion AI API key not configured")
        
        prompt = generate_study_questions_prompt(summary=summary, subject=subject)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator who creates effective study questions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            questions_text = response.choices[0].message.content
            
            # Clean and validate the response
            return clean_and_validate_questions(questions_text)
                
        except Exception as e:
            logger.error(f"Error generating study questions: {str(e)}")
            return []


# Global instance
llm_service = LLMService()
