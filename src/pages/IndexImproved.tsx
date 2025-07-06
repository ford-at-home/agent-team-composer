import { useState, useEffect, useCallback, useMemo, Suspense, lazy } from 'react';
import { Github, Users, GitBranch, CheckCircle2, FileText, Settings, Zap, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useProjectData } from '@/hooks/useProjectData';
import { useAutoSave } from '@/hooks/useAutoSave';
import { useAnnouncement, useSkipLinks } from '@/hooks/useAccessibility';
import ErrorBoundary from '@/components/ErrorBoundary';
import { ProjectSummary as ProjectSummaryType, Phase } from '@/types';

// Lazy load heavy components
const ProjectSummary = lazy(() => import('@/components/ProjectSummary'));
const LifecyclePhases = lazy(() => import('@/components/LifecyclePhases'));
const ReviewSubmit = lazy(() => import('@/components/ReviewSubmit'));

// Loading component
const StepLoader = () => (
  <Card className="max-w-md mx-auto">
    <CardContent className="flex flex-col items-center justify-center py-12">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-4" />
      <p className="text-gray-600">Loading component...</p>
    </CardContent>
  </Card>
);

const IndexImproved = () => {
  const { projectData, loading, error, updateProjectData, createGitHubIssues, refetch } = useProjectData();
  const [currentStep, setCurrentStep] = useState(0);
  const [projectSummary, setProjectSummary] = useState<ProjectSummaryType | null>(null);
  const [phases, setPhases] = useState<Phase[]>([]);
  const { announce, AnnouncementRegion } = useAnnouncement();
  const { SkipLinks } = useSkipLinks();

  // Initialize state from projectData
  useEffect(() => {
    if (projectData && !projectSummary && phases.length === 0) {
      setProjectSummary(projectData.summary);
      setPhases(projectData.phases);
    }
  }, [projectData, projectSummary, phases.length]);

  // Auto-save functionality
  const saveProjectData = useCallback(async (data: { summary: ProjectSummaryType | null; phases: Phase[] }) => {
    if (data.summary && data.phases.length > 0) {
      await updateProjectData({ summary: data.summary, phases: data.phases });
    }
  }, [updateProjectData]);

  const { SaveIndicator, hasUnsavedChanges } = useAutoSave(
    'agent-team-composer-draft',
    { summary: projectSummary, phases },
    saveProjectData,
    {
      delay: 3000,
      onSaveSuccess: () => announce('Changes saved', { priority: 'polite' }),
      onSaveError: () => announce('Failed to save changes', { priority: 'assertive' })
    }
  );

  const steps = useMemo(() => [
    { id: 0, title: 'Project Summary', icon: FileText },
    { id: 1, title: 'Lifecycle Phases', icon: GitBranch },
    { id: 2, title: 'Review & Submit', icon: CheckCircle2 }
  ], []);

  // Memoized callbacks
  const handleNext = useCallback(async () => {
    if (currentStep < steps.length - 1) {
      // Save current data before moving to next step
      if (projectSummary && phases.length > 0) {
        await updateProjectData({ summary: projectSummary, phases });
      }
      const nextStep = currentStep + 1;
      setCurrentStep(nextStep);
      announce(`Navigated to step ${nextStep + 1}: ${steps[nextStep].title}`, { priority: 'polite' });
    }
  }, [currentStep, steps, projectSummary, phases, updateProjectData, announce]);

  const handlePrevious = useCallback(() => {
    if (currentStep > 0) {
      const prevStep = currentStep - 1;
      setCurrentStep(prevStep);
      announce(`Navigated back to step ${prevStep + 1}: ${steps[prevStep].title}`, { priority: 'polite' });
    }
  }, [currentStep, steps, announce]);

  // Memoized project summary setter with validation
  const setValidatedProjectSummary = useCallback((
    updater: ProjectSummaryType | ((prev: ProjectSummaryType | null) => ProjectSummaryType | null)
  ) => {
    setProjectSummary(prev => {
      const newValue = typeof updater === 'function' ? updater(prev) : updater;
      if (newValue && !newValue.title) {
        console.error('Project summary must have a title');
        return prev;
      }
      return newValue;
    });
  }, []);

  // Handle window close with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges()) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  const renderStepContent = () => {
    if (loading) {
      return (
        <Card className="max-w-md mx-auto">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-4" />
            <p className="text-gray-600">Loading project data...</p>
          </CardContent>
        </Card>
      );
    }

    if (error) {
      return (
        <Card className="max-w-md mx-auto border-red-200">
          <CardContent className="py-12">
            <p className="text-red-600 text-center mb-4">Error: {error}</p>
            <p className="text-gray-600 text-center text-sm mb-4">
              Please ensure the CLI tool is running
            </p>
            <div className="flex justify-center">
              <Button onClick={() => refetch()} variant="outline">
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      );
    }

    if (!projectSummary || phases.length === 0) {
      return (
        <Card className="max-w-md mx-auto">
          <CardContent className="py-12">
            <p className="text-gray-600 text-center mb-4">No project data available</p>
            <div className="flex justify-center">
              <Button onClick={() => refetch()} variant="outline">
                Reload Data
              </Button>
            </div>
          </CardContent>
        </Card>
      );
    }

    switch (currentStep) {
      case 0:
        return (
          <ProjectSummary 
            summary={projectSummary}
            setSummary={setValidatedProjectSummary}
            onNext={handleNext}
          />
        );
      case 1:
        return (
          <LifecyclePhases 
            phases={phases}
            setPhases={setPhases}
            onNext={handleNext}
            onPrevious={handlePrevious}
          />
        );
      case 2:
        return (
          <ReviewSubmit 
            summary={projectSummary}
            phases={phases}
            onPrevious={handlePrevious}
            onSubmit={createGitHubIssues}
          />
        );
      default:
        return null;
    }
  };

  // Calculate statistics
  const statistics = useMemo(() => {
    const approvedPhases = phases.filter(p => p.approved);
    const allRoles = [...new Set(phases.flatMap(p => p.roles))];
    const totalIssues = phases.reduce((acc, phase) => acc + phase.issues.length, 0);
    
    return {
      phasesCount: phases.length,
      rolesCount: allRoles.length,
      issuesCount: totalIssues,
      approvedCount: approvedPhases.length
    };
  }, [phases]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <SkipLinks />
      <AnnouncementRegion />
      
      {/* Header */}
      <header 
        className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50"
        role="banner"
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Agent Team Composer</h1>
                <p className="text-sm text-gray-500">Claude Flow SPARC Optimized</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <SaveIndicator />
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <Github className="w-3 h-3 mr-1" />
                <span className="sr-only">GitHub status:</span>
                Connected
              </Badge>
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                <Users className="w-3 h-3 mr-1" />
                <span className="sr-only">Active roles:</span>
                {statistics.rolesCount} Roles Active
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main id="main-content" className="container mx-auto px-6 py-6">
        {/* Progress Steps */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <nav aria-label="Progress steps" role="navigation">
              <ol className="flex items-center justify-between" role="list">
                {steps.map((step, index) => (
                  <li key={step.id} role="listitem" className="flex items-center">
                    <button
                      className={`flex items-center focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg p-2 ${
                        currentStep === index ? 'cursor-default' : 'cursor-pointer hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        if (index < currentStep) {
                          setCurrentStep(index);
                          announce(`Jumped to step ${index + 1}: ${step.title}`, { priority: 'polite' });
                        }
                      }}
                      disabled={index > currentStep || currentStep === index}
                      aria-current={currentStep === index ? 'step' : undefined}
                      aria-label={`Step ${index + 1}: ${step.title}, ${
                        currentStep > index ? 'completed' : 
                        currentStep === index ? 'current' : 'upcoming'
                      }`}
                    >
                      <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-300 ${
                        currentStep >= index 
                          ? 'bg-blue-600 border-blue-600 text-white' 
                          : 'border-gray-300 text-gray-400'
                      }`}>
                        <step.icon className="w-5 h-5" />
                      </div>
                      <div className="ml-3">
                        <p className={`text-sm font-medium ${
                          currentStep >= index ? 'text-blue-600' : 'text-gray-400'
                        }`}>
                          Step {index + 1}
                        </p>
                        <p className={`text-xs ${
                          currentStep >= index ? 'text-gray-700' : 'text-gray-400'
                        }`}>
                          {step.title}
                        </p>
                      </div>
                    </button>
                    {index < steps.length - 1 && (
                      <div 
                        className={`w-20 h-0.5 mx-6 transition-all duration-300 ${
                          currentStep > index ? 'bg-blue-600' : 'bg-gray-300'
                        }`} 
                        aria-hidden="true"
                      />
                    )}
                  </li>
                ))}
              </ol>
            </nav>
          </CardContent>
        </Card>

        {/* Step Content */}
        <div className="transition-all duration-300">
          <ErrorBoundary>
            <Suspense fallback={<StepLoader />}>
              {renderStepContent()}
            </Suspense>
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
};

export default IndexImproved;