import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RefreshCw, Download, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SettingsDialog = ({ open, onOpenChange }: SettingsDialogProps) => {
  const [checking, setChecking] = useState(false);
  const [updateStatus, setUpdateStatus] = useState<'idle' | 'checking' | 'available' | 'not-available' | 'downloading' | 'error'>('idle');
  const [updateInfo, setUpdateInfo] = useState<any>(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const { toast } = useToast();

  const checkForUpdates = async () => {
    setChecking(true);
    setUpdateStatus('checking');

    try {
      // Check if running in Electron
      if (!(window as any).electronAPI) {
        toast({
          title: 'Not Available',
          description: 'Auto-update is only available in the desktop app.',
          variant: 'destructive',
        });
        setChecking(false);
        setUpdateStatus('error');
        return;
      }

      const result = await (window as any).electronAPI.checkForUpdates();
      
      if (result.success === false) {
        toast({
          title: 'Development Mode',
          description: result.message || 'Updates not available in development mode.',
        });
        setChecking(false);
        setUpdateStatus('idle');
        return;
      }

      // Listen for update events
      if ((window as any).electronAPI.onUpdateStatus) {
        (window as any).electronAPI.onUpdateStatus((status: string, info: any) => {
          console.log('Update status:', status, info);
          setUpdateStatus(status as any);
          if (info) {
            setUpdateInfo(info);
          }
        });
      }

      if ((window as any).electronAPI.onUpdateProgress) {
        (window as any).electronAPI.onUpdateProgress((progress: any) => {
          setDownloadProgress(Math.round(progress.percent));
        });
      }

      // Initial check will trigger update-status events
      setTimeout(() => {
        if (updateStatus === 'checking') {
          setUpdateStatus('not-available');
          setChecking(false);
          toast({
            title: 'No Updates',
            description: 'You are running the latest version.',
          });
        }
      }, 5000);

    } catch (error: any) {
      console.error('Error checking for updates:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to check for updates.',
        variant: 'destructive',
      });
      setChecking(false);
      setUpdateStatus('error');
    }
  };

  const getStatusIcon = () => {
    switch (updateStatus) {
      case 'checking':
        return <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />;
      case 'available':
        return <Download className="h-5 w-5 text-green-500" />;
      case 'downloading':
        return <Download className="h-5 w-5 animate-pulse text-blue-500" />;
      case 'not-available':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Info className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusMessage = () => {
    switch (updateStatus) {
      case 'checking':
        return 'Checking for updates...';
      case 'available':
        return `Update available: ${updateInfo?.version || 'New version'}`;
      case 'downloading':
        return `Downloading update: ${downloadProgress}%`;
      case 'not-available':
        return 'You are up to date!';
      case 'error':
        return 'Failed to check for updates';
      default:
        return 'Click to check for updates';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">Settings</DialogTitle>
          <DialogDescription>
            Manage your application settings and preferences.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Application Info */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">Application</h3>
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Version:</span>
                <span className="font-mono text-gray-900">
                  {(window as any).appInfo?.version || '1.0.0'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Platform:</span>
                <span className="font-mono text-gray-900">
                  {(window as any).electronAPI?.platform || 'web'}
                </span>
              </div>
            </div>
          </div>

          {/* Updates Section */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Updates</h3>
            
            {updateStatus !== 'idle' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-3">
                {getStatusIcon()}
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {getStatusMessage()}
                  </p>
                  {updateStatus === 'downloading' && (
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${downloadProgress}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}

            <Button
              onClick={checkForUpdates}
              disabled={checking || updateStatus === 'downloading'}
              className="w-full bg-gradient-to-r from-[#181C5A] to-[#B983FD] text-white hover:brightness-110"
            >
              {checking ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Checking...
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Check for Updates
                </>
              )}
            </Button>

            <p className="text-xs text-gray-500 text-center">
              Updates are checked automatically on startup
            </p>
          </div>

          {/* Additional Settings */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-gray-900">About</h3>
            <p className="text-sm text-gray-600">
              NemhemAI is an AI Chat Assistant for Desktop, built with Electron and React.
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
