import React, { useEffect, useState } from 'react';

const Footer = () => {
  const [status, setStatus] = useState('Checking...');
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        // Ping the local FastAPI backend
        const res = await fetch('http://127.0.0.1:8001/health');
        if (res.ok) {
          setStatus('System Operational');
          setIsOnline(true);
        } else {
          setStatus('System Offline');
          setIsOnline(false);
        }
      } catch (err) {
        setStatus('System Offline (Backend Not Running)');
        setIsOnline(false);
      }
    };
    
    checkHealth();
  }, []);

  return (
    <footer className="bg-dark text-background pt-20 pb-10 px-6 rounded-t-[4rem] -mt-10 relative z-20 w-full">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center">
        
        <div className="mb-10 md:mb-0">
          <h4 className="font-sans font-bold text-2xl tracking-tight text-accent mb-2">Lexa Audit</h4>
          <p className="font-mono text-sm text-background/50">Precision Contract Audit</p>
        </div>

        <div className="flex items-center space-x-3 bg-white/5 border border-white/10 rounded-full px-4 py-2">
          <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
          <span className="font-mono text-xs uppercase tracking-widest text-background/70">{status}</span>
        </div>

      </div>
      
      <div className="max-w-6xl mx-auto mt-16 pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center text-xs font-mono text-background/40">
        <p>&copy; {new Date().getFullYear()} Lexa Audit Pipeline. All rights reserved.</p>
        <div className="flex space-x-6 mt-4 md:mt-0 font-sans">
          <a href="#" className="hover:text-accent transition-colors">Privacy</a>
          <a href="#" className="hover:text-accent transition-colors">Terms</a>
          <a href="#" className="hover:text-accent transition-colors">Security</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
