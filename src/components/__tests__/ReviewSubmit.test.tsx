import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReviewSubmit from '../ReviewSubmit';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
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
    mockOnSubmit.mockResolvedValue({ success: true });
  });

  describe('review state', () => {
    it('should render project summary correctly', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      expect(screen.getByText('Project Summary')).toBeInTheDocument();
      expect(screen.getByText('owner/repo')).toBeInTheDocument();
      expect(screen.getByText('Web Application')).toBeInTheDocument();
      expect(screen.getByText('main')).toBeInTheDocument();
    });

    it('should calculate statistics correctly', () => {
      render(<ReviewSubmit {...defaultProps} />);
      
      // 2 approved phases
      expect(screen.getByText('Approved Phases')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      
      // 3 total issues (2 + 1)
      expect(screen.getByText('Total Issues')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      
      // 3 unique roles
      expect(screen.getByText('Active Roles')).toBeInTheDocument();
      const activeRolesCard = screen.getByText('Active Roles').closest('.space-y-4');
      expect(activeRolesCard?.textContent).toContain('3');
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
    it('should handle successful submission', async () => {
      const user = userEvent.setup();
      const { useToast } = await import('@/hooks/use-toast');
      const toastMock = vi.mocked(useToast().toast);
      
      render(<ReviewSubmit {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(mockPhases);
      });
      
      await waitFor(() => {
        expect(toastMock).toHaveBeenCalledWith({
          title: 'Successfully pushed to GitHub!',
          description: 'Created 2 epics and 3 issues.'
        });
      });
    });

    it('should show loading state during submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      
      render(<ReviewSubmit {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
      await user.click(submitButton);
      
      expect(screen.getByText('Pushing to GitHub...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      expect(screen.getByRole('button', { name: /Back to Phases/i })).toBeDisabled();
    });

    it('should handle submission errors', async () => {
      const user = userEvent.setup();
      const error = new Error('API error');
      mockOnSubmit.mockRejectedValueOnce(error);
      
      const { useToast } = await import('@/hooks/use-toast');
      const toastMock = vi.mocked(useToast().toast);
      
      render(<ReviewSubmit {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(toastMock).toHaveBeenCalledWith({
          title: 'Failed to create GitHub issues',
          description: 'API error',
          variant: 'destructive'
        });
      });
    });

    it('should disable submit button when no phases approved', () => {
      const noApprovedPhases = mockPhases.map(p => ({ ...p, approved: false }));
      
      render(<ReviewSubmit {...defaultProps} phases={noApprovedPhases} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
      expect(submitButton).toBeDisabled();
    });

    it('should handle fallback submission when no onSubmit provided', async () => {
      const user = userEvent.setup();
      vi.useFakeTimers();
      
      render(<ReviewSubmit {...defaultProps} onSubmit={undefined} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
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
    it('should show success screen after submission', async () => {
      const user = userEvent.setup();
      render(<ReviewSubmit {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
      await user.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Successfully Deployed!')).toBeInTheDocument();
      });
      
      expect(screen.getByText('Your agent team structure has been pushed to GitHub')).toBeInTheDocument();
    });

    it('should display correct statistics in success screen', async () => {
      const user = userEvent.setup();
      render(<ReviewSubmit {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
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
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
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
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
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
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
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
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
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

    it('should handle non-Error exceptions in submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockRejectedValueOnce('String error');
      
      const { useToast } = await import('@/hooks/use-toast');
      const toastMock = vi.mocked(useToast().toast);
      
      render(<ReviewSubmit {...defaultProps} />);
      
      const submitButton = screen.getByRole('button', { name: /Push to GitHub/i });
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