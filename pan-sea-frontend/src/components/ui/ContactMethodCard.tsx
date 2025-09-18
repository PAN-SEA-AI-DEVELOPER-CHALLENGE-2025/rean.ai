import React from 'react';
import { IconType } from 'react-icons';

interface ContactMethodCardProps {
  icon: IconType;
  title: string;
  description: string;
  action: string;
  color: string;
  bgColor: string;
  onClick?: () => void;
}

export default function ContactMethodCard({ 
  icon: Icon, 
  title, 
  description, 
  action, 
  color, 
  bgColor, 
  onClick 
}: ContactMethodCardProps) {
  return (
    <div 
      className={`p-8 rounded-2xl bg-gradient-to-br ${bgColor} border border-slate-100 hover:shadow-xl transition-all duration-300 hover:-translate-y-2`}
    >
      <div className={`w-16 h-16 bg-gradient-to-r ${color} rounded-full flex items-center justify-center mx-auto mb-6`}>
        <Icon className="text-2xl text-white" />
      </div>
      <h3 className="text-xl font-semibold text-slate-900 mb-3 text-center">{title}</h3>
      <p className="text-slate-600 text-center mb-6">{description}</p>
      <button 
        onClick={onClick}
        className={`w-full py-3 bg-gradient-to-r ${color} text-white rounded-xl font-semibold hover:shadow-lg transition-all duration-300`}
      >
        {action}
      </button>
    </div>
  );
}
