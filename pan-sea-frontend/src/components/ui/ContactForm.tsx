import React, { useState } from 'react';
import { FaPaperPlane } from 'react-icons/fa';

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  message: string;
}

interface ContactFormProps {
  onSubmit?: (data: FormData) => Promise<void>;
  title?: string;
  className?: string;
}

export default function ContactForm({ 
  onSubmit, 
  title = "Send us a Message",
  className = ""
}: ContactFormProps) {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    subject: '',
    category: 'general',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      if (onSubmit) {
        await onSubmit(formData);
      } else {
        // Default behavior - simulate form submission
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      setIsSubmitted(true);
      setFormData({
        name: '',
        email: '',
        subject: '',
        category: 'general',
        message: ''
      });
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setIsSubmitted(false);
    setFormData({
      name: '',
      email: '',
      subject: '',
      category: 'general',
      message: ''
    });
  };

  return (
    <div className={`bg-white rounded-3xl p-8 shadow-xl ${className}`}>
      <h3 className="text-3xl font-bold text-slate-900 mb-6">{title}</h3>
      
      {isSubmitted ? (
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <FaPaperPlane className="text-3xl text-emerald-600" />
          </div>
          <h4 className="text-2xl font-semibold text-slate-900 mb-4">Message Sent!</h4>
          <p className="text-slate-600 mb-6">Thank you for contacting us. We'll get back to you within 24 hours.</p>
          <button 
            onClick={resetForm}
            className="px-6 py-3 bg-sky-600 text-white rounded-xl font-semibold hover:bg-sky-700 transition-colors"
          >
            Send Another Message
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="name" className="block text-sm font-semibold text-slate-700 mb-2">
                Full Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all duration-200"
                placeholder="Your full name"
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-slate-700 mb-2">
                Email Address *
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all duration-200"
                placeholder="your@email.com"
              />
            </div>
          </div>
          
          <div>
            <label htmlFor="category" className="block text-sm font-semibold text-slate-700 mb-2">
              Category
            </label>
            <select
              id="category"
              name="category"
              value={formData.category}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all duration-200"
            >
              <option value="general">General Inquiry</option>
              <option value="support">Technical Support</option>
              <option value="billing">Billing Question</option>
              <option value="feature">Feature Request</option>
              <option value="bug">Bug Report</option>
              <option value="partnership">Partnership</option>
            </select>
          </div>
          
          <div>
            <label htmlFor="subject" className="block text-sm font-semibold text-slate-700 mb-2">
              Subject *
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleInputChange}
              required
              className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all duration-200"
              placeholder="Brief subject of your message"
            />
          </div>
          
          <div>
            <label htmlFor="message" className="block text-sm font-semibold text-slate-700 mb-2">
              Message *
            </label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleInputChange}
              required
              rows={6}
              className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all duration-200 resize-none"
              placeholder="Tell us more about how we can help you..."
            />
          </div>
          
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-4 bg-gradient-to-r from-sky-600 to-blue-700 text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Sending...
              </>
            ) : (
              <>
                <FaPaperPlane className="text-lg" />
                Send Message
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
}

export type { FormData as ContactFormData };
