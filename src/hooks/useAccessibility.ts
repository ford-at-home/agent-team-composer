import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Custom hook for managing focus and keyboard navigation
 */
export function useFocusManagement<T extends HTMLElement = HTMLElement>(
  itemCount: number,
  options: {
    orientation?: 'horizontal' | 'vertical';
    loop?: boolean;
    onItemSelect?: (index: number) => void;
  } = {}
) {
  const { orientation = 'vertical', loop = true, onItemSelect } = options;
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const itemRefs = useRef<(T | null)[]>([]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    const key = event.key;
    const currentIndex = focusedIndex;

    let nextIndex = currentIndex;

    switch (key) {
      case 'ArrowDown':
      case 'ArrowRight':
        if (
          (orientation === 'vertical' && key === 'ArrowDown') ||
          (orientation === 'horizontal' && key === 'ArrowRight')
        ) {
          event.preventDefault();
          nextIndex = currentIndex + 1;
          if (nextIndex >= itemCount) {
            nextIndex = loop ? 0 : itemCount - 1;
          }
        }
        break;

      case 'ArrowUp':
      case 'ArrowLeft':
        if (
          (orientation === 'vertical' && key === 'ArrowUp') ||
          (orientation === 'horizontal' && key === 'ArrowLeft')
        ) {
          event.preventDefault();
          nextIndex = currentIndex - 1;
          if (nextIndex < 0) {
            nextIndex = loop ? itemCount - 1 : 0;
          }
        }
        break;

      case 'Home':
        event.preventDefault();
        nextIndex = 0;
        break;

      case 'End':
        event.preventDefault();
        nextIndex = itemCount - 1;
        break;

      case 'Enter':
      case ' ':
        event.preventDefault();
        if (onItemSelect && currentIndex >= 0) {
          onItemSelect(currentIndex);
        }
        break;

      default:
        return;
    }

    if (nextIndex !== currentIndex && nextIndex >= 0 && nextIndex < itemCount) {
      setFocusedIndex(nextIndex);
      itemRefs.current[nextIndex]?.focus();
    }
  }, [focusedIndex, itemCount, loop, orientation, onItemSelect]);

  const setItemRef = useCallback((index: number, ref: T | null) => {
    itemRefs.current[index] = ref;
  }, []);

  return {
    focusedIndex,
    setFocusedIndex,
    handleKeyDown,
    setItemRef,
    itemRefs: itemRefs.current
  };
}

/**
 * Custom hook for managing ARIA live region announcements
 */
export function useAnnouncement() {
  const [announcement, setAnnouncement] = useState('');
  const [priority, setPriority] = useState<'polite' | 'assertive'>('polite');
  const timeoutRef = useRef<NodeJS.Timeout>();

  const announce = useCallback((
    message: string,
    options: {
      priority?: 'polite' | 'assertive';
      clearAfter?: number;
    } = {}
  ) => {
    const { priority = 'polite', clearAfter = 5000 } = options;

    // Clear previous announcement to ensure re-announcement
    setAnnouncement('');
    setPriority(priority);

    // Set new announcement after a brief delay
    setTimeout(() => {
      setAnnouncement(message);

      // Clear announcement after specified time
      if (clearAfter > 0) {
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
          setAnnouncement('');
        }, clearAfter);
      }
    }, 100);
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const AnnouncementRegion = () => (
    <>
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        aria-relevant="additions"
      >
        {priority === 'polite' ? announcement : ''}
      </div>
      <div
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        aria-relevant="additions"
      >
        {priority === 'assertive' ? announcement : ''}
      </div>
    </>
  );

  return {
    announce,
    announcement,
    AnnouncementRegion
  };
}

/**
 * Custom hook for managing focus trap
 */
export function useFocusTrap<T extends HTMLElement = HTMLElement>(
  isActive: boolean = true
) {
  const containerRef = useRef<T>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    // Focus first element when trap activates
    firstElement.focus();

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [isActive]);

  return containerRef;
}

/**
 * Custom hook for skip links
 */
export function useSkipLinks() {
  const SkipLinks = () => (
    <div className="sr-only focus-within:not-sr-only">
      <a
        href="#main-content"
        className="absolute top-0 left-0 p-2 bg-blue-600 text-white focus:not-sr-only"
      >
        Skip to main content
      </a>
      <a
        href="#navigation"
        className="absolute top-0 left-0 p-2 bg-blue-600 text-white focus:not-sr-only"
      >
        Skip to navigation
      </a>
    </div>
  );

  return { SkipLinks };
}