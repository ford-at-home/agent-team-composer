import { useState, useCallback, useMemo, memo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronRight, Users, FileText, ArrowLeft, ArrowRight, CheckCircle } from 'lucide-react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';
import { useAnnouncement, useFocusManagement } from '@/hooks/useAccessibility';

interface Phase {
  id: string;
  title: string;
  description: string;
  roles: string[];
  issues: Array<{
    title: string;
    description: string;
    role: string;
  }>;
  approved: boolean;
}

interface LifecyclePhasesProps {
  phases: Phase[];
  setPhases: (phases: Phase[]) => void;
  onNext: () => void;
  onPrevious: () => void;
}

// Memoized sub-components
const RoleCheckbox = memo(({ 
  phaseId, 
  role, 
  checked, 
  onChange 
}: { 
  phaseId: string; 
  role: string; 
  checked: boolean; 
  onChange: (phaseId: string, role: string) => void;
}) => (
  <div className="flex items-center space-x-2">
    <Checkbox
      id={`${phaseId}-${role}`}
      checked={checked}
      onCheckedChange={() => onChange(phaseId, role)}
      aria-label={`Assign ${role} to this phase`}
    />
    <label 
      htmlFor={`${phaseId}-${role}`}
      className="text-sm cursor-pointer hover:text-gray-900 select-none"
    >
      {role}
    </label>
  </div>
));

RoleCheckbox.displayName = 'RoleCheckbox';

const IssueCard = memo(({ issue }: { issue: Phase['issues'][0] }) => {
  const getRoleColor = (role: string) => {
    const colors: { [key: string]: string } = {
      'Product Owner': 'bg-purple-100 text-purple-700',
      'Software Engineer': 'bg-blue-100 text-blue-700',
      'AI Architect': 'bg-indigo-100 text-indigo-700',
      'DevOps Engineer': 'bg-orange-100 text-orange-700',
      'QA Engineer': 'bg-green-100 text-green-700',
      'Designer': 'bg-pink-100 text-pink-700',
      'UX Researcher': 'bg-rose-100 text-rose-700',
      'Data Scientist': 'bg-cyan-100 text-cyan-700',
      'Content Writer': 'bg-yellow-100 text-yellow-700'
    };
    return colors[role] || 'bg-gray-100 text-gray-700';
  };

  return (
    <Card className="border border-gray-200">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h5 className="font-medium text-gray-900 text-sm">
            {issue.title}
          </h5>
          <Badge 
            variant="secondary" 
            className={`text-xs ${getRoleColor(issue.role)}`}
          >
            {issue.role}
          </Badge>
        </div>
        <p className="text-xs text-gray-600 leading-relaxed">
          {issue.description}
        </p>
      </CardContent>
    </Card>
  );
});

IssueCard.displayName = 'IssueCard';

