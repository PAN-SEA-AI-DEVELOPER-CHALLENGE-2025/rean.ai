'use client';

import { motion, easeOut } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';

export default function FeaturesSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  const features = [
    // Core Recording & Processing
    {
      icon: (
        // Video Camera Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="3" y="7" width="13" height="10" rx="2" strokeWidth={2} stroke="currentColor" />
          <path d="M16 9l5-3v12l-5-3" strokeWidth={2} stroke="currentColor" strokeLinejoin="round" />
        </svg>
      ),
      title: "Real-time Lecture Recording",
      description: "Record audio/video directly from the teacher's device."
    },
    {
      icon: (
        // Microphone with Text Lines Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="9" y="2" width="6" height="12" rx="3" strokeWidth={2} stroke="currentColor" />
          <path d="M5 10v2a7 7 0 0014 0v-2" strokeWidth={2} stroke="currentColor" />
          <path d="M8 21h8" strokeWidth={2} stroke="currentColor" strokeLinecap="round" />
        </svg>
      ),
      title: "Live Transcription",
      description: "Instant speech-to-text as the lecture happens."
    },
    {
      icon: (
        // User Group Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="7" cy="10" r="3" strokeWidth={2} stroke="currentColor" />
          <circle cx="17" cy="10" r="3" strokeWidth={2} stroke="currentColor" />
          <path d="M2 20c0-2.5 3-4.5 5-4.5s5 2 5 4.5" strokeWidth={2} stroke="currentColor" />
          <path d="M12 20c0-2.5 3-4.5 5-4.5s5 2 5 4.5" strokeWidth={2} stroke="currentColor" />
        </svg>
      ),
      title: "Speaker Identification",
      description: "Differentiate between teacher and student questions."
    },
    {
      icon: (
        // Clock Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="9" strokeWidth={2} stroke="currentColor" />
          <path d="M12 7v5l3 3" strokeWidth={2} stroke="currentColor" strokeLinecap="round" />
        </svg>
      ),
      title: "Timestamped Segments",
      description: "Each transcript line is linked to the exact time in the lecture."
    },
    // AI-Powered Learning Tools
    {
      icon: (
        // Sparkle/Stars Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M12 3v3M12 18v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M3 12h3M18 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12" strokeWidth={2} stroke="currentColor" strokeLinecap="round" />
          <circle cx="12" cy="12" r="4" strokeWidth={2} stroke="currentColor" />
        </svg>
      ),
      title: "Auto Summarization",
      description: "Generate section-wise and full-lecture summaries."
    },
    {
      icon: (
        // Chat Bubble with Question Mark Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" strokeWidth={2} stroke="currentColor" />
          <path d="M12 8a2 2 0 012 2c0 1-2 1.5-2 3" strokeWidth={2} stroke="currentColor" strokeLinecap="round" />
          <circle cx="12" cy="16" r="1" fill="currentColor" />
        </svg>
      ),
      title: "Natural Language Q&A",
      description: "Students can ask questions about the lecture and get AI-generated answers based only on lecture content."
    },
    {
      icon: (
        // Key Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="15" cy="9" r="3" strokeWidth={2} stroke="currentColor" />
          <path d="M2 22l7-7" strokeWidth={2} stroke="currentColor" strokeLinecap="round" />
          <path d="M7 15v4h4" strokeWidth={2} stroke="currentColor" strokeLinecap="round" />
        </svg>
      ),
      title: "Keyword & Concept Extraction",
      description: "Highlight key terms, definitions, and concepts."
    },
    {
      icon: (
        // Quiz/Clipboard Icon
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="5" y="3" width="14" height="18" rx="2" strokeWidth={2} stroke="currentColor" />
          <path d="M9 7h6M9 11h6M9 15h2" strokeWidth={2} stroke="currentColor" strokeLinecap="round" />
        </svg>
      ),
      title: "Quiz Generator",
      description: "Create quizzes (MCQ, true/false, short answer) from the lecture."
    },
    {
      icon: (
        // Flashcard Icon (Stacked Cards)
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <rect x="3" y="7" width="18" height="10" rx="2" strokeWidth={2} stroke="currentColor" />
          <rect x="7" y="3" width="10" height="4" rx="1" strokeWidth={2} stroke="currentColor" />
        </svg>
      ),
      title: "Flashcard Creator",
      description: "Turn key points into study flashcards."
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { 
      opacity: 0, 
      y: 50,
      scale: 0.9
    },
    visible: { 
      opacity: 1, 
      y: 0,
      scale: 1,
      transition: {
        duration: 0.6,
        ease: easeOut
      }
    }
  };

  const headerVariants = {
    hidden: { 
      opacity: 0, 
      y: 30 
    },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.8,
        ease: easeOut
      }
    }
  };

  return (
    <section ref={ref} className="py-20 bg-slate-50">
      <div className="mx-auto max-w-7xl px-6">
        <motion.div 
          className="text-center mb-16"
          variants={headerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
            Why Rean.AI?
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Rean.AI is your always-present study companion—capturing every word from 
            your teacher, turning it into clear summaries, and helping you understand 
            lessons anytime. No more missed notes, no more confusion—just learning made 
            easier for everyone.
          </p>
        </motion.div>
        
        <motion.div 
          className="grid md:grid-cols-3 gap-8"
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
        >
          {features.map((feature, index) => (
            <motion.div 
              key={index} 
              className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-all duration-300 hover:scale-105"
              variants={itemVariants}
              whileHover={{ 
                y: -5,
                transition: { duration: 0.2 }
              }}
            >
              <motion.div 
                className="w-12 h-12 bg-sky-100 rounded-lg flex items-center justify-center text-sky-600 mb-6"
                whileHover={{ 
                  scale: 1.1,
                  rotate: 5,
                  transition: { duration: 0.2 }
                }}
              >
                {feature.icon}
              </motion.div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-slate-600 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
