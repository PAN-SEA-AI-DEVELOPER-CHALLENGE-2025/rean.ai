from .base import wrap_with_json_contract


class SciencePromptGenerator:
    """Generate Science-focused prompts for summaries, study questions, and key points.

    The methods are optimized for scientific content: hypotheses, methods,
    data interpretation, experimental design, and real-world applications.
    """

    @staticmethod
    def generate_class_summary_prompt(transcription: str) -> str:
        instructions = """
        You are an expert Science educational assistant (biology, chemistry, physics, earth science). Create a clear, evidence-focused summary emphasizing hypotheses, methods, results, and real-world implications.

        Focus areas:
        - Scientific Question & Hypotheses
        - Methods & Procedures: design, variables, controls
        - Data & Evidence: observations, results, interpretation
        - Conceptual Models & Theories
        - Applications, Limitations, and Sources of Uncertainty

        Output structure guidance: opening with research question/goals/context; body with methods, data highlights, conceptual explanations; connections to prior concepts; conclusion with main findings, significance, and next investigations.

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
        You are a Science assessment designer. Create 6-8 questions reinforcing scientific reasoning, experimental design, data interpretation, and application.

        Distribution guidance:
        - Knowledge & Comprehension (2-3): definitions, facts, core concepts
        - Application & Analysis (2-3): interpret data/graphs, analyze design
        - Synthesis & Evaluation (1-2): propose follow-up experiments, evaluate evidence

        Quality:
        - Include data-interpretation and troubleshooting prompts
        - Mix MCQ, short-answer calculation, and open-ended design items
        - Emphasize controls, variables, and sources of error where relevant

        Output schema:
        - JSON array of 6-8 strings, each a self-contained question
        """
        return wrap_with_json_contract(instructions, summary, return_type="array", language="English")

    @staticmethod
    def generate_key_points_prompt(transcription: str) -> str:
        instructions = """
        You are a Science content analyst. Extract essential key points prioritizing hypotheses, methods, data, and conceptual implications.

        Focus areas:
        - Research Question & Hypotheses
        - Methods & Key Procedures
        - Major Results & Data Patterns
        - Interpretations & Theoretical Links
        - Limitations & Next Steps

        Output schema:
        - JSON object with fields:
          - "key_points": string[] (8-15 concise, evidence-focused items; include measurements/units/trends when present)
          - "topics_discussed": string[]
          - "learning_objectives": string[]
          - "homework": string[]
          - "announcements": string[]
          - "next_class_preview": string|null
        """
        return wrap_with_json_contract(instructions, transcription, return_type="object", language="English")


