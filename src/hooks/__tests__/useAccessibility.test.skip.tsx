import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { render, fireEvent } from '@testing-library/react';
import React from 'react';
import { 
  useFocusManagement, 
  useAnnouncement, 
  useFocusTrap,
  useSkipLinks 
} from '../useAccessibility';

describe('useFocusManagement', () => {
  describe('keyboard navigation', () => {
    it('should handle vertical navigation with arrow keys', () => {
      const { result } = renderHook(() => 
        useFocusManagement(5, { orientation: 'vertical' })
      );

      // Mock focus method
      const mockFocus = vi.fn();
      act(() => {
        for (let i = 0; i < 5; i++) {
          result.current.setItemRef(i, { focus: mockFocus } as any);
        }
      });

      // Initial focus
      act(() => {
        result.current.setFocusedIndex(0);
      });

      // Navigate down
      const downEvent = {
        key: 'ArrowDown',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(downEvent);
      });

      expect(result.current.focusedIndex).toBe(1);
      expect(mockFocus).toHaveBeenCalled();
      expect(downEvent.preventDefault).toHaveBeenCalled();

      // Navigate up
      const upEvent = {
        key: 'ArrowUp',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(upEvent);
      });

      expect(result.current.focusedIndex).toBe(0);
    });

    it('should handle horizontal navigation with arrow keys', () => {
      const { result } = renderHook(() => 
        useFocusManagement(3, { orientation: 'horizontal' })
      );

      const mockFocus = vi.fn();
      act(() => {
        for (let i = 0; i < 3; i++) {
          result.current.setItemRef(i, { focus: mockFocus } as any);
        }
        result.current.setFocusedIndex(1);
      });

      // Navigate right
      const rightEvent = {
        key: 'ArrowRight',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(rightEvent);
      });

      expect(result.current.focusedIndex).toBe(2);

      // Navigate left
      const leftEvent = {
        key: 'ArrowLeft',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(leftEvent);
      });

      expect(result.current.focusedIndex).toBe(1);
    });

    it('should handle looping when enabled', () => {
      const { result } = renderHook(() => 
        useFocusManagement(3, { loop: true })
      );

      const mockFocus = vi.fn();
      act(() => {
        for (let i = 0; i < 3; i++) {
          result.current.setItemRef(i, { focus: mockFocus } as any);
        }
        result.current.setFocusedIndex(2);
      });

      // Navigate down from last item - should loop to first
      const downEvent = {
        key: 'ArrowDown',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(downEvent);
      });

      expect(result.current.focusedIndex).toBe(0);

      // Navigate up from first item - should loop to last
      const upEvent = {
        key: 'ArrowUp',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(upEvent);
      });

      expect(result.current.focusedIndex).toBe(2);
    });

    it('should not loop when disabled', () => {
      const { result } = renderHook(() => 
        useFocusManagement(3, { loop: false })
      );

      const mockFocus = vi.fn();
      act(() => {
        for (let i = 0; i < 3; i++) {
          result.current.setItemRef(i, { focus: mockFocus } as any);
        }
        result.current.setFocusedIndex(2);
      });

      // Try to navigate down from last item
      const downEvent = {
        key: 'ArrowDown',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(downEvent);
      });

      expect(result.current.focusedIndex).toBe(2); // Should stay at last item

      // Move to first and try to go up
      act(() => {
        result.current.setFocusedIndex(0);
      });

      const upEvent = {
        key: 'ArrowUp',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(upEvent);
      });

      expect(result.current.focusedIndex).toBe(0); // Should stay at first item
    });

    it('should handle Home and End keys', () => {
      const { result } = renderHook(() => 
        useFocusManagement(5)
      );

      const mockFocus = vi.fn();
      act(() => {
        for (let i = 0; i < 5; i++) {
          result.current.setItemRef(i, { focus: mockFocus } as any);
        }
        result.current.setFocusedIndex(2);
      });

      // Press Home
      const homeEvent = {
        key: 'Home',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(homeEvent);
      });

      expect(result.current.focusedIndex).toBe(0);

      // Press End
      const endEvent = {
        key: 'End',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(endEvent);
      });

      expect(result.current.focusedIndex).toBe(4);
    });

    it('should handle Enter and Space for selection', () => {
      const onItemSelect = vi.fn();
      const { result } = renderHook(() => 
        useFocusManagement(3, { onItemSelect })
      );

      act(() => {
        result.current.setFocusedIndex(1);
      });

      // Press Enter
      const enterEvent = {
        key: 'Enter',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(enterEvent);
      });

      expect(onItemSelect).toHaveBeenCalledWith(1);

      // Press Space
      const spaceEvent = {
        key: ' ',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(spaceEvent);
      });

      expect(onItemSelect).toHaveBeenCalledTimes(2);
      expect(onItemSelect).toHaveBeenLastCalledWith(1);
    });

    it('should ignore irrelevant keys', () => {
      const { result } = renderHook(() => 
        useFocusManagement(3)
      );

      act(() => {
        result.current.setFocusedIndex(1);
      });

      const event = {
        key: 'a',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(event);
      });

      expect(event.preventDefault).not.toHaveBeenCalled();
      expect(result.current.focusedIndex).toBe(1);
    });

    it('should handle empty item list', () => {
      const { result } = renderHook(() => 
        useFocusManagement(0)
      );

      const event = {
        key: 'ArrowDown',
        preventDefault: vi.fn()
      } as any;

      act(() => {
        result.current.handleKeyDown(event);
      });

      expect(result.current.focusedIndex).toBe(-1);
    });
  });

  describe('ref management', () => {
    it('should store item refs correctly', () => {
      const { result } = renderHook(() => 
        useFocusManagement(3)
      );

      const elem1 = document.createElement('div');
      const elem2 = document.createElement('div');

      act(() => {
        result.current.setItemRef(0, elem1 as any);
        result.current.setItemRef(1, elem2 as any);
        result.current.setItemRef(2, null);
      });

      expect(result.current.itemRefs[0]).toBe(elem1);
      expect(result.current.itemRefs[1]).toBe(elem2);
      expect(result.current.itemRefs[2]).toBe(null);
    });
  });
});

