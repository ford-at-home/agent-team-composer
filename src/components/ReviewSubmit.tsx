
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, Github, CheckCircle2, Users, FileText, GitBranch, Zap, Loader2, AlertCircle, RefreshCw, Milestone } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { GitHubService } from '@/services/github-service';

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

interface ReviewSubmitProps {
  summary: {
    title: string;
    description: string;
    domain: string;
    repository: string;
    branch: string;
  };
  phases: Phase[];
  onPrevious: () => void;
  onSubmit?: (phases: Phase[], milestoneMap?: Map<string, number>) => Promise<unknown>;
}

const ReviewSubmit = ({ summary, phases, onPrevious, onSubmit }: ReviewSubmitProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState(summary.repository || '');
  const [selectedBranch, setSelectedBranch] = useState(summary.branch || 'main');
  const [newBranchName, setNewBranchName] = useState('');
  const [createNewBranch, setCreateNewBranch] = useState(false);
  const [repositories, setRepositories] = useState<Array<{ full_name: string; permissions: { push?: boolean; admin?: boolean } }>>([]);
  const [branches, setBranches] = useState<string[]>(['main']);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [loadingBranches, setLoadingBranches] = useState(false);
  const [repoError, setRepoError] = useState<string | null>(null);
  const [milestoneMap, setMilestoneMap] = useState<Map<string, number>>(new Map());
  const [creatingMilestones, setCreatingMilestones] = useState(false);
  const { toast } = useToast();

  const approvedPhases = phases.filter(p => p.approved);
  const totalIssues = approvedPhases.reduce((acc, phase) => acc + phase.issues.length, 0);
  const allRoles = [...new Set(approvedPhases.flatMap(p => p.roles))];

  // Fetch user repositories
  useEffect(() => {
    fetchRepositories();
  }, []);

  // Fetch branches when repo changes
  useEffect(() => {
    if (selectedRepo) {
      fetchBranches(selectedRepo);
    }
  }, [selectedRepo]);

  const fetchRepositories = async () => {
    setLoadingRepos(true);
    setRepoError(null);
    
    try {
      const apiUrl = import.meta.env.DEV ? 'http://localhost:3000/api/github/repositories' : '/api/github/repositories';
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch repositories');
      }
      
      const data = await response.json();
      const repoList = Array.isArray(data) ? data : [];
      setRepositories(repoList.filter((repo: { permissions?: { push?: boolean; admin?: boolean } }) => 
        repo.permissions && (repo.permissions.push || repo.permissions.admin)
      ));
    } catch (error) {
      setRepoError('Failed to load repositories. Please check your GitHub authentication.');
      console.error('Error fetching repositories:', error);
    } finally {
      setLoadingRepos(false);
    }
  };

  const fetchBranches = async (repoFullName: string) => {
    setLoadingBranches(true);
    
    try {
      const apiUrl = import.meta.env.DEV 
        ? `http://localhost:3000/api/github/branches?repo=${encodeURIComponent(repoFullName)}`
        : `/api/github/branches?repo=${encodeURIComponent(repoFullName)}`;
      const response = await fetch(apiUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch branches');
      }
      
      const data = await response.json();
      setBranches(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching branches:', error);
      setBranches(['main']); // Fallback to main
    } finally {
      setLoadingBranches(false);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setCreatingMilestones(true);
    
    const targetBranch = createNewBranch ? newBranchName : selectedBranch;
    const targetRepo = selectedRepo || summary.repository;
    
    if (!targetRepo) {
      toast({
        title: "Repository required",
        description: "Please select a repository",
        variant: "destructive",
      });
      setIsSubmitting(false);
      return;
    }
    
    try {
      // Step 1: Create milestones
      const githubService = new GitHubService();
      const milestoneResults = await githubService.createMilestones(targetRepo, phases);
      
      // Store milestone numbers for issue creation
      const newMilestoneMap = new Map<string, number>();
      milestoneResults.forEach(result => {
        newMilestoneMap.set(result.phase, result.milestoneNumber);
      });
      setMilestoneMap(newMilestoneMap);
      setCreatingMilestones(false);
      
      toast({
        title: "Milestones created!",
        description: `Created ${milestoneResults.length} milestones in GitHub`,
      });
      
      // Step 2: Create issues with milestone associations
      const issueResults = await githubService.createIssuesFromPhases(targetRepo, phases, newMilestoneMap);
      
      setSubmitted(true);
      
      toast({
        title: "Successfully pushed to GitHub!",
        description: `Created ${milestoneResults.length} milestones, ${approvedPhases.length} epics and ${totalIssues} issues in ${targetRepo}.`,
      });
    } catch (error) {
      toast({
        title: "Failed to create GitHub resources",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
      setCreatingMilestones(false);
    }
  };

  if (submitted) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="border-0 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-green-600 to-emerald-600 text-white text-center py-12">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>
            </div>
            <CardTitle className="text-2xl mb-2">Successfully Deployed!</CardTitle>
            <CardDescription className="text-green-100">
              Your agent team structure has been pushed to GitHub
            </CardDescription>
          </CardHeader>
          <CardContent className="p-8 text-center">
            <div className="grid grid-cols-4 gap-6 mb-8">
              <div>
                <div className="text-3xl font-bold text-indigo-600 mb-1">{milestoneMap.size}</div>
                <div className="text-sm text-gray-600">Milestones</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-1">{approvedPhases.length}</div>
                <div className="text-sm text-gray-600">Epics Created</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-blue-600 mb-1">{totalIssues}</div>
                <div className="text-sm text-gray-600">Issues Generated</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600 mb-1">{allRoles.length}</div>
                <div className="text-sm text-gray-600">Roles Assigned</div>
              </div>
            </div>
            
            <div className="space-y-4">
              <Button 
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                onClick={() => window.open(`https://github.com/${summary.repository}/issues`, '_blank')}
              >
                <Github className="w-4 h-4 mr-2" />
                View on GitHub
              </Button>
              
              <div className="text-sm text-gray-500">
                Ready for Claude Flow SPARC agents to start execution
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-600 text-white">
          <CardTitle className="text-xl">Review & Submit</CardTitle>
          <CardDescription className="text-purple-100">
            Final review before pushing to GitHub
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Repository Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Github className="w-5 h-5 mr-2" />
            Target Repository
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {repoError ? (
            <Alert className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{repoError}</AlertDescription>
            </Alert>
          ) : null}
          
          <div>
            <Label htmlFor="repository">Repository</Label>
            <Select
              value={selectedRepo}
              onValueChange={setSelectedRepo}
              disabled={loadingRepos}
            >
              <SelectTrigger id="repository" className="mt-1">
                <SelectValue placeholder={loadingRepos ? "Loading repositories..." : "Select repository"} />
              </SelectTrigger>
              <SelectContent>
                {Array.isArray(repositories) && repositories.map(repo => (
                  <SelectItem key={repo.full_name} value={repo.full_name}>
                    {repo.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="branch">Branch</Label>
            {createNewBranch ? (
              <div className="space-y-2 mt-1">
                <Input
                  id="new-branch"
                  value={newBranchName}
                  onChange={(e) => setNewBranchName(e.target.value)}
                  placeholder="feature/agent-team-composer"
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setCreateNewBranch(false);
                    setNewBranchName('');
                  }}
                >
                  Use existing branch
                </Button>
              </div>
            ) : (
              <div className="space-y-2 mt-1">
                <Select
                  value={selectedBranch}
                  onValueChange={setSelectedBranch}
                  disabled={loadingBranches || !selectedRepo}
                >
                  <SelectTrigger id="branch">
                    <SelectValue placeholder={loadingBranches ? "Loading branches..." : "Select branch"} />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.isArray(branches) && branches.map(branch => (
                      <SelectItem key={branch} value={branch}>
                        {branch}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCreateNewBranch(true)}
                  disabled={!selectedRepo}
                >
                  Create new branch
                </Button>
              </div>
            )}
          </div>
          
          {loadingRepos && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
          )}
          
          <Button
            size="sm"
            variant="ghost"
            onClick={fetchRepositories}
            disabled={loadingRepos}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh Repositories
          </Button>
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Project Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <FileText className="w-5 h-5 mr-2" />
              Project Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-sm font-medium text-gray-700">Title</div>
              <div className="text-sm text-gray-600">{summary.title}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700">Domain</div>
              <Badge variant="outline">{summary.domain}</Badge>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700">Description</div>
              <div className="text-sm text-gray-600 line-clamp-3">{summary.description}</div>
            </div>
          </CardContent>
        </Card>

        {/* Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Users className="w-5 h-5 mr-2" />
              Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Approved Phases</span>
              <span className="font-semibold">{approvedPhases.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Issues</span>
              <span className="font-semibold">{totalIssues}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Active Roles</span>
              <span className="font-semibold">{allRoles.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">SPARC Enabled</span>
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            </div>
          </CardContent>
        </Card>

        {/* Active Roles */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <Zap className="w-5 h-5 mr-2" />
              Active Roles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {allRoles.map(role => (
                <Badge key={role} variant="secondary" className="text-xs">
                  {role}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Approved Phases */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Milestone className="w-5 h-5 mr-2" />
            Approved Phases
          </CardTitle>
          <CardDescription>
            These phases will be created as milestones and epics in your GitHub repository
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {approvedPhases.map((phase, index) => (
              <div key={phase.id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{phase.title}</div>
                    <div className="text-sm text-gray-600">{phase.description}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>{phase.roles.length} roles</span>
                  <span>{phase.issues.length} issues</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Warning if not all phases approved */}
      {approvedPhases.length < phases.length && (
        <Alert>
          <AlertDescription>
            {phases.length - approvedPhases.length} phase(s) not approved and will be skipped. 
            You can always run the tool again to add more phases later.
          </AlertDescription>
        </Alert>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onPrevious} disabled={isSubmitting}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Phases
        </Button>
        
        <Button 
          onClick={handleSubmit}
          disabled={isSubmitting || approvedPhases.length === 0 || !selectedRepo || (createNewBranch && !newBranchName)}
          className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              {creatingMilestones ? 'Creating Milestones...' : 'Creating Issues...'}
            </>
          ) : (
            <>
              <Github className="w-4 h-4 mr-2" />
              Push to GitHub
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default ReviewSubmit;
