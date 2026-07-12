"use client";

import React from 'react';
import { motion } from 'motion/react';
import { ArrowRight, Play, CheckCircle2 } from 'lucide-react';
import { PillButton } from './PillButton';
import { LivePipelineCard } from './LivePipelineCard';
import { useMotionTokens } from '@/lib/motion-tokens';

export function Hero() {
  const { tier2, shouldReduceMotion } = useMotionTokens();

  // Motion variants for stagger
  const containerVariants = {
    initial: {},
    animate: {
      transition: {
        staggerChildren: tier2.stagger,
        delayChildren: 0.6 // Wait for nav & mesh
      }
    }
  };

  const wordVariants = {
    initial: tier2.initial,
    animate: tier2.animate
  };
  
  const lines = [
    ["Predict", "Crime"],
    ["Deploy", "Smarter"]
  ];

  return (
    <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden flex flex-col items-center min-h-[90vh] justify-center">
      <motion.div 
        variants={containerVariants}
        initial="initial"
        animate="animate"
        className="container max-w-[1400px] mx-auto px-4 relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center"
      >
        
        {/* Left Column: Text & CTAs */}
        <div className="flex flex-col items-start text-left lg:col-span-5">
          {/* Badge - Breathing Halo */}
          <motion.div 
            variants={wordVariants}
            transition={tier2.transition}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface-glass border border-surface-border mb-8 shadow-sm backdrop-blur-md relative"
          >
          <div className="relative flex h-2 w-2 items-center justify-center">
            {/* Outer breathing circle */}
            {!shouldReduceMotion && (
              <motion.div 
                className="absolute inset-0 rounded-full bg-accent"
                animate={{ scale: [1, 1.8], opacity: [0.4, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              />
            )}
            {/* Inner solid circle */}
            <div className="relative h-1.5 w-1.5 rounded-full bg-accent" />
          </div>
          <span className="text-xs font-semibold text-accent tracking-wide uppercase">Next-Gen Predictive Policing</span>
        </motion.div>

          {/* Headline */}
          <h1 className="text-4xl md:text-5xl lg:text-[3.5rem] xl:text-[4rem] tracking-tight leading-none mb-6 flex flex-col items-start pb-2">
            {lines.map((line, lineIndex) => (
              <div key={lineIndex} className="flex flex-row items-baseline justify-start gap-x-3">
                {line.map((word, wordIndex) => (
                  <motion.span 
                    key={wordIndex}
                    variants={wordVariants}
                    transition={tier2.transition}
                    className={`hero-headline ${
                      word === 'Crime' ? 'text-[0.85em]' : 
                      lineIndex === 1 ? 'text-[1.1em]' : ''
                    }`}
                  >
                    {word}
                  </motion.span>
                ))}
              </div>
            ))}
          </h1>

          {/* Subhead */}
          <motion.p 
            variants={wordVariants}
            transition={tier2.transition}
            className="text-lg md:text-xl text-text-muted max-w-lg mb-10 leading-relaxed"
          >
            The AI-powered intelligence platform for law enforcement. Turn raw data into actionable deployment strategies in milliseconds.
          </motion.p>

          {/* CTAs */}
          <motion.div 
            variants={wordVariants}
            transition={tier2.transition}
            className="flex flex-col sm:flex-row items-center justify-start gap-4 w-full sm:w-auto mb-10"
          >
            <PillButton className="w-full sm:w-auto" icon={ArrowRight}>
              Start Free Trial
            </PillButton>
            <button className="group relative inline-flex items-center justify-center gap-3 rounded-full px-2 py-2 pr-6 text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-bg-base text-text-primary hover:text-white w-full sm:w-auto bg-white/40 border border-surface-border">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white border border-surface-border group-hover:bg-accent/10 transition-colors">
                <Play className="h-4 w-4 text-accent translate-x-[1px]" />
              </div>
              Watch Demo
            </button>
          </motion.div>

          {/* Trust Row */}
          <motion.div
            variants={wordVariants}
            transition={tier2.transition}
            className="flex flex-wrap items-center justify-start gap-x-8 gap-y-3"
          >
            {["Karnataka CCTNS Integrated", "112 Emergency Compatible", "Data Sovereign"].map((badge) => (
              <div key={badge} className="flex items-center gap-2 text-sm font-medium text-text-muted">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                {badge}
              </div>
            ))}
          </motion.div>
        </div>

        {/* Right Column: Live Pipeline Component */}
        <motion.div 
          variants={wordVariants}
          transition={tier2.transition}
          className="relative w-full max-w-[750px] mx-auto lg:col-span-7 lg:ml-6"
        >
          <LivePipelineCard />
          
          {/* Floor glow */}
          <div className="absolute -bottom-20 left-1/2 -translate-x-1/2 w-3/4 h-20 bg-accent/20 blur-[100px] rounded-full pointer-events-none" />
        </motion.div>

      </motion.div>
    </section>
  );
}
