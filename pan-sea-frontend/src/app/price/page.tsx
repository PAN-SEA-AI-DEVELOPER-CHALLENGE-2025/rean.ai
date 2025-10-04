'use client';

import React, { useState } from 'react';
import { Check, Star, Zap, Users, BookOpen, Shield, Clock, ArrowRight, Sparkles, Award, Headphones } from 'lucide-react';
import NavBar from '@/components/nav';
import Footer from '@/components/Footer';

export default function PricingPage() {
  const [isYearly, setIsYearly] = useState(false);

  const pricingPlans = [
    {
      name: 'Starter',
      description: 'Perfect for individual learners',
      price: { monthly: 0, yearly: 0 },
      period: { monthly: 'forever', yearly: 'forever' },
      icon: BookOpen,
      color: 'from-blue-500 to-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-700',
      features: [
        'Up to 3 classes per month',
        'Basic AI summaries',
        'Standard audio quality',
        'Community support',
        'Mobile app access',
        'Basic analytics'
      ],
      limitations: [
        'Limited to 1 hour per class',
        'No priority support'
      ],
      cta: 'Get Started Free',
      ctaStyle: 'bg-blue-600 hover:bg-blue-700 text-white',
      popular: false
    },
    {
      name: 'Professional',
      description: 'For educators and small teams',
      price: { monthly: 29, yearly: 290 },
      period: { monthly: 'per month', yearly: 'per year' },
      icon: Zap,
      color: 'from-blue-600 to-blue-700',
      bgColor: 'bg-blue-100',
      borderColor: 'border-blue-300',
      textColor: 'text-blue-800',
      features: [
        'Unlimited classes',
        'Advanced AI summaries',
        'High-quality audio recording',
        'Priority support',
        'Advanced analytics & insights',
        'Custom branding',
        'Team collaboration (up to 5 users)',
        'Export to multiple formats',
        'API access'
      ],
      limitations: [],
      cta: 'Start Pro Trial',
      ctaStyle: 'bg-blue-600 hover:bg-blue-700 text-white',
      popular: true
    },
    {
      name: 'Enterprise',
      description: 'For large organizations',
      price: { monthly: 99, yearly: 990 },
      period: { monthly: 'per month', yearly: 'per year' },
      icon: Shield,
      color: 'from-blue-700 to-blue-800',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-700',
      features: [
        'Everything in Professional',
        'Unlimited team members',
        'Advanced security & compliance',
        'Custom integrations',
        'Dedicated account manager',
        'White-label solution',
        'Advanced reporting & analytics',
        'SSO integration',
        'Custom training & onboarding',
        '99.9% uptime SLA'
      ],
      limitations: [],
      cta: 'Contact Sales',
      ctaStyle: 'bg-blue-700 hover:bg-blue-800 text-white',
      popular: false
    }
  ];

  const savings = (monthly: number, yearly: number) => {
    const monthlyTotal = monthly * 12;
    const savings = monthlyTotal - yearly;
    const percentage = Math.round((savings / monthlyTotal) * 100);
    return { amount: savings, percentage };
  };

  return (
    <div className="min-h-screen bg-white">
      <NavBar />
      
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-50">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-blue-800/5"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            {/* Main Heading */}
            <div className="mb-8">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 mb-4">
                Simple, Transparent
                <span className="block text-blue-600">Pricing</span>
              </h1>
              <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
                Choose the perfect plan for your learning journey. Start free and upgrade as you grow.
              </p>
            </div>

            {/* Billing Toggle */}
            <div className="flex items-center justify-center gap-4 mb-12">
              <span className={`text-lg font-medium transition-colors ${!isYearly ? 'text-slate-900' : 'text-slate-500'}`}>
                Monthly
              </span>
              <button
                onClick={() => setIsYearly(!isYearly)}
                className={`relative inline-flex h-10 w-18 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  isYearly ? 'bg-blue-600' : 'bg-slate-300'
                }`}
              >
                <span
                  className={`inline-block h-8 w-8 transform rounded-full bg-white shadow-lg transition-transform duration-300 ${
                    isYearly ? 'translate-x-9' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className={`text-lg font-medium transition-colors ${isYearly ? 'text-slate-900' : 'text-slate-500'}`}>
                Yearly
              </span>
              {isYearly && (
                <span className="bg-blue-100 text-blue-800 text-sm font-semibold px-4 py-2 rounded-full flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Save up to 17%
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pricingPlans.map((plan, index) => {
            const Icon = plan.icon;
            const currentPrice = isYearly ? plan.price.yearly : plan.price.monthly;
            const currentPeriod = isYearly ? plan.period.yearly : plan.period.monthly;
            const monthlyEquivalent = isYearly ? Math.round(plan.price.yearly / 12) : plan.price.monthly;
            const savingsInfo = savings(plan.price.monthly, plan.price.yearly);

            return (
              <div
                key={plan.name}
                className={`relative bg-white rounded-3xl shadow-lg border transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 group ${
                  plan.popular 
                    ? 'border-blue-300 ring-2 ring-blue-100 scale-105' 
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-2 rounded-full text-sm font-semibold flex items-center gap-2 shadow-lg">
                      <Star className="w-4 h-4 fill-current" />
                      Most Popular
                    </div>
                  </div>
                )}

                <div className="p-8">
                  {/* Plan Header */}
                  <div className="text-center mb-8">
                    <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl ${plan.bgColor} mb-6 group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className={`w-8 h-8 ${plan.textColor}`} />
                    </div>
                    <h3 className="text-2xl font-bold text-slate-900 mb-3">{plan.name}</h3>
                    <p className="text-slate-600 leading-relaxed">{plan.description}</p>
                  </div>

                  {/* Pricing */}
                  <div className="text-center mb-8">
                    <div className="flex items-baseline justify-center">
                      <span className="text-5xl font-bold text-slate-900">${currentPrice}</span>
                      {currentPrice > 0 && (
                        <span className="text-xl text-slate-500 ml-1">/{currentPeriod}</span>
                      )}
                    </div>
                    {isYearly && currentPrice > 0 && (
                      <div className="mt-3">
                        <p className="text-sm text-slate-500">
                          ${monthlyEquivalent}/month billed annually
                        </p>
                        <p className="text-sm text-blue-600 font-semibold">
                          Save ${savingsInfo.amount} ({savingsInfo.percentage}% off)
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Features */}
                  <div className="space-y-4 mb-8">
                    {plan.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-start gap-3">
                        <Check className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                        <span className="text-slate-700 leading-relaxed">{feature}</span>
                      </div>
                    ))}
                    {plan.limitations.map((limitation, limitIndex) => (
                      <div key={limitIndex} className="flex items-start gap-3">
                        <div className="w-5 h-5 rounded-full border-2 border-slate-300 mt-0.5 flex-shrink-0"></div>
                        <span className="text-slate-500 leading-relaxed">{limitation}</span>
                      </div>
                    ))}
                  </div>

                  {/* CTA Button */}
                  <button
                    className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 group-hover:scale-105 ${
                      plan.popular
                        ? 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white focus:ring-blue-500 shadow-lg'
                        : plan.ctaStyle + ' shadow-md hover:shadow-lg'
                    }`}
                  >
                    <span className="flex items-center justify-center gap-2">
                      {plan.cta}
                      <ArrowRight className="w-4 h-4" />
                    </span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Trust Indicators */}
        <div className="mt-20 text-center">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-3xl shadow-lg p-8 max-w-5xl mx-auto border border-slate-100">
            <h3 className="text-3xl font-bold text-slate-900 mb-6">
              Trusted by educators worldwide
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center">
                  <Shield className="w-8 h-8 text-blue-600" />
                </div>
                <div className="text-center">
                  <h4 className="font-bold text-slate-900 text-lg">Enterprise Security</h4>
                  <p className="text-slate-600 mt-2">Bank-level encryption and privacy protection</p>
                </div>
              </div>
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center">
                  <Clock className="w-8 h-8 text-blue-600" />
                </div>
                <div className="text-center">
                  <h4 className="font-bold text-slate-900 text-lg">24/7 Support</h4>
                  <p className="text-slate-600 mt-2">Always here to help you succeed</p>
                </div>
              </div>
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center">
                  <Users className="w-8 h-8 text-blue-600" />
                </div>
                <div className="text-center">
                  <h4 className="font-bold text-slate-900 text-lg">Team Collaboration</h4>
                  <p className="text-slate-600 mt-2">Seamless teamwork and sharing</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-20">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-slate-900 mb-4">
              Frequently Asked Questions
            </h3>
            <p className="text-xl text-slate-600">
              Everything you need to know about our pricing
            </p>
          </div>
          
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-100">
                <h4 className="font-bold text-slate-900 mb-3">Can I change plans anytime?</h4>
                <p className="text-slate-600">Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.</p>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-100">
                <h4 className="font-bold text-slate-900 mb-3">Is there a free trial?</h4>
                <p className="text-slate-600">All paid plans come with a 14-day free trial. No credit card required to start.</p>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-100">
                <h4 className="font-bold text-slate-900 mb-3">What payment methods do you accept?</h4>
                <p className="text-slate-600">We accept all major credit cards, PayPal, and bank transfers for Enterprise plans.</p>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-100">
                <h4 className="font-bold text-slate-900 mb-3">Do you offer educational discounts?</h4>
                <p className="text-slate-600">Yes! We offer special pricing for schools and educational institutions. Contact us for details.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
