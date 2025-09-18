from .base import wrap_with_json_contract


class KhmerPromptGenerator:
    """Generate Khmer-focused prompts for summaries, study questions, and key points.

    Methods are tailored for Khmer language classes: reading comprehension,
    literature, writing, grammar, vocabulary, and speaking/listening activities.
    """

    @staticmethod
    def generate_class_summary_prompt(transcription: str) -> str:
        instructions = """
        អ្នកជាគ្រូភាសាខ្មែរ និងអ្នកវិភាគអក្សរសាស្ត្រ បង្កើតសេចក្ដីសង្ខេបថ្នាក់ដែលច្បាស់ សមរម្យតាមកម្រិតសិស្ស ផ្តោតលើគំនិតសំខាន់ៗ ប្រធានបទ ធាតុអក្សរសាស្ត្រ វាក្យសព្ទ និងសកម្មភាពនិយាយ/សរសេរ។

        ការផ្តោតសំខាន់ៗ:
        - គំនិត និងប្រធានបទសំខាន់ៗ
        - ធាតុអក្សរសាស្ត្រ: តួអង្គ សំពាធរឿង សម្លេងរចនា រូបភាព ប្រៀបធៀប
        - ភាសា និងវាក្យសព្ទ: ពាក្យគន្លឹះ/ឃ្លា និងន័យតាមបរិបទ (បន្ថែមនិយមន័យខ្លីៗ)
        - សកម្មភាពសរសេរ/និយាយ និងអនុសាសន៍កែសម្រួល

        រចនាសម្ព័ន្ធលទ្ធផល (មាតិកាតែប៉ុណ្ណោះ មិនចាំបាច់ដាក់ចំណងជើង): បើកបទ/បរិបទ; កាយកថាផ្តោតលើចំណុចសំខាន់ៗ ឧទាហរណ៍ និងចំណាំភាសា; បញ្ចប់ជាមួយការងារផ្ទះ/យោបល់អនុវត្តបាន។

        ទ្រង់ទ្រាយទិន្នន័យចេញ:
        - JSON object មានវាល៖
          - "summary": string ប្រវែង 150-220 ពាក្យ មិនប្រើ markdown
          - "topics_discussed": string[]
          - "learning_objectives": string[]
          - "homework": string[]
          - "announcements": string[]
          - "next_class_preview": string|null
        """
        return wrap_with_json_contract(instructions, transcription, return_type="object", language="Khmer")

    @staticmethod
    def generate_study_questions_prompt(summary: str) -> str:
        instructions = """
        អ្នកជាអ្នករចនាសំណួរ សូមបង្កើតសំណួរ ៦-៨ ដើម្បីជំរុញ អានយល់ វិភាគអក្សរសាស្រ្ដ វាក្យសព្ទ និងការសរសេរ/កែសម្រួល។

        ការចែកចាយ:
        - អានយល់ (២-៣)
        - វិភាគអក្សរសាស្ត្រ (២-៣)
        - សរសេរ និងភាសា (១-២)

        គុណភាព:
        - រួមបញ្ចូលទម្រង់ខុសៗគ្នា (ជ្រើសរើសចម្លើយ ខ្លី សរសេរក្លឹប)
        - មានយ៉ាងហោចណាស់សំណួរមួយសុំឲ្យកែសម្រួល/សរសេរឡើងវិញខ្លី
        - សំណួរទាំងអស់សរសេរជាភាសាខ្មែរ

        ទ្រង់ទ្រាយទិន្នន័យចេញ:
        - JSON array មានសរសេរ ៦-៨ ឃ្លាសំណួរ (string)
        """
        return wrap_with_json_contract(instructions, summary, return_type="array", language="Khmer")

    @staticmethod
    def generate_key_points_prompt(transcription: str) -> str:
        instructions = """
        អ្នកជាអ្នកវិភាគមាតិកាខ្មែរ សូមស្រង់ចំណុចសំខាន់ៗអំពីប្រធានបទ គំនិត សម្រង់ ធាតុភាសា វាក្យសព្ទ និងអនុសាសន៍សរសេរ។

        តំបន់ផ្តោត:
        - គំនិតមេ និងប្រធានបទ
        - សម្រង់ និងឧទាហរណ៍សំខាន់ៗ
        - ធាតុអក្សរសាស្ត្រ និងលក្ខណៈភាសា
        - វាក្យសព្ទ និងការប្រើប្រាស់តាមបរិបទ
        - គន្លឹះសរសេរ/កែសម្រួល និងការងារផ្ទះ

        ទ្រង់ទ្រាយទិន្នន័យចេញ:
        - JSON object មានវាល៖
          - "key_points": string[] ចំនួន ៨-១៥ ឲ្យខ្លី ច្បាស់ មានប្រយោជន៍សម្រាប់រំលឹក
          - "topics_discussed": string[]
          - "learning_objectives": string[]
          - "homework": string[]
          - "announcements": string[]
          - "next_class_preview": string|null
        """
        return wrap_with_json_contract(instructions, transcription, return_type="object", language="Khmer")


