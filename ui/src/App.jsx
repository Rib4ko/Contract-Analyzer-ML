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

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <div className="min-h-screen bg-background w-full overflow-x-hidden flex flex-col font-sans">
      <Navbar />
      <main className="flex-grow flex flex-col w-full">
        <Hero />
        <Features />
        <Philosophy />
        {session ? <AppPlatform session={session} /> : <Auth onLogin={setSession} />}
      </main>
      <Footer />
    </div>
  );
}

export default App;
