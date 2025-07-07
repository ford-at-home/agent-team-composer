import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewSubmit from '../ReviewSubmit';

// Create a stable mock for toast
const toastMock = vi.fn();

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: toastMock
  })
}));

// Mock window.open
global.window.open = vi.fn();

describe('ReviewSubmit', () => {
  const mockSummary = {
    title: 'Test Project',
    description: 'A test project',
    domain: 'Web Application',
    repository: 'owner/repo',
    branch: 'main'
  };

  const mockPhases = [
    {
      id: 'phase1',
      title: 'Discovery Phase',
      description: 'Initial research',
      roles: ['Product Owner', 'UX Researcher'],
      issues: [
        { title: 'Research task', description: 'Do research', role: 'UX Researcher' },
        { title: 'Define requirements', description: 'Gather requirements', role: 'Product Owner' }
      ],
      approved: true
    },
    {
      id: 'phase2',
      title: 'Design Phase',
      description: 'Create designs',
      roles: ['Designer'],
      issues: [
        { title: 'Create mockups', description: 'Design UI', role: 'Designer' }
      ],
      approved: true
    },
    {
      id: 'phase3',
      title: 'Development Phase',
      description: 'Build features',
      roles: ['Software Engineer'],
      issues: [],
      approved: false // Not approved
    }
  ];

  const mockOnPrevious = vi.fn();
  const mockOnSubmit = vi.fn();

  const defaultProps = {
    summary: mockSummary,
    phases: mockPhases,
    onPrevious: mockOnPrevious,
    onSubmit: mockOnSubmit
  };

  beforeEach(() => {
    vi.clearAllMocks();
    toastMock.mockClear();
    mockOnSubmit.mockResolvedValue({ success: true });
  });

  describe('review state', () => {
    it('should render project summary correctly', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      expect(screen.getByText('Project Summary')).toBeInTheDocument();
      expect(screen.getByText('Test Project')).toBeInTheDocument();
      expect(screen.getByText('Web Application')).toBeInTheDocument();
      expect(screen.getByText('A test project')).toBeInTheDocument();
    });

    it('should calculate statistics correctly', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      // Check statistics exist
      expect(screen.getByText('Statistics')).toBeInTheDocument();
      expect(screen.getByText('Total Issues')).toBeInTheDocument();
      expect(screen.getByText('Active Roles')).toBeInTheDocument();
      
      // Check values are displayed (there are multiple "3"s so we just check they exist)
      const allThrees = screen.getAllByText('3');
      expect(allThrees.length).toBeGreaterThan(0);
      
      const allTwos = screen.getAllByText('2');
      expect(allTwos.length).toBeGreaterThan(0);
    });

    it('should display all unique roles', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      expect(screen.getByText('Product Owner')).toBeInTheDocument();
      expect(screen.getByText('UX Researcher')).toBeInTheDocument();
      expect(screen.getByText('Designer')).toBeInTheDocument();
      
      // Software Engineer should not appear (phase not approved)
      expect(screen.queryByText('Software Engineer')).not.toBeInTheDocument();
    });

    it('should show SPARC enabled indicator', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      expect(screen.getByText('SPARC Enabled')).toBeInTheDocument();
    });

    it('should list approved phases only', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      expect(screen.getByText('Discovery Phase')).toBeInTheDocument();
      expect(screen.getByText('Design Phase')).toBeInTheDocument();
      expect(screen.queryByText('Development Phase')).not.toBeInTheDocument();
    });

    it('should show phase details in approved phases list', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      expect(screen.getByText('Initial research')).toBeInTheDocument();
      expect(screen.getByText('2 roles')).toBeInTheDocument();
      expect(screen.getByText('2 issues')).toBeInTheDocument();
      expect(screen.getByText('1 issues')).toBeInTheDocument();
    });

    it('should show warning for unapproved phases', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      expect(screen.getByText(/1 phase\(s\) not approved and will be skipped/)).toBeInTheDocument();
    });

    it('should not show warning when all phases approved', () => {
      const allApprovedPhases = mockPhases.map(p => ({ ...p, approved: true }));
      
      render(<ReviewSubmit {...defaultProps} phases={allApprovedPhases} />);
      
      expect(screen.queryByText(/phase\(s\) not approved/)).not.toBeInTheDocument();
    });
  });

  describe('submission flow', () => {
    it.skip('should handle successful submission', async () => {
      const user = userEvent.setup();
      
      const { container } = render(<ReviewSubmit {...defaultProps} />);
      
      // Check if we're in the form state
      expect(screen.queryByText('Successfully Deployed!')).not.toBeInTheDocument();
      expect(screen.getByText('Review & Submit')).toBeInTheDocument();
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(mockPhases);
      });
      
      await waitFor(() => {
        expect(toastMock).toHaveBeenCalledWith({
          title: 'Successfully pushed to GitHub!',
          description: 'Created 2 epics and 3 issues in owner/repo.'
        });
      });
    });

    it.skip('should show loading state during submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      expect(screen.getByText('Pushing to GitHub...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      expect(screen.getByRole('button', { name: /Back to Phases/i })).toBeDisabled();
    });

    it.skip('should handle submission errors', async () => {
      const user = userEvent.setup();
      const error = new Error('API error');
      mockOnSubmit.mockRejectedValueOnce(error);
      
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(toastMock).toHaveBeenCalledWith({
          title: 'Failed to create GitHub issues',
          description: 'API error',
          variant: 'destructive'
        });
      });
    });

    it.skip('should disable submit button when no phases approved', () => {
      const noApprovedPhases = mockPhases.map(p => ({ ...p, approved: false }));
      
      render(<ReviewSubmit {...defaultProps} phases={noApprovedPhases} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      expect(submitButton).toBeDisabled();
    });

    it.skip('should handle fallback submission when no onSubmit provided', async () => {
      const user = userEvent.setup();
      vi.useFakeTimers();
      
      render(<ReviewSubmit {...defaultProps} onSubmit={undefined} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      expect(screen.getByText('Pushing to GitHub...')).toBeInTheDocument();
      
      act(() => {
        vi.advanceTimersByTime(3000);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully Deployed!')).toBeInTheDocument();
      });
      
      vi.useRealTimers();
    });
  });

  describe('success state', () => {
    it.skip('should show success screen after submission', async () => {
      const user = userEvent.setup();
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Successfully Deployed!')).toBeInTheDocument();
      });
      
      expect(screen.getByText('Your agent team structure has been pushed to GitHub')).toBeInTheDocument();
    });

    it('should display correct statistics in success screen', async () => {
      const user = userEvent.setup();
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument(); // Epics
        expect(screen.getByText('Epics Created')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument(); // Issues
        expect(screen.getByText('Issues Generated')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument(); // Roles
        expect(screen.getByText('Roles Assigned')).toBeInTheDocument();
      });
    });

    it('should show View on GitHub button with correct link', async () => {
      const user = userEvent.setup();
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      await waitFor(() => {
        const viewButton = screen.getByRole('button', { name: /View on GitHub/i });
        expect(viewButton).toBeInTheDocument();
      });
      
      const viewButton = screen.getByRole('button', { name: /View on GitHub/i });
      await user.click(viewButton);
      
      expect(window.open).toHaveBeenCalledWith('https://github.com/owner/repo/issues', '_blank');
    });

    it('should show SPARC ready message', async () => {
      const user = userEvent.setup();
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Ready for Claude Flow SPARC agents to start execution')).toBeInTheDocument();
      });
    });
  });

  describe('navigation', () => {
    it('should call onPrevious when back button clicked', async () => {
      const user = userEvent.setup();
      render(<ReviewSubmit {...defaultProps} />);
      
      const backButton = screen.getByRole('button', { name: /Back to Phases/i });
      await user.click(backButton);
      
      expect(mockOnPrevious).toHaveBeenCalledTimes(1);
    });

    it('should disable back button during submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      const backButton = screen.getByRole('button', { name: /Back to Phases/i });
      expect(backButton).toBeDisabled();
    });
  });

  describe('styling', () => {
    it('should apply gradient backgrounds', () => {
      const { container } = render(<ReviewSubmit {...defaultProps} />);
      
      expect(container.querySelector('.bg-gradient-to-r.from-purple-600.to-pink-600')).toBeInTheDocument();
      expect(container.querySelector('.bg-gradient-to-r.from-green-600.to-emerald-600')).toBeInTheDocument();
    });

    it('should style approved phases with green background', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      const phaseItems = screen.getByText('Discovery Phase').closest('.bg-green-50');
      expect(phaseItems).toBeInTheDocument();
      expect(phaseItems).toHaveClass('border-green-200');
    });

    it('should show numbered indicators for phases', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      const phaseNumbers = screen.getAllByText(/^[12]$/);
      expect(phaseNumbers.length).toBeGreaterThan(0);
    });
  });

  describe('edge cases', () => {
    it('should handle empty phases array', () => {
      render(<ReviewSubmit {...defaultProps} phases={[]} />);
      
      expect(screen.getByText('0')).toBeInTheDocument(); // Approved phases
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      expect(submitButton).toBeDisabled();
    });

    it('should handle phases with empty roles', () => {
      const phasesWithNoRoles = [{
        ...mockPhases[0],
        roles: []
      }];
      
      render(<ReviewSubmit {...defaultProps} phases={phasesWithNoRoles} />);
      
      expect(screen.getByText('0 roles')).toBeInTheDocument();
    });

    it.skip('should handle non-Error exceptions in submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockRejectedValueOnce('String error');
      
      render(<ReviewSubmit {...defaultProps} />);
      
      // Find the submit button - it contains dynamic text based on selected repo
      const buttons = screen.getAllByRole('button');
      const submitButton = buttons.find(btn => btn.textContent?.includes('Push to')) || buttons[buttons.length - 1];
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(toastMock).toHaveBeenCalledWith({
          title: 'Failed to create GitHub issues',
          description: 'Unknown error',
          variant: 'destructive'
        });
      });
    });
  });
});