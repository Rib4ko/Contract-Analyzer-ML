import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Features from './components/Features';
import AppPlatform from './components/AppPlatform';
import Philosophy from './components/Philosophy';
import Footer from './components/Footer';
import Auth from './components/Auth';
import { supabase } from './lib/supabase';

function App() {
  const [session, setSession] = useState(null);
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session: supabaseSession } }) => {
      if (!isOfflineMode) setSession(supabaseSession);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, supabaseSession) => {
      if (!isOfflineMode) setSession(supabaseSession);
    });

    return () => subscription.unsubscribe();
  }, [isOfflineMode]);

  const handleOfflineLogin = () => {
    setIsOfflineMode(true);
    setSession({ access_token: 'OFFLINE_MODE', user: { id: 'offline-user' } });
  };

  return (
    <div className="min-h-screen bg-background w-full overflow-x-hidden flex flex-col font-sans">
      <Navbar />
      <main className="flex-grow flex flex-col w-full">
        <Hero />
        <Features />
        <Philosophy />
        {session ? <AppPlatform session={session} isOfflineMode={isOfflineMode} /> : <Auth onLogin={setSession} onOfflineLogin={handleOfflineLogin} />}
      </main>
      <Footer />
    </div>
  );
}

export default App;