// Virtual scrolling for large issue lists
const VirtualizedIssueList = memo(({ issues }: { issues: Phase['issues'] }) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: issues.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
    overscan: 5
  });

  return (
    <div 
      ref={parentRef} 
      className="space-y-3 max-h-80 overflow-y-auto"
      role="list"
      aria-label="Generated issues for this phase"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
            role="listitem"
          >
            <IssueCard issue={issues[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
});

VirtualizedIssueList.displayName = 'VirtualizedIssueList';

const LifecyclePhasesOptimized = memo(({ 
  phases, 
  setPhases, 
  onNext, 
  onPrevious 
}: LifecyclePhasesProps) => {
  const [openPhases, setOpenPhases] = useState<Set<string>>(
    new Set([phases[0]?.id])
  );
  const { announce, AnnouncementRegion } = useAnnouncement();
  const { focusedIndex, setFocusedIndex, handleKeyDown, setItemRef } = useFocusManagement(
    phases.length,
    {
      orientation: 'vertical',
      onItemSelect: (index) => {
        const phaseId = phases[index].id;
        togglePhase(phaseId);
      }
    }
  );

  const allRoles = useMemo(() => [
    'Product Owner',
    'Software Engineer',
    'AI Architect',
    'DevOps Engineer',
    'QA Engineer',
    'Designer',
    'UX Researcher',
    'Data Scientist',
    'Content Writer'
  ], []);

  // Memoized statistics
  const statistics = useMemo(() => {
    const approvedPhases = phases.filter(p => p.approved);
    const totalIssues = phases.reduce((acc, phase) => acc + phase.issues.length, 0);
    const canProceed = approvedPhases.length >= Math.ceil(phases.length * 0.5);

    return {
      approvedCount: approvedPhases.length,
      totalIssues,
      canProceed
    };
  }, [phases]);

  const togglePhase = useCallback((phaseId: string) => {
    setOpenPhases(prev => {
      const newSet = new Set(prev);
      if (newSet.has(phaseId)) {
        newSet.delete(phaseId);
      } else {
        newSet.add(phaseId);
      }
      return newSet;
    });
  }, []);

  const toggleRole = useCallback((phaseId: string, role: string) => {
    setPhases(phases.map(phase => {
      if (phase.id === phaseId) {
        const newRoles = phase.roles.includes(role)
          ? phase.roles.filter(r => r !== role)
          : [...phase.roles, role];
        return { ...phase, roles: newRoles };
      }
      return phase;
    }));
  }, [phases, setPhases]);

  const toggleApproval = useCallback((phaseId: string) => {
    const phase = phases.find(p => p.id === phaseId);
    if (!phase) return;

    const newApprovalState = !phase.approved;
    
    setPhases(phases.map(p => {
      if (p.id === phaseId) {
        return { ...p, approved: newApprovalState };
      }
      return p;
    }));

    announce(
      `Phase "${phase.title}" ${newApprovalState ? 'approved' : 'unapproved'}. ${
        newApprovalState 
          ? `${statistics.approvedCount + 1} of ${phases.length} phases now approved.`
          : `${statistics.approvedCount - 1} of ${phases.length} phases now approved.`
      }`,
      { priority: 'polite' }
    );
  }, [phases, setPhases, announce, statistics.approvedCount]);

  const handleNextClick = useCallback(() => {
    if (statistics.canProceed) {
      onNext();
    } else {
      announce(
        `Please approve at least ${Math.ceil(phases.length * 0.5)} phases before proceeding.`,
        { priority: 'assertive' }
      );
    }
  }, [statistics.canProceed, onNext, phases.length, announce]);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <AnnouncementRegion />
      
      {/* Progress Header */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl">Configure Lifecycle Phases</CardTitle>
              <CardDescription className="text-indigo-100">
                Assign roles and review generated issues for each phase
              </CardDescription>
            </div>
            <div className="text-right" aria-live="polite">
              <div className="text-2xl font-bold">{statistics.approvedCount}/{phases.length}</div>
              <div className="text-sm text-indigo-100">Phases Approved</div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Phases */}
      <div 
        className="space-y-4" 
        role="list"
        aria-label="Lifecycle phases"
        onKeyDown={handleKeyDown}
      >
        {phases.map((phase, index) => (
          <Card 
            key={phase.id} 
            ref={(el) => setItemRef(index, el)}
            tabIndex={focusedIndex === index ? 0 : -1}
            className={`transition-all duration-200 ${
              phase.approved 
                ? 'border-green-200 bg-green-50/30' 
                : 'border-gray-200 hover:border-gray-300'
            } ${focusedIndex === index ? 'ring-2 ring-blue-500' : ''}`}
            role="listitem"
            aria-label={`Phase ${index + 1}: ${phase.title}, ${phase.approved ? 'approved' : 'not approved'}`}
          >
            <Collapsible 
              open={openPhases.has(phase.id)}
              onOpenChange={() => togglePhase(phase.id)}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-gray-50/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        {openPhases.has(phase.id) ? (
                          <ChevronDown className="w-5 h-5 text-gray-400" aria-hidden="true" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-gray-400" aria-hidden="true" />
                        )}
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                          phase.approved 
                            ? 'bg-green-600 text-white' 
                            : 'bg-gray-200 text-gray-600'
                        }`}>
                          {phase.approved ? <CheckCircle className="w-4 h-4" /> : index + 1}
                        </div>
                      </div>
                      <div>
                        <CardTitle className="text-lg">{phase.title}</CardTitle>
                        <CardDescription>{phase.description}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4 text-gray-400" aria-hidden="true" />
                        <span className="text-sm text-gray-600">{phase.roles.length} roles</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-gray-400" aria-hidden="true" />
                        <span className="text-sm text-gray-600">{phase.issues.length} issues</span>
                      </div>
                      <Button
                        variant={phase.approved ? "default" : "outline"}
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleApproval(phase.id);
                        }}
                        className={phase.approved ? "bg-green-600 hover:bg-green-700" : ""}
                        aria-label={`${phase.approved ? 'Unapprove' : 'Approve'} ${phase.title}`}
                      >
                        {phase.approved ? "Approved" : "Approve"}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <CardContent className="pt-0">
                  <div className="grid lg:grid-cols-3 gap-6">
                    {/* Role Assignment */}
                    <div className="lg:col-span-1">
                      <h4 className="font-semibold text-gray-900 mb-3">Assigned Roles</h4>
                      <div className="space-y-2" role="group" aria-label="Select roles for this phase">
                        {allRoles.map(role => (
                          <RoleCheckbox
                            key={role}
                            phaseId={phase.id}
                            role={role}
                            checked={phase.roles.includes(role)}
                            onChange={toggleRole}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Generated Issues */}
                    <div className="lg:col-span-2">
                      <h4 className="font-semibold text-gray-900 mb-3">
                        Generated Issues ({phase.issues.length})
                      </h4>
                      {phase.issues.length > 10 ? (
                        <VirtualizedIssueList issues={phase.issues} />
                      ) : (
                        <div className="space-y-3 max-h-80 overflow-y-auto" role="list">
                          {phase.issues.map((issue, issueIndex) => (
                            <div key={issueIndex} role="listitem">
                              <IssueCard issue={issue} />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        ))}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onPrevious}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Summary
        </Button>
        <Button 
          onClick={handleNextClick}
          disabled={!statistics.canProceed}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
          aria-label={
            statistics.canProceed
              ? 'Continue to review and submit'
              : `Approve at least ${Math.ceil(phases.length * 0.5)} phases to continue`
          }
        >
          Review & Submit
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
});

LifecyclePhasesOptimized.displayName = 'LifecyclePhasesOptimized';

export default LifecyclePhasesOptimized;