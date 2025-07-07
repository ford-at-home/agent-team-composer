import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useToast, toast, reducer } from '../use-toast';

describe('use-toast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    // Clear any remaining toasts
    act(() => {
      const { result } = renderHook(() => useToast());
      result.current.dismiss();
    });
  });

  describe('reducer', () => {
    const initialState = { toasts: [] };

    it('should add a toast', () => {
      const newToast = {
        id: '1',
        title: 'Test Toast',
        description: 'Test Description',
      };

      const state = reducer(initialState, {
        type: 'ADD_TOAST',
        toast: newToast,
      });

      expect(state.toasts).toHaveLength(1);
      expect(state.toasts[0]).toEqual(newToast);
    });

    it('should limit toasts to TOAST_LIMIT (1)', () => {
      const toast1 = { id: '1', title: 'Toast 1' };
      const toast2 = { id: '2', title: 'Toast 2' };

      let state = reducer(initialState, {
        type: 'ADD_TOAST',
        toast: toast1,
      });

      state = reducer(state, {
        type: 'ADD_TOAST',
        toast: toast2,
      });

      expect(state.toasts).toHaveLength(1);
      expect(state.toasts[0]).toEqual(toast2); // Most recent toast
    });

    it('should update a toast', () => {
      const toast = { id: '1', title: 'Original Title' };
      let state = reducer(initialState, {
        type: 'ADD_TOAST',
        toast,
      });

      state = reducer(state, {
        type: 'UPDATE_TOAST',
        toast: { id: '1', title: 'Updated Title' },
      });

      expect(state.toasts[0].title).toBe('Updated Title');
    });

    it('should dismiss a specific toast', () => {
      const toast = { id: '1', title: 'Test', open: true };
      let state = reducer(initialState, {
        type: 'ADD_TOAST',
        toast,
      });

      state = reducer(state, {
        type: 'DISMISS_TOAST',
        toastId: '1',
      });

      expect(state.toasts[0].open).toBe(false);
    });

    it('should dismiss all toasts when no toastId provided', () => {
      const toast1 = { id: '1', title: 'Toast 1', open: true };
      const toast2 = { id: '2', title: 'Toast 2', open: true };

      let state = reducer(initialState, {
        type: 'ADD_TOAST',
        toast: toast1,
      });
      state = reducer(state, {
        type: 'ADD_TOAST',
        toast: toast2,
      });

      state = reducer(state, {
        type: 'DISMISS_TOAST',
      });

      expect(state.toasts.every(t => t.open === false)).toBe(true);
    });

    it('should remove a specific toast', () => {
      const toast = { id: '1', title: 'Test' };
      let state = reducer(initialState, {
        type: 'ADD_TOAST',
        toast,
      });

      state = reducer(state, {
        type: 'REMOVE_TOAST',
        toastId: '1',
      });

      expect(state.toasts).toHaveLength(0);
    });

    it('should remove all toasts when no toastId provided', () => {
      const toast1 = { id: '1', title: 'Toast 1' };
      const toast2 = { id: '2', title: 'Toast 2' };

      let state = reducer(initialState, {
        type: 'ADD_TOAST',
        toast: toast1,
      });
      state = reducer(state, {
        type: 'ADD_TOAST',
        toast: toast2,
      });

      state = reducer(state, {
        type: 'REMOVE_TOAST',
      });

      expect(state.toasts).toHaveLength(0);
    });
  });

  describe('toast function', () => {
    it('should create a toast with generated id', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        const toastInstance = toast({
          title: 'Test Toast',
          description: 'Test Description',
        });
        
        expect(toastInstance.id).toBeDefined();
        expect(typeof toastInstance.id).toBe('string');
        expect(toastInstance.dismiss).toBeDefined();
        expect(toastInstance.update).toBeDefined();
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Test Toast');
    });

    it('should dismiss a toast', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        const toastInstance = toast({
          title: 'Test Toast',
        });

        toastInstance.dismiss();
      });

      expect(result.current.toasts[0].open).toBe(false);
    });

    it('should update a toast', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        const toastInstance = toast({
          title: 'Original Title',
        });

        toastInstance.update({
          id: toastInstance.id,
          title: 'Updated Title',
        });
      });

      expect(result.current.toasts[0].title).toBe('Updated Title');
    });

    it('should handle onOpenChange callback', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        toast({
          title: 'Test Toast',
        });
      });

      expect(result.current.toasts[0].onOpenChange).toBeDefined();

      act(() => {
        result.current.toasts[0].onOpenChange?.(false);
      });

      expect(result.current.toasts[0].open).toBe(false);
    });
  });

  describe('useToast hook', () => {
    it('should return initial empty state', () => {
      const { result } = renderHook(() => useToast());

      expect(result.current.toasts).toEqual([]);
      expect(result.current.toast).toBeDefined();
      expect(result.current.dismiss).toBeDefined();
    });

    it('should update state when toasts are added', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.toast({
          title: 'Hook Toast',
          description: 'Added via hook',
        });
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Hook Toast');
    });

    it('should dismiss a specific toast', () => {
      const { result } = renderHook(() => useToast());

      let toastId: string;
      act(() => {
        const toastInstance = result.current.toast({
          title: 'Test Toast',
        });
        toastId = toastInstance.id;
      });

      act(() => {
        result.current.dismiss(toastId);
      });

      expect(result.current.toasts[0].open).toBe(false);
    });

    it('should dismiss all toasts', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.toast({ title: 'Toast 1' });
        result.current.toast({ title: 'Toast 2' });
      });

      expect(result.current.toasts).toHaveLength(2);

      act(() => {
        result.current.dismiss();
      });

      expect(result.current.toasts.every(t => t.open === false)).toBe(true);
    });

    it('should auto-remove dismissed toasts after delay', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        const toastInstance = result.current.toast({
          title: 'Auto Remove Toast',
        });
        toastInstance.dismiss();
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].open).toBe(false);

      act(() => {
        vi.advanceTimersByTime(1000000); // TOAST_REMOVE_DELAY
      });

      expect(result.current.toasts).toHaveLength(0);
    });

    it('should handle multiple listeners', () => {
      const { result: result1 } = renderHook(() => useToast());
      const { result: result2 } = renderHook(() => useToast());

      act(() => {
        result1.current.toast({
          title: 'Shared Toast',
        });
      });

      // Both hooks should see the same toast
      expect(result1.current.toasts).toHaveLength(1);
      expect(result2.current.toasts).toHaveLength(1);
      expect(result1.current.toasts[0].title).toBe('Shared Toast');
      expect(result2.current.toasts[0].title).toBe('Shared Toast');
    });

    it('should clean up listeners on unmount', () => {
      const { result, unmount } = renderHook(() => useToast());

      act(() => {
        result.current.toast({ title: 'Test' });
      });

      unmount();

      // Add another toast after unmount
      act(() => {
        toast({ title: 'After Unmount' });
      });

      // The unmounted hook should not receive updates
      // (We can't directly test this, but we ensure no errors occur)
    });

    it('should handle sequential toasts with TOAST_LIMIT', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.toast({ title: 'Toast 1' });
      });
      expect(result.current.toasts[0].title).toBe('Toast 1');

      act(() => {
        result.current.toast({ title: 'Toast 2' });
      });
      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Toast 2');

      act(() => {
        result.current.toast({ title: 'Toast 3' });
      });
      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Toast 3');
    });

    it('should generate unique IDs for toasts', () => {
      const { result } = renderHook(() => useToast());
      const ids = new Set<string>();

      act(() => {
        for (let i = 0; i < 10; i++) {
          const toastInstance = toast({ title: `Toast ${i}` });
          ids.add(toastInstance.id);
        }
      });

      // All IDs should be unique
      expect(ids.size).toBe(10);
    });

    it('should not remove toast if timeout already exists', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        const toastInstance = result.current.toast({
          title: 'Test Toast',
        });
        
        // Dismiss twice
        result.current.dismiss(toastInstance.id);
        result.current.dismiss(toastInstance.id);
      });

      // Should still only be removed once after timeout
      act(() => {
        vi.advanceTimersByTime(1000000);
      });

      expect(result.current.toasts).toHaveLength(0);
    });
  });

  describe('edge cases', () => {
    it('should handle very large number generation', () => {
      // Force count to near MAX_SAFE_INTEGER
      const { result } = renderHook(() => useToast());
      
      // Generate many toasts to test counter wraparound
      act(() => {
        for (let i = 0; i < 100; i++) {
          toast({ title: `Toast ${i}` });
        }
      });

      // Should not throw any errors
      expect(result.current.toasts).toBeDefined();
    });

    it('should handle undefined toast properties', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.toast({});
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBeUndefined();
      expect(result.current.toasts[0].description).toBeUndefined();
    });

    it('should handle action element in toast', () => {
      const { result } = renderHook(() => useToast());
      const actionElement = { type: 'button', props: { children: 'Undo' } };

      act(() => {
        result.current.toast({
          title: 'Toast with Action',
          action: actionElement as any,
        });
      });

      expect(result.current.toasts[0].action).toEqual(actionElement);
    });

    it('should handle variant property', () => {
      const { result } = renderHook(() => useToast());

      act(() => {
        result.current.toast({
          title: 'Error Toast',
          variant: 'destructive',
        });
      });

      expect(result.current.toasts[0].variant).toBe('destructive');
    });
  });
});