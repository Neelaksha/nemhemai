
import { useState, useEffect, useCallback } from 'react';
import { Plus, MessageSquare, Settings, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useSidebar } from '@/components/ui/sidebar';
import { listChatSessionsAPI } from '@/lib/api';
import { getUserInfo } from '@/lib/api';
import { SettingsDialog } from './SettingsDialog';

interface Chat {
  id: string;
  title: string;
  timestamp: Date;
}

interface SidebarProps {
  currentChatId: string;
  onChatSelect: (chatId: string) => void;
}

export const Sidebar = ({ currentChatId, onChatSelect }: SidebarProps) => {
  const { open, setOpen } = useSidebar();
  const [chats, setChats] = useState<Chat[]>([]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load chat sessions for the user
  const loadChats = useCallback(async () => {
    const user = getUserInfo();
    if (!user) return;
    setLoading(true);
    try {
      const sessions = await listChatSessionsAPI();
      console.log('Loaded chat sessions:', sessions);
      if (Array.isArray(sessions)) {
        const userChats = sessions.map((s) => ({
          id: s.session_id,
          title: s.last_message?.slice(0, 30) || 'New Chat',
          timestamp: new Date(s.timestamp),
        }));
        setChats(userChats);
      } else {
        console.warn('Invalid sessions response:', sessions);
        setChats([]);
      }
    } catch (error) {
      console.error('Error loading chats:', error);
      if (error instanceof Error) {
        console.error('Error details:', error.message);
      }
      // Don't throw, just set empty array
      setChats([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load chats only once on mount
  useEffect(() => {
    loadChats();
  }, [loadChats]);

  // Listen for custom events to refresh the sidebar
  useEffect(() => {
    const handleRefresh = () => {
      console.log('Sidebar refresh requested');
      loadChats();
    };
    
    window.addEventListener('refreshSidebar', handleRefresh);
    return () => window.removeEventListener('refreshSidebar', handleRefresh);
  }, [loadChats]);

  const createNewChat = async () => {
    const newChatId = Date.now().toString();
    // Simply create a new chat ID and select it
    // The chat will be created in the backend when the first message is sent
    onChatSelect(newChatId);
    // Optionally refresh the chat list after a delay to show the new chat once a message is sent
  };

  return (
    <div className={`${!open ? 'w-16' : 'w-80'} transition-all duration-300 bg-white border-r border-gray-100 shadow-lg flex flex-col h-screen`}>
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setOpen(!open)}
            className="text-slate-400 hover:text-white hover:bg-slate-700/50 transition-all duration-200"
          >
            {!open ? <Menu className="h-5 w-5" /> : <X className="h-5 w-5" />}
          </Button>
          {open && (
            <Button
              onClick={createNewChat}
              className="bg-gradient-to-r from-[#181C5A] to-[#B983FD] text-white font-bold rounded-[12px] px-4 h-8 text-sm shadow-md hover:brightness-110 transition-all duration-200 flex items-center"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Chat
            </Button>
          )}
        </div>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1 px-2">
        {open && (
          <div className="space-y-2 py-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#A259FF]"></div>
              </div>
            ) : chats.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">
                No chat history yet.<br/>Start a conversation!
              </div>
            ) : (
              chats.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => {
                    console.log('Chat selected:', chat.id, chat.title);
                    onChatSelect(chat.id);
                  }}
                  className={`w-full text-left p-4 rounded-xl transition-all duration-200 ${
                    currentChatId === chat.id
                      ? 'bg-[#F3E8FF] text-black shadow border-2 border-[#A259FF]'
                      : 'hover:bg-gray-50 text-[#181C5A]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <MessageSquare className="h-4 w-4 text-slate-400" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-black truncate">
                        {chat.title}
                      </p>
                      <p className="text-xs text-slate-400">
                        {chat.timestamp.toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        )}
      </ScrollArea>

      {/* Settings */}
      <div className="p-4 border-t border-slate-700/50 mt-auto">
        <Button
          variant="ghost"
          onClick={() => setSettingsOpen(true)}
          className={`${!open ? 'w-8 h-8 p-0' : 'w-full justify-start'} text-slate-400 hover:text-white hover:bg-slate-700/50 transition-all duration-200`}
        >
          <Settings className="h-4 w-4" />
          {open && <span className="ml-2">Settings</span>}
        </Button>
      </div>

      {/* Settings Dialog */}
      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
};
