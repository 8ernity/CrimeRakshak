"use client";

import React, { useEffect, useState } from 'react';
import { motion, useSpring, useTransform } from 'motion/react';
import { cn } from '@/lib/utils';

export function MeshGradientBackground({ children, className }: { children?: React.ReactNode, className?: string }) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsDesktop(window.innerWidth >= 1024);
    const handleResize = () => setIsDesktop(window.innerWidth >= 1024);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (!isDesktop) return;
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth - 0.5) * 2,
        y: (e.clientY / window.innerHeight - 0.5) * 2,
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [isDesktop]);

  const springConfig = { stiffness: 50, damping: 20 };
  const smoothX = useSpring(mousePosition.x, springConfig);
  const smoothY = useSpring(mousePosition.y, springConfig);

  const x1 = useTransform(smoothX, [-1, 1], [-20, 20]);
  const y1 = useTransform(smoothY, [-1, 1], [-20, 20]);
  
  const x2 = useTransform(smoothX, [-1, 1], [20, -20]);
  const y2 = useTransform(smoothY, [-1, 1], [20, -20]);
  
  const x3 = useTransform(smoothX, [-1, 1], [-10, 10]);
  const y3 = useTransform(smoothY, [-1, 1], [10, -10]);

  return (
    <div className={cn("relative min-h-screen bg-bg-base overflow-hidden selection:bg-accent/30 selection:text-white", className)}>
      <motion.div 
        className="fixed inset-0 z-0 pointer-events-none overflow-hidden"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
      >
        {/* Top Left Blob */}
        <motion.div 
          className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-blue-500/15 blur-[140px] mix-blend-multiply"
          style={isDesktop ? { x: x1, y: y1 } : undefined}
        />
        
        {/* Top Right Blob */}
        <motion.div 
          className="absolute top-[-5%] right-[-10%] w-[45vw] h-[45vw] rounded-full bg-lavender/15 blur-[160px] mix-blend-multiply"
          style={isDesktop ? { x: x2, y: y2 } : undefined}
        />
        
        {/* Center Right Champagne Whisper */}
        <motion.div 
          className="absolute top-[20%] right-[10%] w-[40vw] h-[40vw] rounded-full bg-[#FDF6E8]/10 blur-[120px] mix-blend-multiply"
          style={isDesktop ? { x: x3, y: y3 } : undefined}
        />

        {/* Bottom Left Blob */}
        <motion.div 
          className="absolute bottom-[-15%] left-[-5%] w-[55vw] h-[45vw] rounded-full bg-blue-400/12 blur-[160px] mix-blend-multiply"
          style={isDesktop ? { x: x3, y: y1 } : undefined}
        />
        
        {/* Bottom Right Blob */}
        <motion.div 
          className="absolute bottom-[-10%] right-[15%] w-[50vw] h-[40vw] rounded-full bg-indigo-300/8 blur-[160px] mix-blend-multiply"
          style={isDesktop ? { x: x1, y: y2 } : undefined}
        />
        
        {/* Noise overlay to prevent banding */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] mix-blend-overlay"></div>
      </motion.div>
      
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
