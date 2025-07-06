
import { useState, useEffect } from 'react';
import { Github, Users, GitBranch, CheckCircle2, FileText, Settings, Zap, Loader2, Edit3, FolderOpen } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import ParseProduct from '@/components/ParseProduct';
import ProjectSummary from '@/components/ProjectSummary';
import LifecyclePhases from '@/components/LifecyclePhases';
import EpicIssueView from '@/components/EpicIssueView';
import ReviewSubmit from '@/components/ReviewSubmit';
import { useProjectData } from '@/hooks/useProjectData';
import { ProjectSummary as ProjectSummaryType, Phase } from '@/types';

const Index = () => {
  const { projectData, loading, error, updateProjectData, createGitHubIssues } = useProjectData();
  const [currentStep, setCurrentStep] = useState(0);
  const [projectSummary, setProjectSummary] = useState<ProjectSummaryType | null>(null);
  const [phases, setPhases] = useState<Phase[]>([]);
  const [readmeContent, setReadmeContent] = useState<string>('');
  const [parsedMetadata, setParsedMetadata] = useState<any>(null);

  useEffect(() => {
    if (projectData) {
      setProjectSummary(projectData.summary);
      setPhases(projectData.phases);
      // Extract metadata for ParseProduct step
      if (projectData.summary) {
        setParsedMetadata({
          title: projectData.summary.title,
          description: projectData.summary.description,
          domain: projectData.summary.domain,
          targetUsers: ['developers'], // TODO: Get from projectData
          techStack: [], // TODO: Get from projectData
          features: [], // TODO: Get from projectData
          complexity: 'moderate'
        });
      }
    }
    // TODO: Load README content
    fetchReadmeContent();
  }, [projectData]);

  const fetchReadmeContent = async () => {
    try {
      const response = await fetch('/README.md');
      if (response.ok) {
        const content = await response.text();
        setReadmeContent(content);
      }
    } catch (error) {
      console.error('Failed to load README:', error);
    }
  };

  const steps = [
    { id: 0, title: 'Parse Product', icon: FileText },
    { id: 1, title: 'Sprint View', icon: GitBranch },
    { id: 2, title: 'Epic View', icon: FolderOpen },
    { id: 3, title: 'Issues View', icon: Edit3 },
    { id: 4, title: 'GitHub Sync', icon: CheckCircle2 }
  ];

  const handleNext = async () => {
    if (currentStep < steps.length - 1) {
      // Save current data before moving to next step
      if (projectSummary && phases.length > 0) {
        await updateProjectData({ summary: projectSummary, phases });
      }
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

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
            <p className="text-gray-600 text-center text-sm">Please ensure the CLI tool is running</p>
          </CardContent>
        </Card>
      );
    }

    if (!projectSummary || phases.length === 0) {
      return (
        <Card className="max-w-md mx-auto">
          <CardContent className="py-12">
            <p className="text-gray-600 text-center">No project data available</p>
          </CardContent>
        </Card>
      );
    }

    switch (currentStep) {
      case 0:
        return (
          <ParseProduct
            readmeContent={readmeContent}
            initialData={parsedMetadata}
            onNext={(data) => {
              setParsedMetadata(data);
              // Update project summary with parsed data
              if (projectSummary) {
                setProjectSummary({
                  ...projectSummary,
                  title: data.title,
                  description: data.description,
                  domain: data.domain
                });
              }
              handleNext();
            }}
          />
        );
      case 1:
        return (
          <ProjectSummary 
            summary={projectSummary}
            setSummary={setProjectSummary}
            onNext={handleNext}
          />
        );
      case 2:
        return (
          <LifecyclePhases 
            phases={phases}
            setPhases={setPhases}
            onNext={handleNext}
            onPrevious={handlePrevious}
          />
        );
      case 3:
        return (
          <EpicIssueView
            phases={phases}
            setPhases={setPhases}
            onNext={handleNext}
            onPrevious={handlePrevious}
          />
        );
      case 4:
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
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
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <Github className="w-3 h-3 mr-1" />
                Connected
              </Badge>
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                <Users className="w-3 h-3 mr-1" />
                8 Roles Active
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="container mx-auto px-6 py-6">
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center">
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
                  {index < steps.length - 1 && (
                    <div className={`w-20 h-0.5 mx-6 transition-all duration-300 ${
                      currentStep > index ? 'bg-blue-600' : 'bg-gray-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Step Content */}
        <div className="transition-all duration-300">
          {renderStepContent()}
        </div>
      </div>
    </div>
  );
};

export default Index;
