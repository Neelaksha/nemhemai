import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChatInterface } from '@/components/ChatInterface';
import { Sidebar } from '@/components/Sidebar';
import { SidebarProvider } from '@/components/ui/sidebar';
import { isAuthenticated, logoutAPI, fetchUserInfo } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { v4 as uuidv4 } from 'uuid';

const Index = () => {
  const [currentChatId, setCurrentChatId] = useState<string>(() => uuidv4());
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }
    // Fetch user info from /me endpoint
    fetchUserInfo()
      .then(data => {
        if (data) {
          setUser(data);
        } else {
          // Not authenticated, redirect to login
          navigate('/login');
        }
      })
      .catch(() => {
        navigate('/login');
      });
  }, [navigate]);
  // On every mount (reload), always start with a new chat session
  useEffect(() => {
    setCurrentChatId(uuidv4());
  }, []);

  const handleLogout = async () => {
    try {
      await logoutAPI();
    } catch (e) {
      // Continue with logout even if API call fails
    }
    navigate('/login');
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-white">
        {/* Sidebar and ChatInterface side by side */}
        <Sidebar currentChatId={currentChatId} onChatSelect={setCurrentChatId} />
        <main className="flex-1 flex flex-col" style={{background: '#fff', minHeight: '100vh', boxShadow: '0 0 0 1px #e5e7eb'}}>
          <ChatInterface chatId={currentChatId} />
        </main>
      </div>
    </SidebarProvider>
  );
};

export default Index;
