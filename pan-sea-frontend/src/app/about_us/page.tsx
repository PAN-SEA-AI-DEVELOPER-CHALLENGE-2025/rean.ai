"use client";

import { FaGraduationCap, FaUsers, FaLightbulb, FaRocket, FaHeart, FaGlobe } from "react-icons/fa";

export default function AboutUsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-sky-50">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white">
        <div className="absolute inset-0 bg-gradient-to-r from-sky-600 to-blue-700 opacity-90"></div>
        <div className="relative max-w-7xl mx-auto px-6 py-24 text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            About Pan-Sea
          </h1>
          <p className="text-xl md:text-2xl text-sky-100 max-w-3xl mx-auto leading-relaxed">
            Revolutionizing education through AI-powered learning experiences and intelligent classroom management
          </p>
          <div className="mt-12 flex flex-wrap justify-center gap-6">
            <div className="flex items-center space-x-2 text-sky-100">
              <FaGraduationCap className="text-2xl" />
              <span className="text-lg">Smart Learning</span>
            </div>
            <div className="flex items-center space-x-2 text-sky-100">
              <FaUsers className="text-2xl" />
              <span className="text-lg">Global Community</span>
            </div>
            <div className="flex items-center space-x-2 text-sky-100">
              <FaLightbulb className="text-2xl" />
              <span className="text-lg">Innovation First</span>
            </div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-6">Our Mission</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              To democratize education by providing cutting-edge AI tools that enhance learning outcomes 
              and empower educators worldwide.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-sky-50 to-blue-50 border border-sky-100">
              <div className="w-16 h-16 bg-sky-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <FaGraduationCap className="text-2xl text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-4">Educational Excellence</h3>
              <p className="text-slate-600">
                We believe every student deserves access to world-class education, regardless of their location or background.
              </p>
            </div>
            
            <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100">
              <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <FaLightbulb className="text-2xl text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-4">Innovation Driven</h3>
              <p className="text-slate-600">
                Continuously pushing the boundaries of what's possible in educational technology and AI applications.
              </p>
            </div>
            
            <div className="text-center p-8 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-100">
              <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <FaHeart className="text-2xl text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-4">Student Centered</h3>
              <p className="text-slate-600">
                Every feature we build is designed with students and educators in mind, ensuring meaningful impact.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Story Section */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-4xl font-bold text-slate-900 mb-6">Our Story</h2>
              <p className="text-lg text-slate-600 mb-6">
                Pan-Sea was born from a simple observation: traditional education systems were struggling to keep up 
                with the rapidly evolving digital landscape. We saw an opportunity to bridge this gap using artificial intelligence.
              </p>
              <p className="text-lg text-slate-600 mb-6">
                What started as a small team of educators and technologists has grown into a global platform that's 
                transforming how students learn and teachers teach. Our journey is marked by continuous innovation, 
                user feedback, and an unwavering commitment to educational excellence.
              </p>
              <p className="text-lg text-slate-600">
                Today, we're proud to serve thousands of educators and students across the world, helping them 
                achieve their educational goals through intelligent, personalized learning experiences.
              </p>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-sky-400 to-blue-600 rounded-3xl p-8 text-white">
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <FaRocket className="text-2xl" />
                    <span className="text-xl font-semibold">2019</span>
                  </div>
                  <p className="text-sky-100">Founded with a vision to revolutionize education</p>
                  
                  <div className="flex items-center space-x-3">
                    <FaUsers className="text-2xl" />
                    <span className="text-xl font-semibold">2021</span>
                  </div>
                  <p className="text-sky-100">First 1000+ educators joined our platform</p>
                  
                  <div className="flex items-center space-x-3">
                    <FaGlobe className="text-2xl" />
                    <span className="text-xl font-semibold">2024</span>
                  </div>
                  <p className="text-sky-100">Expanding globally with AI-powered features</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-6">Our Values</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              The principles that guide everything we do and every decision we make.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-20 h-20 bg-sky-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <FaGraduationCap className="text-3xl text-sky-600" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Excellence</h3>
              <p className="text-slate-600">We strive for excellence in everything we do, from product development to user support.</p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <FaHeart className="text-3xl text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Empathy</h3>
              <p className="text-slate-600">We understand the challenges educators face and design solutions that truly help.</p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <FaLightbulb className="text-3xl text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Innovation</h3>
              <p className="text-slate-600">We constantly explore new technologies and approaches to improve education.</p>
            </div>
            
            <div className="text-center">
              <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <FaUsers className="text-3xl text-amber-600" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Community</h3>
              <p className="text-slate-600">We believe in the power of community and collaboration in education.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-sky-600 to-blue-700">
        <div className="max-w-4xl mx-auto text-center px-6">
          <h2 className="text-4xl font-bold text-white mb-6">Join Us in Shaping the Future of Education</h2>
          <p className="text-xl text-sky-100 mb-8">
            Whether you're an educator looking to enhance your classroom or a student seeking better learning tools, 
            we're here to help you succeed.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="px-8 py-4 bg-white text-sky-600 rounded-xl font-semibold hover:bg-slate-100 transition-colors">
              Get Started Today
            </button>
            <button className="px-8 py-4 border-2 border-white text-white rounded-xl font-semibold hover:bg-white hover:text-sky-600 transition-colors">
              Learn More
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
