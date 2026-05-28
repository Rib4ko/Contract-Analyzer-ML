import React, { useState } from 'react';
import { supabase } from '../lib/supabase';
import { Lock, Mail, KeyRound } from 'lucide-react';

const Auth = ({ onLogin, onOfflineLogin }) => {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        setMessage('Check your email for the login link!');
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        if (data.session) onLogin(data.session);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="platform" className="py-24 px-6 bg-primary w-full text-background">
      <div className="max-w-md mx-auto flex flex-col items-center">
        <div className="text-center mb-12">
          <h2 className="font-drama italic text-5xl text-accent mb-4">Authenticate</h2>
          <p className="font-sans text-background/70">Secure access to the Lexa Audit pipeline.</p>
        </div>

        <div className="w-full bg-white/5 border border-white/10 rounded-[3rem] p-8 md:p-12 backdrop-blur-sm shadow-2xl">
          <form onSubmit={handleAuth} className="flex flex-col space-y-6">
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 h-5 w-5" />
              <input
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-full py-3 pl-12 pr-4 text-background placeholder-white/40 focus:outline-none focus:border-accent transition-colors"
                required
              />
            </div>
            
            <div className="relative">
              <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 h-5 w-5" />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-full py-3 pl-12 pr-4 text-background placeholder-white/40 focus:outline-none focus:border-accent transition-colors"
                required
              />
            </div>

            {error && <p className="text-red-400 text-sm text-center font-mono">{error}</p>}
            {message && <p className="text-accent text-sm text-center font-mono">{message}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full relative overflow-hidden px-8 py-3 bg-accent text-primary rounded-full font-sans font-bold transition-transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center space-x-2"
            >
              <Lock size={18} />
              <span>{loading ? 'Authenticating...' : isSignUp ? 'Create Account' : 'Sign In'}</span>
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <button 
              onClick={() => setIsSignUp(!isSignUp)}
              className="text-white/60 hover:text-accent font-sans text-sm transition-colors"
            >
              {isSignUp ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
            </button>
          </div>
          
          <div className="mt-8 pt-6 border-t border-white/10 text-center">
            <button 
              type="button"
              onClick={onOfflineLogin}
              className="w-full relative overflow-hidden px-8 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-background rounded-full font-sans font-bold transition-all hover:border-accent/50 flex items-center justify-center space-x-2"
            >
              <span>Work Offline (Air-Gapped Mode)</span>
            </button>
            <p className="mt-3 font-mono text-[10px] text-background/40">
              Bypass cloud authentication and run entirely on your local machine.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Auth;
