from .base import wrap_with_json_contract


class SocialStudiesPromptGenerator:
    """Generate Social Studies-focused prompts for summaries, study questions, and key points.

    The three methods mirror the previous standalone functions but tailor the
    instructions for Social Studies topics (history, civics, geography,
    economics, culture, and political analysis).
    """

    @staticmethod
    def generate_class_summary_prompt(transcription: str) -> str:
        instructions = """
        You are an expert Social Studies educational assistant (history, civics, geography, economics, culture). Create a comprehensive, student-focused summary emphasizing historical context, causation, geographic and cultural factors, and civic implications.

        Focus areas:
        - Chronology & Causation: how events and ideas influenced one another
        - Key Actors & Institutions: people, groups, and governing bodies
        - Geographic Context: locations, spatial relationships, and resources
        - Political & Economic Implications: policies, systems, outcomes
        - Cultural Perspectives: beliefs, norms, and differing interpretations

        Output structure guidance (content only, not headings): opening/context; body with key events/ideas and evidence; connections to prior lessons/broader themes/present relevance; conclusion with takeaways and civic implications.

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
        You are a Social Studies assessment designer. Create 6-8 high-quality study questions that build historical reasoning, source analysis, and civic understanding.

        Distribution guidance:
        - Knowledge & Comprehension (2-3): recall key facts, dates, definitions, actors
        - Application & Analysis (2-3): causes/effects, comparisons across regions/periods, primary-source interpretation
        - Synthesis & Evaluation (1-2): evaluate impacts, connect to present-day civic issues

        Quality:
        - Reference specific details from the provided summary
        - Mix short-answer, document-analysis, and essay-style prompts
        - Order from foundational recall to higher-order analysis

        Output schema:
        - JSON array of 6-8 strings, each string is a self-contained question
        """
        return wrap_with_json_contract(instructions, summary, return_type="array", language="English")

    @staticmethod
    def generate_key_points_prompt(transcription: str) -> str:
        instructions = """
        You are a Social Studies content analyst. Extract essential key points prioritizing events, actors, causation, geography/culture, and civic implications.

        Focus areas:
        - Core Events & Chronology: key dates, sequences, turning points
        - Actors & Institutions: leaders, movements, organizations
        - Causes & Consequences: short- and long-term effects and drivers
        - Geographic/Cultural Context: locations, spatial patterns, cultural influences
        - Civic Relevance: policy implications, rights, governance, modern connections

        Output schema:
        - JSON object with fields:
          - "key_points": string[] (8-15 concise items; include dates/examples when present)
          - "topics_discussed": string[]
          - "learning_objectives": string[]
          - "homework": string[]
          - "announcements": string[]
          - "next_class_preview": string|null
        """
        return wrap_with_json_contract(instructions, transcription, return_type="object", language="English")


