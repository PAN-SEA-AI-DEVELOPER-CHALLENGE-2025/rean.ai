"use client";

import React from 'react';
import Link from 'next/link';
import { 
  FaEnvelope, 
  FaPhone, 
  FaMapMarkerAlt, 
  FaClock, 
  FaHeadset, 
  FaComments, 
  FaBug, 
  FaLightbulb,
  FaTwitter,
  FaLinkedin,
  FaFacebook,
  FaGithub
} from "react-icons/fa";

// Import reusable components
import PageHero from '@/components/ui/PageHero';
import ContactMethodCard from '@/components/ui/ContactMethodCard';
import ContactForm, { ContactFormData } from '@/components/ui/ContactForm';
import ContactInfoCard from '@/components/ui/ContactInfoCard';
import CTASection from '@/components/ui/CTASection';
import SocialLinks from '@/components/ui/SocialLinks';

export default function ContactPage() {
  // Handle form submission
  const handleFormSubmit = async (data: ContactFormData) => {
    // Here you would typically send the data to your API
    console.log('Form submitted:', data);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
  };

  const contactMethods = [
    {
      icon: FaHeadset,
      title: "General Support",
      description: "Get help with your account, billing, or general questions",
      action: "Start Chat",
      color: "from-sky-500 to-blue-600",
      bgColor: "from-sky-50 to-blue-50"
    },
    {
      icon: FaBug,
      title: "Report a Bug",
      description: "Found a technical issue? Let us know so we can fix it",
      action: "Report Issue",
      color: "from-red-500 to-pink-600",
      bgColor: "from-red-50 to-pink-50"
    },
    {
      icon: FaLightbulb,
      title: "Feature Request",
      description: "Have an idea for a new feature? We'd love to hear it",
      action: "Share Idea",
      color: "from-amber-500 to-orange-600",
      bgColor: "from-amber-50 to-orange-50"
    },
    {
      icon: FaComments,
      title: "Feedback",
      description: "Share your thoughts on how we can improve Pan-Sea",
      action: "Give Feedback",
      color: "from-emerald-500 to-teal-600",
      bgColor: "from-emerald-50 to-teal-50"
    }
  ];

  const contactInfo = [
    {
      icon: FaEnvelope,
      title: "Email Us",
      content: "duchpanhathun@gmail.com, bunkheangheng99@gmail.com",
      description: "We typically respond within 24 hours",
      color: "sky"
    },
    {
      icon: FaPhone,
      title: "Call Us",
      content: "+855 16 222 054",
      description: "Monday - Sunday",
      color: "emerald"
    },
  ];

  const socialLinks = [
    { icon: FaTwitter, href: "#", label: "Twitter", color: "blue" },
    { icon: FaLinkedin, href: "#", label: "LinkedIn", color: "blue" },
    { icon: FaFacebook, href: "#", label: "Facebook", color: "blue" },
    { icon: FaGithub, href: "#", label: "GitHub", color: "gray" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-sky-50">
      {/* Hero Section */}
      <PageHero
        icon={FaEnvelope}
        title="Get in Touch"
        description="Have questions about Pan-Sea? Need help getting started? We're here to help you succeed in your educational journey."
      />

      {/* Contact Methods */}
      {/* <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 mb-6">How Can We Help?</h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Choose the best way to reach us based on your needs
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {contactMethods.map((method, index) => (
              <ContactMethodCard
                key={index}
                icon={method.icon}
                title={method.title}
                description={method.description}
                action={method.action}
                color={method.color}
                bgColor={method.bgColor}
                onClick={() => console.log(`${method.title} clicked`)}
              />
            ))}
          </div>
        </div>
      </section> */}

      {/* Contact Form and Info */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12">
            {/* Contact Form */}
            <ContactForm onSubmit={handleFormSubmit} />

            {/* Contact Information */}
            <div className="space-y-8">
              <div>
                <h3 className="text-3xl font-bold text-slate-900 mb-6">Contact Information</h3>
                <p className="text-lg text-slate-600 mb-8">
                  We're here to help! Reach out through any of these channels and we'll get back to you as soon as possible.
                </p>
              </div>
              
              <div className="grid gap-6">
                {contactInfo.map((info, index) => (
                  <ContactInfoCard
                    key={index}
                    icon={info.icon}
                    title={info.title}
                    content={info.content}
                    description={info.description}
                    color={info.color}
                  />
                ))}
              </div>

              {/* Social Links */}
              <SocialLinks links={socialLinks} />
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Quick Links */}
      <section className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-6">Looking for Quick Answers?</h2>
          <p className="text-xl text-slate-600 mb-8">
            Check out our FAQ section for instant answers to common questions
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/faq"
              className="px-8 py-4 bg-sky-600 text-white rounded-xl font-semibold hover:bg-sky-700 transition-colors"
            >
              Browse FAQ
            </Link>
            <Link 
              href="/about_us"
              className="px-8 py-4 border-2 border-sky-600 text-sky-600 rounded-xl font-semibold hover:bg-sky-600 hover:text-white transition-colors"
            >
              Learn About Us
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <CTASection
        title="Ready to Get Started?"
        description="Join thousands of educators and students who are already using Pan-Sea to enhance their learning experience."
        buttons={[
          { text: "Try Pan-Sea Free", variant: "primary" },
          { text: "Schedule a Demo", variant: "secondary" }
        ]}
      />
    </div>
  );
}
