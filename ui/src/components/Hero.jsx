import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import ScannerAnimation from './ScannerAnimation';

const Hero = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    let ctx = gsap.context(() => {
      gsap.from('.hero-elem', {
        y: 40,
        opacity: 0,
        duration: 1.2,
        stagger: 0.15,
        ease: 'power3.out',
        delay: 0.2
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  return (
    <section 
      ref={containerRef}
      className="relative w-full min-h-[100dvh] flex items-center justify-center bg-dark overflow-hidden pt-20 pb-16"
    >
      {/* Background Image */}
      <div 
        className="absolute inset-0 w-full h-full bg-cover bg-center opacity-40"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=2069&auto=format&fit=crop')" }}
      ></div>
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 w-full h-full bg-gradient-to-t from-primary via-primary/60 to-transparent"></div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 flex flex-col lg:flex-row items-center justify-between gap-12">
        {/* Left Column: Text */}
        <div className="w-full lg:w-1/2 flex flex-col items-start text-left">
          <h1 className="flex flex-col text-background">
            <span className="hero-elem font-sans font-bold text-xl md:text-3xl tracking-wide uppercase text-accent mb-2">
              Lexa Audit is the
            </span>
            <span className="hero-elem font-drama italic font-semibold text-6xl md:text-8xl lg:text-[8rem] leading-[0.9] tracking-tighter">
              Precision Audit.
            </span>
          </h1>
          
          <p className="hero-elem mt-8 max-w-xl font-mono text-sm md:text-base text-background/80 leading-relaxed">
            A local-first contract pipeline tailored for top-tier transactional lawyers. Playbook deviation, definitions validation, and DOCX generation—running entirely on your infrastructure.
          </p>

          <button 
            onClick={() => document.getElementById('platform')?.scrollIntoView({ behavior: 'smooth' })}
            className="hero-elem mt-10 relative overflow-hidden px-8 py-4 bg-accent text-primary rounded-full font-sans text-base md:text-lg font-bold transition-transform hover:scale-[1.03] active:scale-95 shadow-xl hover:shadow-accent/20"
          >
            <span className="relative z-10">Start Local Scan</span>
          </button>
        </div>

        {/* Right Column: Animation */}
        <div className="hero-elem w-full lg:w-1/2 hidden md:flex items-center justify-center">
          <ScannerAnimation />
        </div>
      </div>
    </section>
  );
};

export default Hero;
