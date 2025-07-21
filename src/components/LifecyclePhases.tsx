
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronRight, Users, FileText, ArrowLeft, ArrowRight, CheckCircle, Github, Loader2, Milestone } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';

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
  repository?: string;
}

const LifecyclePhases = ({ phases, setPhases, onNext, onPrevious, repository }: LifecyclePhasesProps) => {
  const [openPhases, setOpenPhases] = useState<string[]>([phases[0]?.id]);
  const [isCreatingMilestones, setIsCreatingMilestones] = useState(false);
  const [milestonesCreated, setMilestonesCreated] = useState(false);
  const [milestoneMap, setMilestoneMap] = useState<Map<string, number>>(new Map());
  const [repositories, setRepositories] = useState<{ name: string; full_name: string; }[]>([]);
  const [selectedRepository, setSelectedRepository] = useState<string>('');
  const [milestoneCreationProgress, setMilestoneCreationProgress] = useState<{ current: number; total: number; status: string } | null>(null);
  const { toast } = useToast();

  // Load repositories on component mount
  useEffect(() => {
    loadRepositories();
  }, []);

  // Load GitHub repositories
  const loadRepositories = async () => {
    try {
      const response = await fetch('/api/github/repositories');
      if (response.ok) {
        const repos = await response.json();
        setRepositories(repos);
      }
    } catch (error) {
      console.error('Failed to load repositories:', error);
    }
  };

  const allRoles = [
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

  const togglePhase = (phaseId: string) => {
    setOpenPhases(prev => 
      prev.includes(phaseId) 
        ? prev.filter(id => id !== phaseId)
        : [...prev, phaseId]
    );
  };

  const toggleRole = (phaseId: string, role: string) => {
    setPhases(phases.map(phase => {
      if (phase.id === phaseId) {
        const newRoles = phase.roles.includes(role)
          ? phase.roles.filter(r => r !== role)
          : [...phase.roles, role];
        return { ...phase, roles: newRoles };
      }
      return phase;
    }));
  };

  const toggleApproval = (phaseId: string) => {
    setPhases(phases.map(phase => {
      if (phase.id === phaseId) {
        return { ...phase, approved: !phase.approved };
      }
      return phase;
    }));
  };

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

  const approvedCount = phases.filter(p => p.approved).length;
  const canProceed = approvedCount >= Math.ceil(phases.length * 0.5); // At least 50% approved

  const handleCreateMilestones = async () => {
    if (!selectedRepository) {
      toast({
        title: "Repository not selected",
        description: "Please select a repository first",
        variant: "destructive",
      });
      return;
    }

    setIsCreatingMilestones(true);
    setMilestoneCreationProgress({ current: 0, total: 3, status: 'Preparing milestone creation...' });
    
    try {
      setMilestoneCreationProgress({ current: 1, total: 3, status: 'Creating GitHub milestones...' });
      
      // Use server API endpoint instead of direct GitHub service
      const response = await fetch('/api/github/create-milestones-and-issues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repository: selectedRepository,
          phases: phases.filter(p => p.approved)
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.details || errorData.error || 'Failed to create milestones');
      }
      
      const result = await response.json();
      
      setMilestoneCreationProgress({ current: 2, total: 3, status: 'Processing results...' });
      
      // Store milestone numbers for later use
      const newMap = new Map<string, number>();
      result.milestones.forEach((milestone: { phase: string; milestoneNumber: number }) => {
        newMap.set(milestone.phase, milestone.milestoneNumber);
      });
      setMilestoneMap(newMap);
      setMilestonesCreated(true);
      
      setMilestoneCreationProgress({ current: 3, total: 3, status: 'Milestones created successfully!' });
      
      toast({
        title: "Milestones created successfully!",
        description: `Created ${result.milestones.length} milestones in GitHub`,
      });
      
      // Move to next step after successful creation
      setTimeout(() => {
        onNext();
      }, 1000);
      
    } catch (error) {
      toast({
        title: "Failed to create milestones",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setTimeout(() => {
        setIsCreatingMilestones(false);
        setMilestoneCreationProgress(null);
      }, 2000);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 relative">
      {/* Milestone Creation Loading Overlay */}
      {isCreatingMilestones && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center">
          <Card className="max-w-lg mx-auto">
            <CardContent className="flex flex-col items-center justify-center py-12 px-8">
              <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mb-4" />
              <h3 className="text-lg font-semibold mb-2">Creating GitHub Milestones</h3>
              <p className="text-gray-600 text-center mb-6">
                Creating project milestones in your GitHub repository...
              </p>
              
              {milestoneCreationProgress && (
                <div className="w-full space-y-2">
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{milestoneCreationProgress.status}</span>
                    <span>{milestoneCreationProgress.current} / {milestoneCreationProgress.total}</span>
                  </div>
                  <Progress 
                    value={(milestoneCreationProgress.current / milestoneCreationProgress.total) * 100}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

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
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-2xl font-bold">{approvedCount}/{phases.length}</div>
                <div className="text-sm text-indigo-100">Phases Approved</div>
              </div>
              {repository && approvedCount > 0 && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleCreateMilestones}
                  disabled={isCreatingMilestones || milestonesCreated}
                  className="bg-white/20 hover:bg-white/30 text-white border-white/30"
                >
                  {isCreatingMilestones ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : milestonesCreated ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Milestones Created
                    </>
                  ) : (
                    <>
                      <Milestone className="w-4 h-4 mr-2" />
                      Create GitHub Milestones
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Repository Selection */}
      {approvedCount > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">GitHub Repository</CardTitle>
            <CardDescription>Select the repository where milestones will be created</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="repository-select">Repository</Label>
                <Select value={selectedRepository} onValueChange={setSelectedRepository}>
                  <SelectTrigger id="repository-select" className="mt-1">
                    <SelectValue placeholder="Select a repository" />
                  </SelectTrigger>
                  <SelectContent>
                    {repositories.map(repo => (
                      <SelectItem key={repo.full_name} value={repo.full_name}>
                        {repo.full_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {selectedRepository && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <p className="text-sm text-indigo-800">
                    <strong>Selected:</strong> {selectedRepository}
                  </p>
                  <p className="text-xs text-indigo-600 mt-1">
                    GitHub milestones will be created in this repository for each approved phase
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Phases */}
      <div className="space-y-4">
        {phases.map((phase, index) => (
          <Card key={phase.id} className={`transition-all duration-200 ${
            phase.approved 
              ? 'border-green-200 bg-green-50/30' 
              : 'border-gray-200 hover:border-gray-300'
          }`}>
            <Collapsible 
              open={openPhases.includes(phase.id)}
              onOpenChange={() => togglePhase(phase.id)}
            >
              <CollapsibleTrigger asChild>
                <CardHeader className="cursor-pointer hover:bg-gray-50/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        {openPhases.includes(phase.id) ? (
                          <ChevronDown className="w-5 h-5 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-gray-400" />
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
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">{phase.roles.length} roles</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-gray-400" />
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
                      <div className="space-y-2">
                        {allRoles.map(role => (
                          <div key={role} className="flex items-center space-x-2">
                            <Checkbox
                              id={`${phase.id}-${role}`}
                              checked={phase.roles.includes(role)}
                              onCheckedChange={() => toggleRole(phase.id, role)}
                            />
                            <label 
                              htmlFor={`${phase.id}-${role}`}
                              className="text-sm cursor-pointer hover:text-gray-900"
                            >
                              {role}
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Generated Issues */}
                    <div className="lg:col-span-2">
                      <h4 className="font-semibold text-gray-900 mb-3">Generated Issues</h4>
                      <div className="space-y-3 max-h-80 overflow-y-auto">
                        {phase.issues.map((issue, issueIndex) => (
                          <Card key={issueIndex} className="border border-gray-200">
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
                        ))}
                      </div>
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
          onClick={handleCreateMilestones}
          disabled={!canProceed || !selectedRepository || isCreatingMilestones}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
        >
          {isCreatingMilestones ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Creating Milestones...
            </>
          ) : (
            <>
              Create Milestones & Continue
              <ArrowRight className="w-4 h-4 ml-2" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default LifecyclePhases;
