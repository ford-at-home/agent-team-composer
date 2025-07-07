import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProjectSummary from '../ProjectSummary';

describe('ProjectSummary', () => {
  const mockSummary = {
    title: 'Test Project',
    description: 'A test project description',
    domain: 'Web Application',
    repository: 'owner/repo',
    branch: 'main'
  };

  const mockSetSummary = vi.fn();
  const mockOnNext = vi.fn();
  
  // Add a delay helper for Radix UI animations
  const waitForRadixUI = () => new Promise(resolve => setTimeout(resolve, 100));

  const defaultProps = {
    summary: mockSummary,
    setSummary: mockSetSummary,
    onNext: mockOnNext
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render project title from summary', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    it('should render repository information', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      expect(screen.getByText('owner/repo')).toBeInTheDocument();
      expect(screen.getByText('main')).toBeInTheDocument();
    });

    it('should render project description in preview mode', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      expect(screen.getByText('A test project description')).toBeInTheDocument();
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('should render placeholder when no description', () => {
      const props = {
        ...defaultProps,
        summary: { ...mockSummary, description: '' }
      };
      
      render(<ProjectSummary {...props} />);
      
      expect(screen.getByText('No description provided')).toBeInTheDocument();
    });

    it('should render domain select with current value', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      expect(screen.getByText('Web Application')).toBeInTheDocument();
    });

    it('should render stats cards', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('Lifecycle Phases')).toBeInTheDocument();
      expect(screen.getByText('9')).toBeInTheDocument();
      expect(screen.getByText('Agent Roles')).toBeInTheDocument();
      expect(screen.getByText('~32')).toBeInTheDocument();
      expect(screen.getByText('Expected Issues')).toBeInTheDocument();
    });

    it('should render auto-detected badge', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      expect(screen.getByText('Auto-detected')).toBeInTheDocument();
    });
  });

  describe('description editing', () => {
    it('should toggle to edit mode when Edit button clicked', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      const editButton = screen.getByRole('button', { name: 'Edit' });
      await user.click(editButton);
      
      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Preview' })).toBeInTheDocument();
    });

    it('should show current description in textarea when editing', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      await user.click(screen.getByRole('button', { name: 'Edit' }));
      
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      expect(textarea.value).toBe('A test project description');
    });

    it.skip('should update description when typing', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      await user.click(screen.getByRole('button', { name: 'Edit' }));
      
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      
      // Type additional text (instead of replacing)
      await user.type(textarea, ' plus new text');
      
      // Check that setSummary was called with the appended text
      expect(mockSetSummary).toHaveBeenCalledWith({
        ...mockSummary,
        description: 'A test project description plus new text'
      });
    });

    it('should toggle back to preview mode', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      await user.click(screen.getByRole('button', { name: 'Edit' }));
      await user.click(screen.getByRole('button', { name: 'Preview' }));
      
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Edit' })).toBeInTheDocument();
    });
  });

  describe('domain selection', () => {
    it('should show all domain options when select is opened', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      const select = screen.getByRole('combobox');
      await user.click(select);
      
      const domains = [
        'Web Application',
        'Mobile App',
        'Data Science',
        'AI/ML Project',
        'API Service',
        'DevOps/Infrastructure',
        'Civic Tech',
        'E-commerce',
        'SaaS Platform'
      ];
      
      // Wait for dropdown to open and check each domain exists
      await waitFor(async () => {
        for (const domain of domains) {
          // Use getAllByText since the selected domain appears multiple times
          const elements = screen.getAllByText(domain);
          expect(elements.length).toBeGreaterThan(0);
        }
      });
    });

    it('should update domain when selection changes', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      const select = screen.getByRole('combobox');
      await user.click(select);
      
      // Find and click the Mobile App option
      const mobileOption = await screen.findByText('Mobile App');
      await user.click(mobileOption);
      
      expect(mockSetSummary).toHaveBeenCalledWith({
        ...mockSummary,
        domain: 'Mobile App'
      });
    });
  });

  describe('navigation', () => {
    it('should call onNext when Continue button is clicked', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      const continueButton = screen.getByRole('button', { name: /Configure Phases/i });
      await user.click(continueButton);
      
      expect(mockOnNext).toHaveBeenCalledTimes(1);
    });
  });

  describe('styling and accessibility', () => {
    it('should have proper labels for form controls', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      expect(screen.getByText('Repository')).toBeInTheDocument();
      expect(screen.getByText('Project Domain')).toBeInTheDocument();
      expect(screen.getByText('Project Description')).toBeInTheDocument();
    });

    it('should have gradient background on header', () => {
      render(<ProjectSummary {...defaultProps} />);
      
      const header = screen.getByText('Test Project').closest('.bg-gradient-to-r');
      expect(header).toHaveClass('from-blue-600', 'to-indigo-600');
    });

    it('should render icons', () => {
      const { container } = render(<ProjectSummary {...defaultProps} />);
      
      // Check for SVG icons
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should have responsive grid layout', () => {
      const { container } = render(<ProjectSummary {...defaultProps} />);
      
      const grids = container.querySelectorAll('.grid');
      expect(grids.length).toBeGreaterThan(0);
      
      // Check for responsive classes
      const responsiveGrid = container.querySelector('.md\\:grid-cols-2');
      expect(responsiveGrid).toBeInTheDocument();
    });
  });

  describe('edge cases', () => {
    it('should handle empty summary object gracefully', () => {
      const emptySummary = {
        title: '',
        description: '',
        domain: '',
        repository: '',
        branch: ''
      };
      
      render(<ProjectSummary summary={emptySummary} setSummary={mockSetSummary} onNext={mockOnNext} />);
      
      expect(screen.getByText('No description provided')).toBeInTheDocument();
    });

    it.skip('should handle very long descriptions', async () => {
      const user = userEvent.setup();
      const longText = ' - This is a very long additional text to test handling of long descriptions';
      
      render(<ProjectSummary {...defaultProps} />);
      
      await user.click(screen.getByRole('button', { name: 'Edit' }));
      
      const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
      
      // Type additional long text
      await user.type(textarea, longText);
      
      // Check that setSummary was called with the full text
      expect(mockSetSummary).toHaveBeenCalledWith({
        ...mockSummary,
        description: 'A test project description' + longText
      });
    });

    it('should handle rapid edit/preview toggles', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      for (let i = 0; i < 5; i++) {
        await user.click(screen.getByRole('button', { name: i % 2 === 0 ? 'Edit' : 'Preview' }));
      }
      
      // Should end in edit mode after 5 toggles
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });
  });

  describe('component integration', () => {
    it('should preserve other summary fields when updating', async () => {
      const user = userEvent.setup();
      render(<ProjectSummary {...defaultProps} />);
      
      // Change domain
      const select = screen.getByRole('combobox');
      await user.click(select);
      const mobileOption = await screen.findByText('Mobile App');
      await user.click(mobileOption);
      
      expect(mockSetSummary).toHaveBeenCalledWith({
        title: 'Test Project',
        description: 'A test project description',
        domain: 'Mobile App',
        repository: 'owner/repo',
        branch: 'main'
      });
      
      // All other fields should remain unchanged
      expect(mockSetSummary.mock.calls[0][0].title).toBe(mockSummary.title);
      expect(mockSetSummary.mock.calls[0][0].repository).toBe(mockSummary.repository);
    });

    it('should handle textarea placeholder correctly', async () => {
      const user = userEvent.setup();
      const props = {
        ...defaultProps,
        summary: { ...mockSummary, description: '' }
      };
      
      render(<ProjectSummary {...props} />);
      
      await user.click(screen.getByRole('button', { name: 'Edit' }));
      
      const textarea = screen.getByPlaceholderText('Describe your project goals and requirements...');
      expect(textarea).toBeInTheDocument();
    });
  });
});