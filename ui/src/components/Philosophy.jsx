import React, { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const Philosophy = () => {
  const containerRef = useRef(null);
  
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.manifesto-line', {
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 70%',
        },
        y: 40,
        opacity: 0,
        duration: 1.2,
        stagger: 0.2,
        ease: 'power3.out'
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  return (
    <section id="philosophy" ref={containerRef} className="relative py-32 px-6 bg-dark text-background overflow-hidden w-full">
      
      {/* Background Texture Overlay */}
      <div 
        className="absolute inset-0 w-full h-full bg-cover bg-center opacity-10 mix-blend-overlay"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1541888086425-d81bb19240f5?q=80&w=2070&auto=format&fit=crop')" }}
      ></div>

      <div className="relative z-10 max-w-5xl mx-auto flex flex-col justify-center items-center text-center space-y-12">
        
        <div className="manifesto-line">
          <p className="font-sans text-xl md:text-2xl text-background/60 tracking-tight font-light">
            Most contract review focuses on: <span className="font-medium text-background/80">manual checklist verification.</span>
          </p>
        </div>

        <div className="manifesto-line w-full h-px bg-background/10"></div>

        <div className="manifesto-line">
          <p className="font-drama italic font-semibold text-5xl md:text-7xl lg:text-8xl leading-tight text-background">
            We focus on: <br/>
            <span className="text-accent">automated precision audit.</span>
          </p>
        </div>

      </div>
    </section>
  );
};

export default Philosophy;