describe('useAnnouncement', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should announce message after delay', () => {
    const { result } = renderHook(() => useAnnouncement());

    act(() => {
      result.current.announce('Test announcement');
    });

    expect(result.current.announcement).toBe('');

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current.announcement).toBe('Test announcement');
  });

  it('should clear announcement after specified time', () => {
    const { result } = renderHook(() => useAnnouncement());

    act(() => {
      result.current.announce('Test', { clearAfter: 1000 });
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current.announcement).toBe('Test');

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(result.current.announcement).toBe('');
  });

  it('should handle assertive priority', () => {
    const { result } = renderHook(() => useAnnouncement());

    act(() => {
      result.current.announce('Urgent', { priority: 'assertive' });
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    const { AnnouncementRegion } = result.current;
    const { container } = render(<AnnouncementRegion />);

    const assertiveRegion = container.querySelector('[aria-live="assertive"]');
    const politeRegion = container.querySelector('[aria-live="polite"]');

    expect(assertiveRegion?.textContent).toBe('Urgent');
    expect(politeRegion?.textContent).toBe('');
  });

  it('should handle polite priority', () => {
    const { result } = renderHook(() => useAnnouncement());

    act(() => {
      result.current.announce('Info', { priority: 'polite' });
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    const { AnnouncementRegion } = result.current;
    const { container } = render(<AnnouncementRegion />);

    const assertiveRegion = container.querySelector('[aria-live="assertive"]');
    const politeRegion = container.querySelector('[aria-live="polite"]');

    expect(politeRegion?.textContent).toBe('Info');
    expect(assertiveRegion?.textContent).toBe('');
  });

  it('should cancel previous announcement timeout', () => {
    const { result } = renderHook(() => useAnnouncement());

    act(() => {
      result.current.announce('First', { clearAfter: 1000 });
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    act(() => {
      result.current.announce('Second', { clearAfter: 2000 });
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current.announcement).toBe('Second');

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // First timeout should have been cancelled
    expect(result.current.announcement).toBe('Second');

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(result.current.announcement).toBe('');
  });

  it('should not clear if clearAfter is 0', () => {
    const { result } = renderHook(() => useAnnouncement());

    act(() => {
      result.current.announce('Permanent', { clearAfter: 0 });
    });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current.announcement).toBe('Permanent');

    act(() => {
      vi.advanceTimersByTime(10000);
    });

    expect(result.current.announcement).toBe('Permanent');
  });

  it('should cleanup timeout on unmount', () => {
    const { result, unmount } = renderHook(() => useAnnouncement());

    act(() => {
      result.current.announce('Test', { clearAfter: 5000 });
    });

    unmount();

    // Should not throw
    act(() => {
      vi.advanceTimersByTime(5000);
    });
  });

  it('should render AnnouncementRegion with correct attributes', () => {
    const { result } = renderHook(() => useAnnouncement());
    const { AnnouncementRegion } = result.current;
    const { container } = render(<AnnouncementRegion />);

    const regions = container.querySelectorAll('[aria-live]');
    expect(regions).toHaveLength(2);

    regions.forEach(region => {
      expect(region).toHaveAttribute('aria-atomic', 'true');
      expect(region).toHaveAttribute('aria-relevant', 'additions');
      expect(region).toHaveClass('sr-only');
    });
  });
});

describe('useFocusTrap', () => {
  it('should trap focus within container', () => {
    const { result } = renderHook(() => useFocusTrap(true));

    const container = document.createElement('div');
    const button1 = document.createElement('button');
    const button2 = document.createElement('button');
    const button3 = document.createElement('button');

    container.appendChild(button1);
    container.appendChild(button2);
    container.appendChild(button3);

    // Mock focus method
    button1.focus = vi.fn();
    button2.focus = vi.fn();
    button3.focus = vi.fn();

    (result.current as any).current = container;

    // Re-run effect
    const { rerender } = renderHook(() => useFocusTrap(true));
    rerender();

    // Should focus first element
    expect(button1.focus).toHaveBeenCalled();

    // Simulate Tab from last element
    const tabEvent = new KeyboardEvent('keydown', { 
      key: 'Tab',
      shiftKey: false 
    });
    Object.defineProperty(document, 'activeElement', {
      value: button3,
      configurable: true
    });

    container.dispatchEvent(tabEvent);

    expect(button1.focus).toHaveBeenCalledTimes(2);
  });

  it('should handle Shift+Tab to loop to last element', () => {
    const { result } = renderHook(() => useFocusTrap(true));

    const container = document.createElement('div');
    const button1 = document.createElement('button');
    const button2 = document.createElement('button');

    container.appendChild(button1);
    container.appendChild(button2);

    button1.focus = vi.fn();
    button2.focus = vi.fn();

    (result.current as any).current = container;

    const { rerender } = renderHook(() => useFocusTrap(true));
    rerender();

    // Simulate Shift+Tab from first element
    const shiftTabEvent = new KeyboardEvent('keydown', { 
      key: 'Tab',
      shiftKey: true 
    });
    Object.defineProperty(document, 'activeElement', {
      value: button1,
      configurable: true
    });

    container.dispatchEvent(shiftTabEvent);

    expect(button2.focus).toHaveBeenCalled();
  });

  it('should not trap when inactive', () => {
    const { result } = renderHook(() => useFocusTrap(false));

    const container = document.createElement('div');
    const button = document.createElement('button');
    container.appendChild(button);

    button.focus = vi.fn();

    (result.current as any).current = container;

    const { rerender } = renderHook(() => useFocusTrap(false));
    rerender();

    expect(button.focus).not.toHaveBeenCalled();
  });

  it('should handle containers with no focusable elements', () => {
    const { result } = renderHook(() => useFocusTrap(true));

    const container = document.createElement('div');
    const span = document.createElement('span');
    container.appendChild(span);

    (result.current as any).current = container;

    // Should not throw
    const { rerender } = renderHook(() => useFocusTrap(true));
    rerender();
  });

  it('should ignore non-Tab keys', () => {
    const { result } = renderHook(() => useFocusTrap(true));

    const container = document.createElement('div');
    const button = document.createElement('button');
    container.appendChild(button);

    (result.current as any).current = container;

    const { rerender } = renderHook(() => useFocusTrap(true));
    rerender();

    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' });
    const preventDefault = vi.fn();
    Object.defineProperty(enterEvent, 'preventDefault', { value: preventDefault });

    container.dispatchEvent(enterEvent);

    expect(preventDefault).not.toHaveBeenCalled();
  });

  it('should cleanup event listener on unmount', () => {
    const { result, unmount } = renderHook(() => useFocusTrap(true));

    const container = document.createElement('div');
    const button = document.createElement('button');
    container.appendChild(button);

    const removeEventListener = vi.spyOn(container, 'removeEventListener');

    (result.current as any).current = container;

    const { rerender } = renderHook(() => useFocusTrap(true));
    rerender();

    unmount();

    expect(removeEventListener).toHaveBeenCalledWith('keydown', expect.any(Function));
  });
});

describe('useSkipLinks', () => {
  it('should render skip links with correct structure', () => {
    const { result } = renderHook(() => useSkipLinks());
    const { SkipLinks } = result.current;

    const { container } = render(<SkipLinks />);

    const links = container.querySelectorAll('a');
    expect(links).toHaveLength(2);

    expect(links[0]).toHaveAttribute('href', '#main-content');
    expect(links[0]).toHaveTextContent('Skip to main content');

    expect(links[1]).toHaveAttribute('href', '#navigation');
    expect(links[1]).toHaveTextContent('Skip to navigation');
  });

  it('should have correct accessibility classes', () => {
    const { result } = renderHook(() => useSkipLinks());
    const { SkipLinks } = result.current;

    const { container } = render(<SkipLinks />);

    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('sr-only', 'focus-within:not-sr-only');

    const links = container.querySelectorAll('a');
    links.forEach(link => {
      expect(link).toHaveClass('absolute', 'top-0', 'left-0', 'p-2', 'bg-blue-600', 'text-white', 'focus:not-sr-only');
    });
  });
});