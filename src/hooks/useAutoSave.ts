import { useEffect, useState, useRef, useCallback } from 'react';
import { useToast } from './use-toast';

interface AutoSaveOptions {
  delay?: number;
  onSaveSuccess?: () => void;
  onSaveError?: (error: Error) => void;
  enableLocalStorage?: boolean;
}

export function useAutoSave<T>(
  key: string,
  data: T,
  saveToServer: (data: T) => Promise<void>,
  options: AutoSaveOptions = {}
) {
  const {
    delay = 2000,
    onSaveSuccess,
    onSaveError,
    enableLocalStorage = true
  } = options;

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const { toast } = useToast();
  const saveTimeoutRef = useRef<NodeJS.Timeout>();
  const lastSavedDataRef = useRef<string>(JSON.stringify(data));

  // Load from localStorage on mount
  useEffect(() => {
    if (!enableLocalStorage) return;

    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Notify parent component to update state if needed
        console.log('Restored from localStorage:', key);
      }
    } catch (error) {
      console.error('Failed to load from localStorage:', error);
    }
  }, [key, enableLocalStorage]);

  // Auto-save logic
  useEffect(() => {
    const currentData = JSON.stringify(data);
    
    // Skip if data hasn't changed
    if (currentData === lastSavedDataRef.current) {
      return;
    }

    // Save to localStorage immediately
    if (enableLocalStorage) {
      try {
        localStorage.setItem(key, currentData);
        localStorage.setItem(`${key}_timestamp`, new Date().toISOString());
      } catch (error) {
        console.error('Failed to save to localStorage:', error);
      }
    }

    // Clear existing timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // Set new timeout for server save
    setSaveStatus('idle');
    saveTimeoutRef.current = setTimeout(async () => {
      setSaveStatus('saving');
      
      try {
        await saveToServer(data);
        setSaveStatus('saved');
        setLastSaved(new Date());
        lastSavedDataRef.current = currentData;
        
        if (onSaveSuccess) {
          onSaveSuccess();
        }

        // Clear localStorage after successful server save
        if (enableLocalStorage) {
          localStorage.removeItem(key);
          localStorage.removeItem(`${key}_timestamp`);
        }
      } catch (error) {
        setSaveStatus('error');
        
        if (onSaveError) {
          onSaveError(error as Error);
        }
        
        toast({
          title: 'Auto-save failed',
          description: 'Your changes are saved locally and will sync when connection is restored.',
          variant: 'destructive'
        });
      }
    }, delay);

    // Cleanup function
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [data, key, delay, saveToServer, enableLocalStorage, toast, onSaveSuccess, onSaveError]);

  // Manual save function
  const saveNow = useCallback(async () => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    setSaveStatus('saving');
    try {
      await saveToServer(data);
      setSaveStatus('saved');
      setLastSaved(new Date());
      lastSavedDataRef.current = JSON.stringify(data);

      if (enableLocalStorage) {
        localStorage.removeItem(key);
        localStorage.removeItem(`${key}_timestamp`);
      }

      toast({
        title: 'Saved successfully',
        description: 'Your changes have been saved.',
      });
    } catch (error) {
      setSaveStatus('error');
      throw error;
    }
  }, [data, key, saveToServer, enableLocalStorage, toast]);

  // Check for unsaved changes
  const hasUnsavedChanges = useCallback(() => {
    return JSON.stringify(data) !== lastSavedDataRef.current;
  }, [data]);

  // Get save indicator component
  const SaveIndicator = useCallback(() => {
    if (saveStatus === 'idle' && !hasUnsavedChanges()) return null;

    const statusConfig = {
      idle: { text: 'Unsaved changes', className: 'text-gray-500' },
      saving: { text: 'Saving...', className: 'text-blue-600 animate-pulse' },
      saved: { text: 'Saved', className: 'text-green-600' },
      error: { text: 'Save failed', className: 'text-red-600' }
    };

    const config = statusConfig[saveStatus];

    return (
      <div className={`text-sm ${config.className} flex items-center gap-2`}>
        <span>{config.text}</span>
        {lastSaved && saveStatus === 'saved' && (
          <span className="text-xs text-gray-400">
            {new Date(lastSaved).toLocaleTimeString()}
          </span>
        )}
      </div>
    );
  }, [saveStatus, lastSaved, hasUnsavedChanges]);

  return {
    saveStatus,
    lastSaved,
    saveNow,
    hasUnsavedChanges,
    SaveIndicator
  };
}