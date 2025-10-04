from .english import EnglishPromptGenerator
from .khmer import KhmerPromptGenerator
from .math import MathPromptGenerator
from .science import SciencePromptGenerator
from .social_studies import SocialStudiesPromptGenerator

SUBJECT_PROMPT_GENERATORS = {
    "math": MathPromptGenerator,
    "mathematics": MathPromptGenerator,
    "language_arts": EnglishPromptGenerator,
    "literature": EnglishPromptGenerator,
    "english": EnglishPromptGenerator,
    "science": SciencePromptGenerator,
    "earth_science": SciencePromptGenerator,
    "biology": SciencePromptGenerator,
    "chemistry": SciencePromptGenerator,
    "physics": SciencePromptGenerator,
    "khmer": KhmerPromptGenerator,
    "social_studies": SocialStudiesPromptGenerator,
    "history": SocialStudiesPromptGenerator,
    "geography": SocialStudiesPromptGenerator,
    "civics": SocialStudiesPromptGenerator,
}


def get_prompt_generator(subject: str):
    """Get the appropriate prompt generator class based on subject"""
    if not subject:
        return EnglishPromptGenerator  # Default fallback
    subject_lower = subject.lower().strip().replace(" ", "_")
    return SUBJECT_PROMPT_GENERATORS.get(subject_lower, EnglishPromptGenerator)


def generate_class_summary_prompt(transcription: str, subject: str = None) -> str:
    """Generate class summary prompt based on subject"""
    generator = get_prompt_generator(subject)
    return generator.generate_class_summary_prompt(transcription)


def generate_study_questions_prompt(summary: str, subject: str = None) -> str:
    """Generate study questions prompt based on subject"""
    generator = get_prompt_generator(subject)
    return generator.generate_study_questions_prompt(summary)


def generate_key_points_prompt(transcription: str, subject: str = None) -> str:
    """Generate key points prompt based on subject"""
    generator = get_prompt_generator(subject)
    return generator.generate_key_points_prompt(transcription)


