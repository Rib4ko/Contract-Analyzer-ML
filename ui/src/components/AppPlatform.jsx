import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, FileText, ChevronRight, CheckCircle2, AlertCircle } from 'lucide-react';
import gsap from 'gsap';

import { supabase } from '../lib/supabase';

const AppPlatform = ({ session }) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [savedPlaybook, setSavedPlaybook] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, loading, complete, error
  const [results, setResults] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [airGappedMode, setAirGappedMode] = useState(false);
  const loadingTextRef = useRef(null);

  const loadingSteps = [
    "Ingesting Document...",
    "Running SVM Router...",
    "Checking Definitions...",
    "Comparing Playbook Deviations...",
    "Extracting Facts via Groq...",
    "Compiling Audit Report..."
  ];

  useEffect(() => {
    if (session?.user?.id) {
      supabase
        .from('playbooks')
        .select('mapping')
        .eq('user_id', session.user.id)
        .order('created_at', { ascending: false })
        .limit(1)
        .single()
        .then(({ data, error }) => {
          if (data && !error) setSavedPlaybook(data.mapping);
        });
    }
  }, [session]);

  useEffect(() => {
    let interval;
    if (status === 'loading') {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => {
          const next = prev + 1;
          return next < loadingSteps.length ? next : prev;
        });
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [status]);

  useEffect(() => {
    if (status === 'loading' && loadingTextRef.current) {
      gsap.fromTo(
        loadingTextRef.current,
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }
      );
    }
  }, [loadingStep, status]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handlePlaybookUpload = async (e) => {
    const pFile = e.target.files[0];
    if (!pFile) return;
    
    setStatus('loading');
    const formData = new FormData();
    formData.append('playbook_file', pFile);
    
    try {
      const res = await fetch('http://127.0.0.1:8001/api/parse_playbook', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: formData
      });
      if (!res.ok) throw new Error("Failed to parse playbook");
      const mapping = await res.json();
      
      if (session?.user?.id) {
        await supabase.from('playbooks').delete().eq('user_id', session.user.id);
        await supabase.from('playbooks').insert({ user_id: session.user.id, mapping });
      }
      
      setSavedPlaybook(mapping);
      setStatus('idle');
    } catch (err) {
      console.error(err);
      setStatus('idle');
    }
  };

  const runAnalysis = async () => {
    if (!file) return;
    setStatus('loading');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('air_gapped_mode', airGappedMode);
    if (savedPlaybook) {
      formData.append('playbook_mapping', JSON.stringify(savedPlaybook));
    }

    try {
      const response = await fetch('http://127.0.0.1:8001/api/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      
      setStatus('complete');
      setResults({
        file_name: file.name,
        deviations: data.summary?.playbook_deviations || 0,
        undefined_terms: data.summary?.undefined_terms || 0,
        raw_data: data,
      });
    } catch (error) {
      console.error(error);
      setStatus('idle'); // or error state
    }
  };

  return (
    <section id="platform" className="py-24 px-6 bg-primary w-full text-background">
      <div className="max-w-4xl mx-auto flex flex-col items-center">
        
        <div className="text-center mb-12">
          <h2 className="font-drama italic text-5xl text-accent mb-4">The Platform</h2>
          <p className="font-sans text-background/70 max-w-lg mx-auto">Upload a contract to run it through the local SVM pipeline. Secure, private, and precise.</p>
        </div>

        <div className="w-full bg-white/5 border border-white/10 rounded-[3rem] p-8 md:p-12 backdrop-blur-sm shadow-2xl">
          
          {status === 'idle' && (
            <div className="flex flex-col space-y-4">
              <div 
                className={`relative border-2 border-dashed rounded-[2rem] p-12 text-center transition-colors duration-300 ${dragActive ? 'border-accent bg-accent/5' : 'border-white/20 hover:border-accent/50'}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input 
                  type="file" 
                  accept=".pdf,image/*" 
                  onChange={handleChange} 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <UploadCloud className="mx-auto h-16 w-16 text-accent mb-4" />
                <p className="font-sans font-semibold text-xl mb-2">
                  {file ? file.name : "Drag & Drop PDF or Image"}
                </p>
                <p className="font-mono text-xs text-background/50">
                  {file ? "Ready for analysis" : "Supports .pdf, .png, .jpg"}
                </p>
              </div>

              <div className="relative border border-white/10 rounded-[1.5rem] p-6 text-center hover:border-accent/30 transition-colors bg-white/5">
                <input 
                  type="file" 
                  accept=".json,.txt,.pdf" 
                  onChange={handlePlaybookUpload} 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <p className="font-sans font-semibold text-sm mb-1">
                  {savedPlaybook ? "Custom Playbook Loaded! Click to replace." : "Optional: Upload Playbook (.json, .txt, .pdf)"}
                </p>
                <p className="font-mono text-[10px] text-background/50">
                  Maps categories to standard clause language securely to your account
                </p>
              </div>

              <div className="flex items-center justify-between bg-white/5 border border-white/10 p-4 rounded-[1.5rem]">
                <div>
                  <h4 className="font-sans font-bold text-sm">Air-Gapped / Strict Local Mode</h4>
                  <p className="font-mono text-[10px] text-background/50">Disables 3rd-party Cloud LLMs. 100% data privacy.</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" checked={airGappedMode} onChange={(e) => setAirGappedMode(e.target.checked)} />
                  <div className="w-11 h-6 bg-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                </label>
              </div>

              {file && (
                <button 
                  onClick={runAnalysis}
                  className="mt-4 relative z-20 overflow-hidden px-8 py-3 bg-accent text-primary rounded-full font-sans font-bold transition-transform hover:scale-105 active:scale-95 mx-auto block"
                >
                  Analyze Document
                </button>
              )}
            </div>
          )}

          {status === 'loading' && (
            <div className="flex flex-col items-center justify-center py-12 space-y-8 min-h-[300px]">
              <div className="relative w-24 h-24">
                <div className="absolute inset-0 border-4 border-white/10 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-accent rounded-full border-t-transparent animate-spin"></div>
              </div>
              <div className="h-8 overflow-hidden flex items-center justify-center">
                <div 
                  ref={loadingTextRef} 
                  className="font-mono text-lg text-accent font-semibold tracking-wide"
                >
                  {loadingSteps[loadingStep]}
                </div>
              </div>
            </div>
          )}

          {status === 'complete' && results && (
            <div className="flex flex-col w-full animate-[fadeIn_0.5s_ease-out]">
              <div className="flex items-center space-x-4 mb-8 pb-8 border-b border-white/10">
                <FileText className="h-12 w-12 text-accent" />
                <div>
                  <h3 className="font-sans font-bold text-2xl">{results.file_name}</h3>
                  <p className="font-mono text-xs text-background/50">Analysis Complete</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <div className="bg-white/5 p-6 rounded-[2rem] border border-white/10">
                  <div className="flex justify-between items-center mb-4">
                    <span className="font-sans font-bold">Playbook Deviations</span>
                    <AlertCircle className="text-red-400 h-5 w-5" />
                  </div>
                  <div className="font-mono text-3xl text-red-400">{results.deviations} <span className="text-sm text-background/50">Flags</span></div>
                </div>

                <div className="bg-white/5 p-6 rounded-[2rem] border border-white/10">
                  <div className="flex justify-between items-center mb-4">
                    <span className="font-sans font-bold">Undefined Terms</span>
                    <CheckCircle2 className="text-accent h-5 w-5" />
                  </div>
                  <div className="font-mono text-3xl text-accent">{results.undefined_terms} <span className="text-sm text-background/50">Found</span></div>
                </div>
              </div>

              <div className="flex justify-center">
                <button 
                  onClick={() => { setStatus('idle'); setFile(null); }}
                  className="px-8 py-3 bg-white/10 hover:bg-white/20 text-background rounded-full font-sans font-semibold transition-colors mr-4"
                >
                  New Scan
                </button>
                <button 
                  onClick={async () => {
                    try {
                      const res = await fetch('http://127.0.0.1:8001/api/export', {
                        method: 'POST',
                        headers: { 
                          'Content-Type': 'application/json',
                          'Authorization': `Bearer ${session?.access_token}`
                        },
                        body: JSON.stringify({ analysis: results.raw_data, title: results.file_name })
                      });
                      if (!res.ok) throw new Error('Export failed');
                      const blob = await res.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = results.file_name.replace('.pdf', '-report.docx');
                      a.click();
                      window.URL.revokeObjectURL(url);
                    } catch (e) {
                      console.error(e);
                    }
                  }}
                  className="px-8 py-3 bg-accent text-primary rounded-full font-sans font-bold transition-transform hover:scale-105 shadow-xl flex items-center space-x-2"
                >
                  <span>Export DOCX</span>
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </section>
  );
};

export default AppPlatform;
