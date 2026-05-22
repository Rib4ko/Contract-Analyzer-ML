import React, { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { FileDown, RefreshCw } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

// Sub-component: Playbook Shuffler
const PlaybookShuffler = () => {
  const [cards, setCards] = useState([
    { id: 1, title: 'Governing Law', status: 'Match', color: 'text-green-600' },
    { id: 2, title: 'Indemnification', status: 'Deviation', color: 'text-red-600' },
    { id: 3, title: 'Confidentiality', status: 'Review', color: 'text-accent' }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCards(prev => {
        const newArr = [...prev];
        const last = newArr.pop();
        newArr.unshift(last);
        return newArr;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative h-48 w-full flex items-center justify-center">
      {cards.map((c, i) => (
        <div 
          key={c.id} 
          className="absolute w-full max-w-[200px] bg-white border border-primary/10 rounded-2xl p-4 shadow-sm transition-all duration-700 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
          style={{
            transform: `translateY(${i * 12}px) scale(${1 - i * 0.05})`,
            zIndex: 10 - i,
            opacity: 1 - i * 0.2
          }}
        >
          <div className="font-mono text-xs text-primary/50 mb-2">Clause {c.id}</div>
          <div className="font-sans font-bold text-primary mb-1">{c.title}</div>
          <div className={`font-mono text-xs font-semibold ${c.color}`}>{c.status}</div>
        </div>
      ))}
    </div>
  );
};

// Sub-component: Telemetry Typewriter
const TelemetryTypewriter = () => {
  const textRef = useRef(null);
  
  useEffect(() => {
    const text = '"Proprietary Materials" found. Checking definitions... [WARN] Undefined term detected.';
    let i = 0;
    textRef.current.innerHTML = '';
    
    const interval = setInterval(() => {
      if (i < text.length) {
        textRef.current.innerHTML += text.charAt(i);
        i++;
      } else {
        setTimeout(() => {
          i = 0;
          textRef.current.innerHTML = '';
        }, 2000);
      }
    }, 50);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-48 w-full bg-dark rounded-2xl p-6 flex flex-col justify-between">
      <div className="flex items-center space-x-2">
        <div className="w-2 h-2 rounded-full bg-accent animate-pulse"></div>
        <div className="font-mono text-[10px] uppercase text-background/50 tracking-wider">Live Telemetry</div>
      </div>
      <div className="font-mono text-sm text-green-400 mt-4 h-full leading-relaxed">
        <span ref={textRef}></span>
        <span className="animate-pulse ml-1 inline-block w-2 h-4 bg-accent align-middle"></span>
      </div>
    </div>
  );
};

// Sub-component: Export Protocol
const ExportProtocol = () => {
  return (
    <div className="h-48 w-full flex items-center justify-center bg-primary/5 rounded-2xl border border-primary/10 group relative overflow-hidden">
      <div className="absolute inset-0 bg-accent/5 transform -translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
      <div className="flex flex-col items-center justify-center space-y-4 relative z-10">
        <div className="relative">
          <FileDown size={48} className="text-primary group-hover:scale-110 transition-transform duration-500" />
          <div className="absolute -bottom-2 -right-2 bg-accent text-primary text-[10px] font-bold px-1.5 py-0.5 rounded font-mono">DOCX</div>
        </div>
        <div className="flex items-center space-x-2 text-primary/70 font-mono text-xs">
          <RefreshCw size={12} className="animate-spin" />
          <span>Generating Report</span>
        </div>
      </div>
    </div>
  );
};

const Features = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    let ctx = gsap.context(() => {
      gsap.from('.feature-card', {
        scrollTrigger: {
          trigger: containerRef.current,
          start: 'top 75%',
        },
        y: 60,
        opacity: 0,
        duration: 1,
        stagger: 0.15,
        ease: 'power3.out'
      });
    }, containerRef);
    return () => ctx.revert();
  }, []);

  return (
    <section id="features" ref={containerRef} className="py-24 px-6 bg-background w-full">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16">
          <h2 className="font-drama italic text-5xl md:text-6xl text-primary mb-4">Functional Artifacts</h2>
          <p className="font-sans text-primary/70 max-w-lg text-lg">Precision algorithms packaged into beautiful, responsive interfaces.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Card 1 */}
          <div className="feature-card bg-white p-8 rounded-[2rem] border border-primary/10 shadow-xl shadow-primary/5 group hover:-translate-y-2 transition-transform duration-500">
            <PlaybookShuffler />
            <div className="mt-8">
              <h3 className="font-sans font-bold text-xl text-primary mb-2">Playbook Engine</h3>
              <p className="font-sans text-sm text-primary/70">TF-IDF similarity scoring compares extracted clauses against your standard playbook.</p>
            </div>
          </div>

          {/* Card 2 */}
          <div className="feature-card bg-white p-8 rounded-[2rem] border border-primary/10 shadow-xl shadow-primary/5 group hover:-translate-y-2 transition-transform duration-500">
            <TelemetryTypewriter />
            <div className="mt-8">
              <h3 className="font-sans font-bold text-xl text-primary mb-2">Definitions Validation</h3>
              <p className="font-sans text-sm text-primary/70">Two-pass regex extraction flags capitalized terms that are used but not defined.</p>
            </div>
          </div>

          {/* Card 3 */}
          <div className="feature-card bg-white p-8 rounded-[2rem] border border-primary/10 shadow-xl shadow-primary/5 group hover:-translate-y-2 transition-transform duration-500">
            <ExportProtocol />
            <div className="mt-8">
              <h3 className="font-sans font-bold text-xl text-primary mb-2">Word Report Export</h3>
              <p className="font-sans text-sm text-primary/70">One-click conversion of findings into a client-ready .docx deviation report.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;
