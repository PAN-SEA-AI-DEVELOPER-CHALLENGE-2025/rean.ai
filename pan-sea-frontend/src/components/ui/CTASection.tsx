import React from 'react';

interface CTAButton {
  text: string;
  href?: string;
  onClick?: () => void;
  variant: 'primary' | 'secondary';
}

interface CTASectionProps {
  title: string;
  description: string;
  buttons: CTAButton[];
  className?: string;
  backgroundVariant?: 'gradient' | 'solid';
}

export default function CTASection({ 
  title, 
  description, 
  buttons, 
  className = "",
  backgroundVariant = 'gradient'
}: CTASectionProps) {
  const backgroundClass = backgroundVariant === 'gradient' 
    ? 'bg-gradient-to-r from-sky-600 to-blue-700' 
    : 'bg-sky-600';

  return (
    <section className={`py-20 ${backgroundClass} ${className}`}>
      <div className="max-w-4xl mx-auto text-center px-6">
        <h2 className="text-4xl font-bold text-white mb-6">{title}</h2>
        <p className="text-xl text-sky-100 mb-8">
          {description}
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          {buttons.map((button, index) => (
            <CTAButton key={index} {...button} />
          ))}
        </div>
      </div>
    </section>
  );
}

function CTAButton({ text, href, onClick, variant }: CTAButton) {
  const baseClasses = "px-8 py-4 rounded-xl font-semibold transition-colors";
  const variantClasses = variant === 'primary'
    ? "bg-white text-sky-600 hover:bg-slate-100"
    : "border-2 border-white text-white hover:bg-white hover:text-sky-600";

  const className = `${baseClasses} ${variantClasses}`;

  if (href) {
    return (
      <a href={href} className={className}>
        {text}
      </a>
    );
  }

  return (
    <button onClick={onClick} className={className}>
      {text}
    </button>
  );
}

export type { CTAButton, CTASectionProps };