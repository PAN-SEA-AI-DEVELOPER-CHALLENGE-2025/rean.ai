
"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { FaQuestionCircle, FaChevronDown, FaChevronUp, FaGraduationCap, FaUsers, FaShieldAlt, FaHeadset, FaCreditCard, FaRocket } from "react-icons/fa";

const faqs = [
  {
    question: 'What is Rean.AI?',
    answer: 'Rean.AI is an AI-powered classroom assistant that records lectures, creates clear summaries, and allows students to ask questions anytime. It ensures no detail is lost, helping students learn better and teachers save time.',
    icon: FaGraduationCap,
    color: 'from-sky-500 to-blue-600'
  },
  {
    question: 'How do I get started with Rean.AI?',
    answer: 'Getting started is simple! Click the "Register" button, create your free account, and you’ll instantly have access to our demo classes, summaries, and smart Q&A features. You can explore right away without setup.',
    icon: FaRocket,
    color: 'from-emerald-500 to-teal-600'
  },
  {
    question: 'Is Rean.AI free to use?',
    answer: 'Yes! Rean.AI offers a free tier with access to lecture recordings, summaries, and basic Q&A. For advanced features like flashcards, quizzes, and detailed analytics, we also provide affordable premium plans.',
    icon: FaCreditCard,
    color: 'from-purple-500 to-indigo-600'
  },
  {
    question: 'Who can use Rean.AI?',
    answer: 'Rean.AI is built for students, teachers, and schools. Students can review lessons and ask questions anytime, while teachers gain tools to save time, understand student struggles, and improve classroom outcomes.',
    icon: FaUsers,
    color: 'from-amber-500 to-orange-600'
  },
  {
    question: 'Is my data secure on Rean.AI?',
    answer: 'Absolutely! We take privacy seriously. All recordings and transcripts are encrypted, protected with secure access, and never shared without consent. Rean.AI follows strict data protection standards to keep you safe.',
    icon: FaShieldAlt,
    color: 'from-red-500 to-pink-600'
  },
  {
    question: 'How can I get support?',
    answer: 'You can contact us anytime through our Help Center, send us an email at support@rean.ai, or use the in-app chat. Our team is always ready to help you make the most of your learning experience.',
    icon: FaHeadset,
    color: 'from-cyan-500 to-blue-600'
  }
];


export default function FAQPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const handleToggle = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-sky-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white">
        <div className="absolute inset-0 bg-gradient-to-r from-sky-600 to-blue-700 opacity-90"></div>
        <div className="relative max-w-7xl mx-auto px-6 py-24 text-center">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center">
              <FaQuestionCircle className="text-4xl text-white" />
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Frequently Asked Questions
          </h1>
          <p className="text-xl md:text-2xl text-sky-100 max-w-3xl mx-auto leading-relaxed">
            Find answers to common questions about Pan-Sea's features, pricing, and how to get the most out of our platform
          </p>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-6">
          <div className="space-y-6">
            {faqs.map((faq, idx) => {
              const IconComponent = faq.icon;
              const isOpen = openIndex === idx;
              
              return (
                <div 
                  key={idx} 
                  className={`rounded-2xl border-2 transition-all duration-300 ${
                    isOpen 
                      ? 'border-sky-200 shadow-xl bg-gradient-to-r from-sky-50 to-blue-50' 
                      : 'border-slate-200 shadow-lg bg-white hover:border-sky-300 hover:shadow-xl'
                  }`}
                >
                  <button
                    className="w-full text-left p-6 focus:outline-none focus:ring-4 focus:ring-sky-100 rounded-2xl"
                    onClick={() => handleToggle(idx)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-full bg-gradient-to-r ${faq.color} flex items-center justify-center flex-shrink-0`}>
                          <IconComponent className="text-xl text-white" />
                        </div>
                        <h3 className="font-semibold text-xl text-slate-900 pr-4">
                          {faq.question}
                        </h3>
                      </div>
                      <div className="flex-shrink-0">
                        {isOpen ? (
                          <FaChevronUp className="text-sky-500 text-xl" />
                        ) : (
                          <FaChevronDown className="text-slate-400 text-xl" />
                        )}
                      </div>
                    </div>
                  </button>
                  
                  {isOpen && (
                    <div className="px-6 pb-6 animate-in slide-in-from-top-2 duration-200">
                      <div className="ml-16 pt-2 border-t border-sky-100">
                        <p className="text-slate-700 text-lg leading-relaxed pt-4">
                          {faq.answer}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
           <div className='flex justify-center mt-10'>
            <button className="bg-sky-600 text-white rounded-xl font-semibold p-4 transition-colors">
                <Link href="/">
                   Back to Home
                </Link>

            </button>
           </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-sky-600 to-blue-700">
        <div className="max-w-4xl mx-auto text-center px-6">
          <h2 className="text-4xl font-bold text-white mb-6">Still Have Questions?</h2>
          <p className="text-xl text-sky-100 mb-8">
            Our support team is here to help! Don't hesitate to reach out if you need assistance or have specific questions about using Pan-Sea.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-8 py-4 bg-white text-sky-600 rounded-xl font-semibold hover:bg-slate-100 transition-colors">
              Contact Support
            </button>
            <button className="px-8 py-4 border-2 border-white text-white rounded-xl font-semibold hover:bg-white hover:text-sky-600 transition-colors">
              Browse Help Center
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
