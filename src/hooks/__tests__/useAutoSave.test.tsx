import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { render } from '@testing-library/react';
import React from 'react';
import { useAutoSave } from '../useAutoSave';

// Mock the toast hook
vi.mock('../use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useAutoSave', () => {
  const mockSaveToServer = vi.fn();
  const testData = { id: 1, name: 'Test' };
  const testKey = 'test-key';

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockSaveToServer.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('initial state', () => {
    it('should initialize with idle status', () => {
      const { result } = renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      expect(result.current.saveStatus).toBe('idle');
      expect(result.current.lastSaved).toBe(null);
      expect(result.current.hasUnsavedChanges()).toBe(false);
    });

    it('should attempt to load from localStorage on mount', () => {
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify(testData));

      renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      expect(localStorageMock.getItem).toHaveBeenCalledWith(testKey);
    });

    it('should handle localStorage errors gracefully', () => {
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error');
      });

      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      expect(consoleError).toHaveBeenCalledWith('Failed to load from localStorage:', expect.any(Error));
      consoleError.mockRestore();
    });

    it('should skip localStorage when disabled', () => {
      renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer, { enableLocalStorage: false })
      );

      expect(localStorageMock.getItem).not.toHaveBeenCalled();
    });
  });

  describe('auto-save behavior', () => {
    it('should save to localStorage immediately on data change', () => {
      const { rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer),
        { initialProps: { data: testData } }
      );

      const updatedData = { ...testData, name: 'Updated' };
      rerender({ data: updatedData });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(testKey, JSON.stringify(updatedData));
      expect(localStorageMock.setItem).toHaveBeenCalledWith(`${testKey}_timestamp`, expect.any(String));
    });

    it('should save to server after delay', async () => {
      const { rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 1000 }),
        { initialProps: { data: testData } }
      );

      const updatedData = { ...testData, name: 'Updated' };
      rerender({ data: updatedData });

      expect(mockSaveToServer).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(mockSaveToServer).toHaveBeenCalledWith(updatedData);
      });
    });

    it('should update status during save process', async () => {
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 100 }),
        { initialProps: { data: testData } }
      );

      const updatedData = { ...testData, name: 'Updated' };
      rerender({ data: updatedData });

      expect(result.current.saveStatus).toBe('idle');

      act(() => {
        vi.advanceTimersByTime(100);
      });

      expect(result.current.saveStatus).toBe('saving');

      await waitFor(() => {
        expect(result.current.saveStatus).toBe('saved');
        expect(result.current.lastSaved).toBeInstanceOf(Date);
      });
    });

    it('should clear localStorage after successful server save', async () => {
      const { rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 100 }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(localStorageMock.removeItem).toHaveBeenCalledWith(testKey);
        expect(localStorageMock.removeItem).toHaveBeenCalledWith(`${testKey}_timestamp`);
      });
    });

    it('should debounce multiple rapid changes', async () => {
      const { rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 1000 }),
        { initialProps: { data: testData } }
      );

      // Make multiple rapid changes
      rerender({ data: { ...testData, name: 'Update 1' } });
      act(() => { vi.advanceTimersByTime(500); });
      
      rerender({ data: { ...testData, name: 'Update 2' } });
      act(() => { vi.advanceTimersByTime(500); });
      
      rerender({ data: { ...testData, name: 'Update 3' } });
      act(() => { vi.advanceTimersByTime(1000); });

      await waitFor(() => {
        // Should only save once with the final data
        expect(mockSaveToServer).toHaveBeenCalledTimes(1);
        expect(mockSaveToServer).toHaveBeenCalledWith({ ...testData, name: 'Update 3' });
      });
    });

    it('should skip save when data hasnt changed', () => {
      const { rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer),
        { initialProps: { data: testData } }
      );

      // Rerender with same data
      rerender({ data: testData });

      act(() => {
        vi.advanceTimersByTime(2000);
      });

      expect(mockSaveToServer).not.toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should handle server save errors', async () => {
      const error = new Error('Network error');
      mockSaveToServer.mockRejectedValueOnce(error);

      const onSaveError = vi.fn();
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { 
          delay: 100,
          onSaveError 
        }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(result.current.saveStatus).toBe('error');
        expect(onSaveError).toHaveBeenCalledWith(error);
      });

      // Check if toast was called
      const { useToast } = await import('../use-toast');
      const toastMock = vi.mocked(useToast().toast);
      expect(toastMock).toHaveBeenCalledWith({
        title: 'Auto-save failed',
        description: 'Your changes are saved locally and will sync when connection is restored.',
        variant: 'destructive'
      });
    });

    it('should handle localStorage save errors', () => {
      localStorageMock.setItem.mockImplementationOnce(() => {
        throw new Error('Storage full');
      });

      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      expect(consoleError).toHaveBeenCalledWith('Failed to save to localStorage:', expect.any(Error));
      consoleError.mockRestore();
    });
  });

  describe('manual save', () => {
    it('should save immediately when saveNow is called', async () => {
      const { result } = renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      await act(async () => {
        await result.current.saveNow();
      });

      expect(mockSaveToServer).toHaveBeenCalledWith(testData);
      expect(result.current.saveStatus).toBe('saved');
      expect(result.current.lastSaved).toBeInstanceOf(Date);
    });

    it('should show success toast on manual save', async () => {
      const { result } = renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      await act(async () => {
        await result.current.saveNow();
      });

      const { useToast } = await import('../use-toast');
      const toastMock = vi.mocked(useToast().toast);
      expect(toastMock).toHaveBeenCalledWith({
        title: 'Saved successfully',
        description: 'Your changes have been saved.',
      });
    });

    it('should cancel pending auto-save when saveNow is called', async () => {
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 1000 }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      act(() => {
        vi.advanceTimersByTime(500);
      });

      await act(async () => {
        await result.current.saveNow();
      });

      // Advance time to when auto-save would have triggered
      act(() => {
        vi.advanceTimersByTime(500);
      });

      // Should only have been called once (by saveNow)
      expect(mockSaveToServer).toHaveBeenCalledTimes(1);
    });

    it('should handle errors in manual save', async () => {
      const error = new Error('Save failed');
      mockSaveToServer.mockRejectedValueOnce(error);

      const { result } = renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      await expect(result.current.saveNow()).rejects.toThrow('Save failed');
      expect(result.current.saveStatus).toBe('error');
    });
  });

  describe('hasUnsavedChanges', () => {
    it('should detect unsaved changes', () => {
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer),
        { initialProps: { data: testData } }
      );

      expect(result.current.hasUnsavedChanges()).toBe(false);

      rerender({ data: { ...testData, name: 'Updated' } });

      expect(result.current.hasUnsavedChanges()).toBe(true);
    });

    it('should return false after successful save', async () => {
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 100 }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      expect(result.current.hasUnsavedChanges()).toBe(true);

      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(result.current.hasUnsavedChanges()).toBe(false);
      });
    });
  });

  describe('SaveIndicator component', () => {
    it('should render nothing when no unsaved changes', () => {
      const { result } = renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      const { SaveIndicator } = result.current;
      const { container } = render(<SaveIndicator />);

      expect(container.firstChild).toBeNull();
    });

    it('should show unsaved changes indicator', () => {
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      const { SaveIndicator } = result.current;
      const { getByText } = render(<SaveIndicator />);

      expect(getByText('Unsaved changes')).toBeInTheDocument();
    });

    it('should show saving indicator', async () => {
      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 100 }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      act(() => {
        vi.advanceTimersByTime(100);
      });

      const { SaveIndicator } = result.current;
      const { getByText } = render(<SaveIndicator />);

      expect(getByText('Saving...')).toBeInTheDocument();
    });

    it('should show saved indicator with timestamp', async () => {
      const { result } = renderHook(() => 
        useAutoSave(testKey, testData, mockSaveToServer)
      );

      await act(async () => {
        await result.current.saveNow();
      });

      const { SaveIndicator } = result.current;
      const { getByText } = render(<SaveIndicator />);

      expect(getByText('Saved')).toBeInTheDocument();
      // Should also show timestamp
      expect(getByText(/\d{1,2}:\d{2}:\d{2}/)).toBeInTheDocument();
    });

    it('should show error indicator', async () => {
      mockSaveToServer.mockRejectedValueOnce(new Error('Save failed'));

      const { result, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 100 }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(result.current.saveStatus).toBe('error');
      });

      const { SaveIndicator } = result.current;
      const { getByText } = render(<SaveIndicator />);

      expect(getByText('Save failed')).toBeInTheDocument();
    });
  });

  describe('callbacks', () => {
    it('should call onSaveSuccess callback', async () => {
      const onSaveSuccess = vi.fn();
      const { rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { 
          delay: 100,
          onSaveSuccess 
        }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      act(() => {
        vi.advanceTimersByTime(100);
      });

      await waitFor(() => {
        expect(onSaveSuccess).toHaveBeenCalled();
      });
    });
  });

  describe('cleanup', () => {
    it('should clear timeout on unmount', () => {
      const { unmount, rerender } = renderHook(
        ({ data }) => useAutoSave(testKey, data, mockSaveToServer, { delay: 1000 }),
        { initialProps: { data: testData } }
      );

      rerender({ data: { ...testData, name: 'Updated' } });

      unmount();

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(mockSaveToServer).not.toHaveBeenCalled();
    });
  });
});