
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { FileText, GitBranch, ArrowRight, Sparkles } from 'lucide-react';

interface ProjectSummaryProps {
  summary: {
    title: string;
    description: string;
    domain: string;
    repository: string;
    branch: string;
  };
  setSummary: (summary: any) => void;
  onNext: () => void;
}

const ProjectSummary = ({ summary, setSummary, onNext }: ProjectSummaryProps) => {
  const [isEditing, setIsEditing] = useState(false);

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
                  Detected from README.md
                </CardDescription>
              </div>
            </div>
            <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
              <Sparkles className="w-3 h-3 mr-1" />
              Auto-detected
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Repository
                </label>
                <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                  <GitBranch className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-700">{summary.repository}</span>
                  <Badge variant="outline" className="ml-auto">
                    {summary.branch}
                  </Badge>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Project Domain
                </label>
                <Select value={summary.domain} onValueChange={handleDomainChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select project type" />
                  </SelectTrigger>
                  <SelectContent>
                    {domains.map((domain) => (
                      <SelectItem key={domain} value={domain}>
                        {domain}
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

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">8</div>
            <div className="text-sm text-gray-600">Lifecycle Phases</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-indigo-600">9</div>
            <div className="text-sm text-gray-600">Agent Roles</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">~32</div>
            <div className="text-sm text-gray-600">Expected Issues</div>
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
