import React, { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

const Navbar = () => {
  const navRef = useRef(null);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="fixed top-6 left-0 right-0 z-50 flex justify-center px-4 w-full">
      <nav
        ref={navRef}
        className={`transition-all duration-500 ease-in-out flex items-center justify-between px-6 py-3 rounded-full w-full max-w-5xl ${
          isScrolled 
            ? 'bg-background/80 backdrop-blur-xl border border-primary/10 shadow-lg text-primary' 
            : 'bg-transparent text-background'
        }`}
      >
        <div className="font-sans font-bold text-xl tracking-tight">
          Lexa Audit
        </div>
        
        <div className="hidden md:flex items-center space-x-8 font-sans text-sm font-medium">
          <a href="#features" className="hover:-translate-y-[1px] transition-transform">Features</a>
          <a href="#philosophy" className="hover:-translate-y-[1px] transition-transform">Philosophy</a>
          <a href="#platform" className="hover:-translate-y-[1px] transition-transform">App Platform</a>
        </div>

        <button 
          onClick={() => document.getElementById('platform')?.scrollIntoView({ behavior: 'smooth' })}
          className={`relative overflow-hidden px-6 py-2 rounded-full font-sans text-sm font-semibold transition-transform hover:scale-105 active:scale-95 ${
            isScrolled ? 'bg-primary text-background' : 'bg-background text-primary'
          }`}
        >
          <span className="relative z-10">Upload Contract</span>
        </button>
      </nav>
    </div>
  );
};

export default Navbar;
