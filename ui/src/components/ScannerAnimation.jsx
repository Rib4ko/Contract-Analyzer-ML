import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ShieldCheck } from 'lucide-react';

const ScannerAnimation = () => {
  const containerRef = useRef(null);
  const cardRef = useRef(null);
  const scannerRef = useRef(null);
  const linesRef = useRef([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // 1. Float the whole card gently
      gsap.to(cardRef.current, {
        y: 15,
        rotationX: 2,
        rotationY: -2,
        duration: 4,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });

      // 2. Continuous Scanner Loop
      const scanDuration = 3.5;
      const t1 = gsap.timeline({ repeat: -1 });

      // Move scanner down
      t1.fromTo(scannerRef.current, 
        { top: '-20%', opacity: 0 },
        { top: '120%', opacity: 1, duration: scanDuration, ease: "linear" }
      );

      // Reveal text lines as scanner passes
      linesRef.current.forEach((line, index) => {
        // Calculate the time when scanner hits this line (approximate by index)
        const hitTime = (index / linesRef.current.length) * (scanDuration * 0.7) + 0.5;
        
        t1.to(line, {
          opacity: 1,
          width: '100%',
          backgroundColor: line.dataset.verified === 'true' ? '#10B981' : (line.dataset.flagged === 'true' ? '#EF4444' : '#FFFFFF'),
          duration: 0.3,
          ease: "power2.out"
        }, hitTime);
        
        // Reset lines before next scan loop starts
        t1.to(line, {
          opacity: 0.2,
          width: '70%',
          backgroundColor: '#FFFFFF',
          duration: 0.1
        }, scanDuration - 0.1);
      });

    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef} className="relative w-full h-[400px] flex items-center justify-center perspective-[1000px]">
      
      {/* Background glowing orb */}
      <div className="absolute w-64 h-64 bg-accent/20 rounded-full blur-3xl opacity-50 animate-pulse"></div>
      
      {/* Document Card */}
      <div 
        ref={cardRef} 
        className="relative w-80 h-96 bg-white/5 border border-white/10 rounded-[2rem] p-8 shadow-2xl backdrop-blur-md overflow-hidden flex flex-col"
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* Document Header */}
        <div className="w-1/3 h-4 bg-white/20 rounded-full mb-10"></div>
        
        {/* Document Lines */}
        <div className="space-y-6 flex-1">
          {[
            { id: 1, flag: false, verified: true },
            { id: 2, flag: false, verified: false },
            { id: 3, flag: true, verified: false }, // Deviation
            { id: 4, flag: false, verified: false },
            { id: 5, flag: false, verified: true },
            { id: 6, flag: false, verified: false },
          ].map((item, i) => (
            <div key={item.id} className="w-full h-3 bg-transparent rounded-full flex overflow-hidden">
              <div 
                ref={el => linesRef.current[i] = el}
                data-verified={item.verified}
                data-flagged={item.flag}
                className="h-full bg-white/20 w-[70%] opacity-20 rounded-full"
              ></div>
            </div>
          ))}
        </div>
        
        {/* The Laser Scanner */}
        <div 
          ref={scannerRef} 
          className="absolute left-0 w-full h-[2px] bg-accent shadow-[0_0_15px_rgba(123,97,255,1)] z-20"
        >
          {/* Scanner gradient fade */}
          <div className="absolute bottom-full left-0 w-full h-24 bg-gradient-to-t from-accent/20 to-transparent"></div>
        </div>

        {/* Security Shield Watermark */}
        <div className="absolute bottom-6 right-6 opacity-20 flex flex-col items-center">
          <ShieldCheck size={48} className="text-accent mb-1" />
          <span className="font-mono text-[8px] tracking-widest text-accent uppercase">Zero Trust</span>
        </div>
      </div>
    </div>
  );
};

export default ScannerAnimation;
