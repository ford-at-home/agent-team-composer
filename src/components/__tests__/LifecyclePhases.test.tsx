import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LifecyclePhases from '../LifecyclePhases';

describe('LifecyclePhases', () => {
  const mockPhases = [
    {
      id: 'phase1',
      title: 'Discovery Phase',
      description: 'Initial research and planning',
      roles: ['Product Owner', 'UX Researcher'],
      issues: [
        {
          title: 'User Research',
          description: 'Conduct user interviews',
          role: 'UX Researcher'
        },
        {
          title: 'Requirements Gathering',
          description: 'Define project requirements',
          role: 'Product Owner'
        }
      ],
      approved: false
    },
    {
      id: 'phase2',
      title: 'Design Phase',
      description: 'UI/UX design and architecture',
      roles: ['Designer', 'AI Architect'],
      issues: [
        {
          title: 'Create Wireframes',
          description: 'Design initial wireframes',
          role: 'Designer'
        }
      ],
      approved: true
    }
  ];

  const mockSetPhases = vi.fn();
  const mockOnNext = vi.fn();
  const mockOnPrevious = vi.fn();

  const defaultProps = {
    phases: mockPhases,
    setPhases: mockSetPhases,
    onNext: mockOnNext,
    onPrevious: mockOnPrevious
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render all phases', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      expect(screen.getByText('Discovery Phase')).toBeInTheDocument();
      expect(screen.getByText('Design Phase')).toBeInTheDocument();
    });

    it('should show phase descriptions', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      expect(screen.getByText('Initial research and planning')).toBeInTheDocument();
      expect(screen.getByText('UI/UX design and architecture')).toBeInTheDocument();
    });

    it('should display progress header', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      expect(screen.getByText('Configure Lifecycle Phases')).toBeInTheDocument();
      expect(screen.getByText('1/2')).toBeInTheDocument(); // 1 approved out of 2
      expect(screen.getByText('Phases Approved')).toBeInTheDocument();
    });

    it('should show role and issue counts', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      expect(screen.getByText('2 roles')).toBeInTheDocument(); // Phase 1
      expect(screen.getByText('2 issues')).toBeInTheDocument(); // Phase 1
      expect(screen.getByText('1 issues')).toBeInTheDocument(); // Phase 2
    });

    it('should apply approved styling to approved phases', () => {
      const { container } = render(<LifecyclePhases {...defaultProps} />);
      
      // Find the approved phase card
      const approvedCard = container.querySelector('.border-green-200');
      expect(approvedCard).toBeInTheDocument();
    });

    it('should show phase numbers or check icons', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      // First phase should show "1"
      expect(screen.getByText('1')).toBeInTheDocument();
      
      // Second phase (approved) should have check icon
      const approvedPhase = screen.getByText('Design Phase').closest('.cursor-pointer');
      const checkIcon = approvedPhase?.querySelector('svg');
      expect(checkIcon).toBeInTheDocument();
    });
  });

  describe('collapsible behavior', () => {
    it('should expand first phase by default', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      // Check if issues for first phase are visible
      expect(screen.getByText('User Research')).toBeInTheDocument();
      expect(screen.getByText('Conduct user interviews')).toBeInTheDocument();
    });

    it('should toggle phase expansion on header click', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // Click on second phase header
      const designPhaseHeader = screen.getByText('Design Phase').closest('.cursor-pointer');
      await user.click(designPhaseHeader!);
      
      // Should show design phase issues
      expect(screen.getByText('Create Wireframes')).toBeInTheDocument();
    });

    it('should collapse expanded phase on second click', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // First phase is initially expanded
      expect(screen.getByText('User Research')).toBeInTheDocument();
      
      // Click to collapse
      const discoveryPhaseHeader = screen.getByText('Discovery Phase').closest('.cursor-pointer');
      await user.click(discoveryPhaseHeader!);
      
      // Issues should be hidden
      expect(screen.queryByText('User Research')).not.toBeInTheDocument();
    });
  });

  describe('role management', () => {
    it('should display all available roles', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // Expand first phase if needed
      const firstPhaseHeader = screen.getByText('Discovery Phase').closest('.cursor-pointer');
      await user.click(firstPhaseHeader!);
      
      const roles = [
        'Product Owner',
        'Software Engineer',
        'AI Architect',
        'DevOps Engineer',
        'QA Engineer',
        'Designer',
        'UX Researcher',
        'Data Scientist',
        'Content Writer'
      ];
      
      roles.forEach(role => {
        expect(screen.getAllByText(role)[0]).toBeInTheDocument();
      });
    });

    it('should show checked roles correctly', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      // Find checkboxes for phase1 roles
      const productOwnerCheckbox = screen.getByRole('checkbox', { name: /Product Owner/i });
      const uxResearcherCheckbox = screen.getByRole('checkbox', { name: /UX Researcher/i });
      
      expect(productOwnerCheckbox).toBeChecked();
      expect(uxResearcherCheckbox).toBeChecked();
    });

    it('should toggle role assignment', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // Find unchecked role
      const engineerCheckbox = screen.getAllByRole('checkbox', { name: /Software Engineer/i })[0];
      await user.click(engineerCheckbox);
      
      expect(mockSetPhases).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: 'phase1',
            roles: ['Product Owner', 'UX Researcher', 'Software Engineer']
          })
        ])
      );
    });

    it('should remove role when unchecking', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // Uncheck existing role
      const productOwnerCheckbox = screen.getAllByRole('checkbox', { name: /Product Owner/i })[0];
      await user.click(productOwnerCheckbox);
      
      expect(mockSetPhases).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: 'phase1',
            roles: ['UX Researcher']
          })
        ])
      );
    });
  });

  describe('phase approval', () => {
    it('should toggle phase approval', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // Find approve button for first phase
      const approveButtons = screen.getAllByRole('button', { name: /Approve/i });
      await user.click(approveButtons[0]);
      
      expect(mockSetPhases).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: 'phase1',
            approved: true
          })
        ])
      );
    });

    it('should toggle approved phase to unapproved', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // Find approved button for second phase
      const approvedButton = screen.getByRole('button', { name: 'Approved' });
      await user.click(approvedButton);
      
      expect(mockSetPhases).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: 'phase2',
            approved: false
          })
        ])
      );
    });

    it('should stop propagation when clicking approve button', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      // Click approve button
      const approveButton = screen.getAllByRole('button', { name: /Approve/i })[0];
      await user.click(approveButton);
      
      // Phase should not toggle expansion
      expect(screen.getByText('User Research')).toBeInTheDocument();
    });
  });

  describe('issue display', () => {
    it('should display all issues for a phase', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      expect(screen.getByText('User Research')).toBeInTheDocument();
      expect(screen.getByText('Requirements Gathering')).toBeInTheDocument();
      expect(screen.getByText('Conduct user interviews')).toBeInTheDocument();
      expect(screen.getByText('Define project requirements')).toBeInTheDocument();
    });

    it('should show role badges with correct colors', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      const uxBadge = screen.getByText('UX Researcher').closest('.text-xs');
      expect(uxBadge).toHaveClass('bg-rose-100', 'text-rose-700');
      
      const poBadge = screen.getByText('Product Owner').closest('.text-xs');
      expect(poBadge).toHaveClass('bg-purple-100', 'text-purple-700');
    });

    it('should handle scrollable issue list', () => {
      const { container } = render(<LifecyclePhases {...defaultProps} />);
      
      const scrollableContainer = container.querySelector('.max-h-80.overflow-y-auto');
      expect(scrollableContainer).toBeInTheDocument();
    });
  });

  describe('navigation', () => {
    it('should call onPrevious when back button clicked', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      const backButton = screen.getByRole('button', { name: /Back to Summary/i });
      await user.click(backButton);
      
      expect(mockOnPrevious).toHaveBeenCalledTimes(1);
    });

    it('should enable next button when 50% phases approved', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      const nextButton = screen.getByRole('button', { name: /Review & Submit/i });
      expect(nextButton).not.toBeDisabled();
    });

    it('should disable next button when less than 50% approved', () => {
      const phasesWithNoApproval = mockPhases.map(p => ({ ...p, approved: false }));
      
      render(<LifecyclePhases {...defaultProps} phases={phasesWithNoApproval} />);
      
      const nextButton = screen.getByRole('button', { name: /Review & Submit/i });
      expect(nextButton).toBeDisabled();
    });

    it('should call onNext when next button clicked', async () => {
      const user = userEvent.setup();
      render(<LifecyclePhases {...defaultProps} />);
      
      const nextButton = screen.getByRole('button', { name: /Review & Submit/i });
      await user.click(nextButton);
      
      expect(mockOnNext).toHaveBeenCalledTimes(1);
    });
  });

  describe('styling', () => {
    it('should apply gradient to header', () => {
      const { container } = render(<LifecyclePhases {...defaultProps} />);
      
      const header = container.querySelector('.bg-gradient-to-r.from-indigo-600.to-purple-600');
      expect(header).toBeInTheDocument();
    });

    it('should apply hover effects to phase headers', () => {
      const { container } = render(<LifecyclePhases {...defaultProps} />);
      
      const phaseHeader = container.querySelector('.hover\\:bg-gray-50\\/50');
      expect(phaseHeader).toBeInTheDocument();
    });

    it('should show chevron icons for expansion state', () => {
      render(<LifecyclePhases {...defaultProps} />);
      
      // First phase is expanded by default
      const expandedPhase = screen.getByText('Discovery Phase').closest('.cursor-pointer');
      const chevronDown = expandedPhase?.querySelector('svg');
      expect(chevronDown).toBeInTheDocument();
    });
  });

  describe('edge cases', () => {
    it('should handle empty phases array', () => {
      render(<LifecyclePhases {...defaultProps} phases={[]} />);
      
      expect(screen.getByText('0/0')).toBeInTheDocument();
    });

    it('should handle phases with no issues', () => {
      const phaseWithNoIssues = [{
        ...mockPhases[0],
        issues: []
      }];
      
      render(<LifecyclePhases {...defaultProps} phases={phaseWithNoIssues} />);
      
      expect(screen.getByText('0 issues')).toBeInTheDocument();
    });

    it('should handle phases with no roles', () => {
      const phaseWithNoRoles = [{
        ...mockPhases[0],
        roles: []
      }];
      
      render(<LifecyclePhases {...defaultProps} phases={phaseWithNoRoles} />);
      
      expect(screen.getByText('0 roles')).toBeInTheDocument();
    });

    it('should handle unknown role colors', () => {
      const phaseWithUnknownRole = [{
        ...mockPhases[0],
        issues: [{
          title: 'Test Issue',
          description: 'Test',
          role: 'Unknown Role'
        }]
      }];
      
      render(<LifecyclePhases {...defaultProps} phases={phaseWithUnknownRole} />);
      
      const badge = screen.getByText('Unknown Role').closest('.text-xs');
      expect(badge).toHaveClass('bg-gray-100', 'text-gray-700');
    });
  });
});