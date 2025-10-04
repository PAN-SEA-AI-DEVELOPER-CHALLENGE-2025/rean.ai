from .base import wrap_with_json_contract


class MathPromptGenerator:
    """Generate Math-focused prompts for summaries, study questions, and key points.

    The methods are optimized for mathematics content: problem-solving strategies,
    mathematical reasoning, computational skills, formulas, theorems, and real-world
    applications.
    """

    @staticmethod
    def generate_class_summary_prompt(transcription: str) -> str:
        instructions = """
        You are an expert Mathematics educational assistant. Create a clear, student-focused summary emphasizing key concepts, solution methods, reasoning, and computational skills.

        Focus areas:
        - Key Concepts: definitions, theorems, formulas, properties
        - Problem-Solving Strategies: step-by-step methods, algorithms, approaches
        - Mathematical Reasoning: logical connections, proofs, justifications
        - Computational Skills: calculations, applications, procedural fluency
        - Real-World Applications and Common Mistakes

        Output structure guidance: opening with learning objectives and topic context; body explaining concepts, demonstrating solution methods with examples; connections to prior topics; conclusion with skills learned, practice suggestions, and next concepts.

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
        You are a Mathematics assessment designer. Create 6-8 questions reinforcing concepts, problem-solving skills, computational fluency, and reasoning.

        Distribution guidance:
        - Conceptual Understanding (2-3): definitions, properties, theoretical knowledge
        - Procedural Fluency (2-3): step-by-step solving and calculations
        - Application & Reasoning (1-2): word problems, real-world applications, explain why/how

        Quality:
        - Include specific numbers or scenarios where appropriate
        - Include at least one question asking students to explain their reasoning
        - Order from basic recall to higher-order thinking

        Output schema:
        - JSON array of 6-8 strings, each a self-contained question
        """
        return wrap_with_json_contract(instructions, summary, return_type="array", language="English")

    @staticmethod
    def generate_key_points_prompt(transcription: str) -> str:
        instructions = """
        You are a Mathematics content analyst. Extract essential key points prioritizing concepts, formulas, problem-solving methods, and computational skills.

        Focus areas:
        - Key Concepts & Definitions; Formulas & Theorems
        - Problem-Solving Methods (step-by-step)
        - Computational Skills; Common Mistakes & Tips
        - Real-World Applications

        Output schema:
        - JSON object with fields:
          - "key_points": string[] (8-15 concise items; include formulas/properties/method steps when present)
          - "topics_discussed": string[]
          - "learning_objectives": string[]
          - "homework": string[]
          - "announcements": string[]
          - "next_class_preview": string|null
        """
        return wrap_with_json_contract(instructions, transcription, return_type="object", language="English")


