'use client';

import Image from 'next/image';
import { motion } from 'framer-motion';
import { useState } from 'react';

export default function HeroImage() {
  const [src, setSrc] = useState(
    'https://www.unicef.org/cambodia/sites/unicef.org.cambodia/files/styles/hero_extended/public/IMG20200420141915.jpg.webp?itok=BVrQIGqz'
  );

  return (
    <motion.div 
      className="relative"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
    >
      <div className="relative w-full max-w-[520px] aspect-square mx-auto">
        {/* Outer ring */}
        <motion.div 
          className="absolute inset-0 rounded-full border-8 border-sky-100" 
          aria-hidden="true"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        />
        {/* Photo with fallback and no optimization to avoid upstream 403 */}
        <Image
          src={src}
          alt="Student studying at desk"
          fill
          sizes="(max-width: 768px) 80vw, 520px"
          className="object-cover rounded-full"
          priority
          unoptimized
          onError={() => setSrc('/logo.png')}
        />
        {/* Accent blocks */}
        <motion.div
          className="absolute -right-6 -bottom-6 h-24 w-24 rounded-2xl bg-sky-500/15 border-2 border-sky-300"
          aria-hidden="true"
          initial={{ scale: 0, rotate: -45 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.6, delay: 1.2, ease: "easeOut" }}
        />
        <motion.div
          className="absolute -left-6 top-8 h-14 w-14 rounded-xl bg-sky-400/20 border-2 border-sky-300"
          aria-hidden="true"
          initial={{ scale: 0, rotate: 45 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.6, delay: 1.4, ease: "easeOut" }}
        />
        {/* Small dotted ring */}
        <motion.div
          className="absolute -right-8 top-10 h-10 w-10 rounded-full border-2 border-dashed border-sky-400"
          aria-hidden="true"
          initial={{ scale: 0, rotate: 180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ duration: 0.6, delay: 1.6, ease: "easeOut" }}
        />
      </div>
    </motion.div>
  );
}
