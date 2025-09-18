from .base import wrap_with_json_contract


class EnglishPromptGenerator:
    """Generate English-focused prompts for summaries, study questions, and key points.

    The methods are optimized for English lessons: reading comprehension,
    literary analysis, writing mechanics, grammar, vocabulary, and speaking/listening
    activities.
    """

    @staticmethod
    def generate_class_summary_prompt(transcription: str) -> str:
        instructions = """
        You are an expert English teacher and literary analyst. Produce a clear, student-friendly summary highlighting main ideas, themes, literary devices, vocabulary, and writing/speaking activities.

        Focus areas:
        - Main Ideas & Themes; Literary Elements (characters, plot, tone, imagery, metaphors)
        - Language & Vocabulary (include brief definitions for advanced terms)
        - Writing/Speaking Activities with actionable feedback; Homework and next steps

        Output structure guidance: opening with lesson objective/context; body with main points, notable excerpts/examples, and language notes; conclusion with actionable feedback, homework, and revision tasks.

        Output schema:
        - JSON object with fields:
          - "summary": string, 150-220 words, no markdown
          - "topics_discussed": string[]
          - "learning_objectives": string[]
          - "homework": string[]
          - "announcements": string[]
          - "next_class_preview": string|null
        """
        return wrap_with_json_contract(instructions, transcription, return_type="object", language="English")

    @staticmethod
    def generate_study_questions_prompt(summary: str) -> str:
        instructions = """
        You are an English assessment designer. Create 6-8 questions reinforcing reading comprehension, literary analysis, grammar, vocabulary usage, and writing skills.

        Distribution guidance:
        - Reading Comprehension (2-3)
        - Literary Analysis (2-3)
        - Writing & Language (1-2), include at least one brief rewrite/revision item

        Quality:
        - Mix multiple-choice, short-answer, and short-essay prompts
        - Include vocabulary-in-context where relevant

        Output schema:
        - JSON array of 6-8 strings, each a self-contained question
        """
        return wrap_with_json_contract(instructions, summary, return_type="array", language="English")

    @staticmethod
    def generate_key_points_prompt(transcription: str) -> str:
        instructions = """
        You are an English content analyst. Extract essential key points prioritizing themes, arguments, language features, and writing guidance.

        Focus areas:
        - Main Ideas & Themes; Important Quotations & Examples
        - Literary Devices & Language Features
        - Vocabulary & Usage Notes (add brief definitions for new words)
        - Writing/Revision Tips & Homework

        Output schema:
        - JSON object with fields:
          - "key_points": string[] (8-15 concise, study-ready items)
          - "topics_discussed": string[]
          - "learning_objectives": string[]
          - "homework": string[]
          - "announcements": string[]
          - "next_class_preview": string|null
        """
        return wrap_with_json_contract(instructions, transcription, return_type="object", language="English")


