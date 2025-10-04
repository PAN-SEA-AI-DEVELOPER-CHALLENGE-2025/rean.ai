'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import { BookOpen, Mic, Brain, FolderOpen, Star, ArrowRight, CheckCircle, PlayCircle, Users, Shield } from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

const guideSteps = [
  {
    id: 1,
    title: "Getting Started",
    icon: PlayCircle,
    color: "from-blue-500 to-blue-600",
    bgColor: "bg-blue-50",
    textColor: "text-blue-700",
    content: [
      "Sign up for a demo account by clicking start, then click sign in - we've already set up a placeholder for you",
      "Explore the dashboard to familiarize yourself with the interface"
    ]
  },
  {
    id: 2,
    title: "Creating Your First Class",
    icon: BookOpen,
    color: "from-blue-600 to-blue-700",
    bgColor: "bg-blue-100",
    textColor: "text-blue-800",
    content: [
      "Click the 'Create New Class' button on your dashboard",
      "Fill in class details: title, subject, grade level, and classroom",
      "Set your class schedule with start and end times",
      "Save your class and it will appear on your dashboard"
    ]
  },
  {
    id: 3,
    title: "Recording Audio Lessons",
    icon: Mic,
    color: "from-blue-500 to-blue-600",
    bgColor: "bg-blue-50",
    textColor: "text-blue-700",
    content: [
      "Navigate to your class and click 'Record Lesson' or 'Upload Lesson'",
      "Allow microphone permissions when prompted",
      "Click the record button to start recording your lesson",
      "Speak clearly and at a moderate pace for best transcription results",
      "Click stop when your lesson is complete"
    ]
  },
  {
    id: 4,
    title: "AI-Powered Transcription & Summaries",
    icon: Brain,
    color: "from-blue-600 to-blue-700",
    bgColor: "bg-blue-100",
    textColor: "text-blue-800",
    content: [
      "After recording, our AI automatically transcribes your audio and summary for you",
      "Key topics and concepts are extracted automatically",
    ]
  },
  {
    id: 5,
    title: "Managing Your Content",
    icon: FolderOpen,
    color: "from-blue-500 to-blue-600",
    bgColor: "bg-blue-50",
    textColor: "text-blue-700",
    content: [
      "View all your lessons and summaries in the class dashboard",
      "Search through your content using keywords or topics",
    ]
  },
  {
    id: 6,
    title: "Advanced Features",
    icon: Star,
    color: "from-blue-600 to-blue-700",
    bgColor: "bg-blue-100",
    textColor: "text-blue-800",
    content: [
      "Use the RAG (Retrieval-Augmented Generation) feature for intelligent Q&A",
      "Generate custom quizzes and assignments from your lesson content",
      "Create study guides automatically from multiple lessons",
      "Integrate with your existing learning management system"
    ]
  }
];

export default function UserGuidePage() {

  return (
    <div className="min-h-screen bg-white">
      <Header />
      
      <main className="py-16">
        <div className="max-w-7xl mx-auto px-6">

          {/* Step-by-Step Guide */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-slate-900 mb-4">
                Step-by-Step Tutorial
              </h2>
              <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                Follow these comprehensive steps to get the most out of REAN.AI
              </p>
            </div>
            
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {guideSteps.map((step, index) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    key={step.id}
                    className="bg-white rounded-3xl p-8 shadow-lg border border-slate-100 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 group"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                  >
                    <div className="text-center mb-6">
                      <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl ${step.bgColor} mb-4 group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className={`w-8 h-8 ${step.textColor}`} />
                      </div>
                      <div className="text-sm font-semibold text-blue-600 mb-2">Step {step.id}</div>
                      <h3 className="text-xl font-bold text-slate-900">{step.title}</h3>
                    </div>
                    <ul className="space-y-3">
                      {step.content.map((item, itemIndex) => (
                        <li key={itemIndex} className="flex items-start gap-3 text-slate-600">
                          <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm leading-relaxed">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>

          {/* Features Overview */}
          <motion.div
            className="mt-20"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <div className="text-center mb-12">
              <h3 className="text-3xl font-bold text-slate-900 mb-4">
                Why Choose REAN.AI?
              </h3>
              <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                Discover the powerful features that make REAN.AI the perfect tool for modern educators
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="text-xl font-bold text-slate-900 mb-3">AI-Powered Intelligence</h4>
                <p className="text-slate-600">Advanced AI automatically transcribes, summarizes, and extracts key concepts from your lessons</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Users className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="text-xl font-bold text-slate-900 mb-3">Team Collaboration</h4>
                <p className="text-slate-600">Share lessons, collaborate with colleagues, and create a comprehensive knowledge base</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="text-xl font-bold text-slate-900 mb-3">Secure & Private</h4>
                <p className="text-slate-600">Enterprise-grade security ensures your content and student data are always protected</p>
              </div>
            </div>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
