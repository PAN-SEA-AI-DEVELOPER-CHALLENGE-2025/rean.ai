'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import NavBar from './nav';

export default function Header() {
  return (
    <motion.header 
      className="sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-slate-200"
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <NavBar />
    </motion.header>
  );
}
