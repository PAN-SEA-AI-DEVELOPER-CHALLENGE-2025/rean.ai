import React from 'react';
import { IconType } from 'react-icons';

interface ContactInfoCardProps {
  icon: IconType;
  title: string;
  content: string;
  description: string;
  color: string;
  className?: string;
}

export default function ContactInfoCard({ 
  icon: Icon, 
  title, 
  content, 
  description, 
  color,
  className = ""
}: ContactInfoCardProps) {
  return (
    <div className={`bg-white p-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 ${className}`}>
      <div className="flex items-start space-x-4">
        <div className={`w-12 h-12 bg-${color}-100 rounded-full flex items-center justify-center flex-shrink-0`}>
          <Icon className={`text-xl text-${color}-600`} />
        </div>
        <div>
          <h4 className="font-semibold text-slate-900 mb-1">{title}</h4>
          <p className="text-lg font-medium text-slate-800 mb-1">{content}</p>
          <p className="text-sm text-slate-600">{description}</p>
        </div>
      </div>
    </div>
  );
}
