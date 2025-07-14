
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { FileText, GitBranch, ArrowRight, Sparkles, Users, Code, Zap, Target } from 'lucide-react';
import { ProjectSummary as ProjectSummaryType } from '@/types';

interface ProjectSummaryProps {
  summary: ProjectSummaryType | null;
  setSummary: (summary: ProjectSummaryType) => void;
  onNext: () => void;
}

const ProjectSummary = ({ summary, setSummary, onNext }: ProjectSummaryProps) => {
  const [isEditing, setIsEditing] = useState(false);
  
  if (!summary) {
    return (
      <Card className="max-w-md mx-auto">
        <CardContent className="py-12 text-center">
          <p className="text-gray-600">No project summary available</p>
          <p className="text-sm text-gray-500 mt-2">Debug: This is ProjectSummary component (Step 1)</p>
          <p className="text-sm text-gray-500">You should be seeing ParseProduct (Step 0)</p>
        </CardContent>
      </Card>
    );
  }

  const domainLabels: Record<string, string> = {
    'e-commerce': 'E-commerce',
    'social-media': 'Social Media',
    'productivity': 'Productivity',
    'healthcare': 'Healthcare',
    'education': 'Education',
    'finance': 'Finance',
    'entertainment': 'Entertainment',
    'devtools': 'Developer Tools',
    'iot': 'IoT',
    'general': 'General'
  };
  
  const complexityColors = {
    simple: 'bg-green-100 text-green-700',
    moderate: 'bg-yellow-100 text-yellow-700',
    complex: 'bg-red-100 text-red-700'
  };

  const handleDescriptionChange = (value: string) => {
    setSummary({
      ...summary,
      description: value
    });
  };

  const handleDomainChange = (value: string) => {
    setSummary({
      ...summary,
      domain: value
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Project Info Card */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-6 h-6" />
              <div>
                <CardTitle className="text-xl">{summary.title}</CardTitle>
                <CardDescription className="text-blue-100">
                  {domainLabels[summary.domain] || summary.domain}
                </CardDescription>
              </div>
            </div>
            {summary.complexity && (
              <Badge className={`${complexityColors[summary.complexity]} border-0`}>
                {summary.complexity.charAt(0).toUpperCase() + summary.complexity.slice(1)}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {summary.repository && (
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Repository
                  </label>
                  <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                    <GitBranch className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-700">{summary.repository}</span>
                    {summary.branch && (
                      <Badge variant="outline" className="ml-auto">
                        {summary.branch}
                      </Badge>
                    )}
                  </div>
                </div>
              )}
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Project Domain
                </label>
                <Select value={summary.domain} onValueChange={handleDomainChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select project type" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(domainLabels).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">
                  Project Description
                </label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsEditing(!isEditing)}
                >
                  {isEditing ? 'Preview' : 'Edit'}
                </Button>
              </div>
              
              {isEditing ? (
                <Textarea
                  value={summary.description}
                  onChange={(e) => handleDescriptionChange(e.target.value)}
                  placeholder="Describe your project goals and requirements..."
                  className="min-h-[120px] resize-none"
                />
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg min-h-[120px] text-sm text-gray-700 leading-relaxed">
                  {summary.description || 'No description provided'}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Additional Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Target Users */}
        {summary.targetUsers && summary.targetUsers.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center">
                <Users className="w-4 h-4 mr-2" />
                Target Users
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {summary.targetUsers.map((user, index) => (
                  <Badge key={index} variant="secondary">
                    {user}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tech Stack */}
        {summary.techStack && summary.techStack.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center">
                <Code className="w-4 h-4 mr-2" />
                Tech Stack
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {summary.techStack.map((tech, index) => (
                  <Badge key={index} variant="outline">
                    {tech}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Key Features */}
        {summary.features && summary.features.length > 0 && (
          <Card className="md:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center">
                <Zap className="w-4 h-4 mr-2" />
                Key Features
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {summary.features.map((feature, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <Target className="w-3 h-3 text-blue-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {summary.targetUsers?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Target User Groups</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-indigo-600">
              {summary.techStack?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Technologies</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">
              {summary.features?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Key Features</div>
          </CardContent>
        </Card>
      </div>

      {/* Continue Button */}
      <div className="flex justify-end">
        <Button onClick={onNext} size="lg" className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700">
          Configure Phases
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
};

export default ProjectSummary;
