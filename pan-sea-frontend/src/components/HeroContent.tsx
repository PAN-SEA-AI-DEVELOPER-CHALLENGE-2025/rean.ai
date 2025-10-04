'use client';

import Link from 'next/link';
import { motion, easeOut } from 'framer-motion';

export default function HeroContent() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.3
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.8, ease: easeOut }
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.h1 
        className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight"
        variants={itemVariants}
      >
        REAN
        <span className="block text-sky-700">.AI</span>
      </motion.h1>
      <motion.p 
        className="mt-5 max-w-xl text-slate-600"
        variants={itemVariants}
      >
        Learning shouldn&apos;t be a race to write notes before the moment is gone.
        Our AI-powered Class Memory & Tutor captures everything your teacher says, turns it into clear summaries, 
        and lets you ask questions anytime, answered in the teacher&apos;s own words.
      </motion.p>

      <motion.div 
        className="mt-8"
        variants={itemVariants}
      >
        <Link
          href="/auth/login"
          className="inline-flex items-center rounded-full bg-sky-600 hover:bg-sky-700 text-white px-7 py-3 font-semibold shadow-md transition-all duration-300 hover:scale-105"
        >
          GET REAN AI
        </Link>
      </motion.div>
    </motion.div>
  );
}
