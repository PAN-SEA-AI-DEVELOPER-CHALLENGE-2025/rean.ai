"use client";

import { FaFileAlt, FaQuestion, FaLightbulb } from "react-icons/fa";

type PrepPromptedOption = {
  id: string;
  title: string;
  description: string;
  icon: typeof FaFileAlt;
  prompt: string;
};

type PrepPromptedOptionsProps = {
  onOptionSelect: (option: PrepPromptedOption) => void;
};

const prepromptedOptions: PrepPromptedOption[] = [
  {
    id: 'summary',
    title: 'Get Summary',
    description: 'Generate a comprehensive summary of the lecture',
    icon: FaFileAlt,
    prompt: 'Please provide a comprehensive summary of this lecture, highlighting the key concepts, main points, and important takeaways.'
  },
  {
    id: 'quiz',
    title: 'Generate Quiz',
    description: 'Create practice questions based on the lecture content',
    icon: FaQuestion,
    prompt: 'Please generate 5-10 practice questions based on this lecture content. Include multiple choice, short answer, and true/false questions.'
  },
  {
    id: 'ideas',
    title: 'Main Ideas',
    description: 'Extract the core concepts and main ideas',
    icon: FaLightbulb,
    prompt: 'Please extract and explain the main ideas and core concepts from this lecture. Focus on the most important takeaways.'
  }
];

export default function PrepPromptedOptions({ onOptionSelect }: PrepPromptedOptionsProps) {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-slate-900 mb-4 text-center">
        How can I help you with this lecture?
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
        {prepromptedOptions.map((option) => (
          <button
            key={option.id}
            onClick={() => onOptionSelect(option)}
            className="p-6 bg-white rounded-xl border border-slate-200 hover:border-sky-300 hover:shadow-lg transition-all duration-200 text-left group"
          >
            <div className="flex items-center space-x-3 mb-3">
              <div className="p-2 bg-sky-100 rounded-lg group-hover:bg-sky-200 transition-colors">
                <option.icon className="text-sky-600" />
              </div>
              <h3 className="font-semibold text-slate-900">{option.title}</h3>
            </div>
            <p className="text-slate-600 text-sm">{option.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
