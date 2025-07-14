import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ArrowRight, ArrowLeft, ChevronDown, ChevronRight, Plus, Trash2, Edit, Save, X, FolderOpen, FileText, Users, Copy } from 'lucide-react';
import { Phase, Issue } from '@/types';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import ReactMarkdown from 'react-markdown';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface EpicIssueViewProps {
  phases: Phase[];
  setPhases: (phases: Phase[]) => void;
  onNext: () => void;
  onPrevious: () => void;
}

const EpicIssueView = ({ phases, setPhases, onNext, onPrevious }: EpicIssueViewProps) => {
  const [expandedEpics, setExpandedEpics] = useState<Set<string>>(new Set());
  const [editingIssue, setEditingIssue] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Issue | null>(null);
  const [selectedEpics, setSelectedEpics] = useState<Set<string>>(new Set());
  const [selectedIssues, setSelectedIssues] = useState<Set<string>>(new Set());

  // Toggle epic expansion
  const toggleEpic = (epicId: string) => {
    const newExpanded = new Set(expandedEpics);
    if (newExpanded.has(epicId)) {
      newExpanded.delete(epicId);
    } else {
      newExpanded.add(epicId);
    }
    setExpandedEpics(newExpanded);
  };

  // Add new issue to epic
  const addIssue = (phaseId: string) => {
    const newIssue: Issue = {
      title: 'New Issue',
      description: 'Issue description',
      role: 'Developer'
    };
    
    setPhases(phases.map(phase => 
      phase.id === phaseId 
        ? { ...phase, issues: [...phase.issues, newIssue] }
        : phase
    ));
  };

  // Delete issue
  const deleteIssue = (phaseId: string, issueIndex: number) => {
    setPhases(phases.map(phase => 
      phase.id === phaseId 
        ? { ...phase, issues: phase.issues.filter((_, i) => i !== issueIndex) }
        : phase
    ));
  };

  // Start editing issue
  const startEdit = (issue: Issue, phaseId: string, issueIndex: number) => {
    setEditingIssue(`${phaseId}-${issueIndex}`);
    setEditForm({ ...issue });
  };

  // Save edited issue
  const saveEdit = (phaseId: string, issueIndex: number) => {
    if (!editForm) return;
    
    setPhases(phases.map(phase => 
      phase.id === phaseId 
        ? {
            ...phase,
            issues: phase.issues.map((issue, i) => 
              i === issueIndex ? editForm : issue
            )
          }
        : phase
    ));
    
    setEditingIssue(null);
    setEditForm(null);
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingIssue(null);
    setEditForm(null);
  };

  // Bulk operations
  const deleteSelectedIssues = () => {
    const updatedPhases = phases.map(phase => ({
      ...phase,
      issues: phase.issues.filter((_, index) => 
        !selectedIssues.has(`${phase.id}-${index}`)
      )
    }));
    setPhases(updatedPhases);
    setSelectedIssues(new Set());
  };

  // Toggle issue selection
  const toggleIssueSelection = (issueId: string) => {
    const newSelected = new Set(selectedIssues);
    if (newSelected.has(issueId)) {
      newSelected.delete(issueId);
    } else {
      newSelected.add(issueId);
    }
    setSelectedIssues(newSelected);
  };

  // Get available roles
  const availableRoles = Array.from(new Set(
    phases.flatMap(phase => phase.roles)
  ));

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-600 text-white">
          <CardTitle className="text-xl flex items-center">
            <FolderOpen className="w-5 h-5 mr-2" />
            Epic Issue View
          </CardTitle>
          <CardDescription className="text-purple-100">
            Review and edit all issues grouped by epic
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Bulk Actions */}
      {selectedIssues.size > 0 && (
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                {selectedIssues.size} issue{selectedIssues.size > 1 ? 's' : ''} selected
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={deleteSelectedIssues}
                >
                  <Trash2 className="w-4 h-4 mr-1" />
                  Delete Selected
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setSelectedIssues(new Set())}
                >
                  Clear Selection
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Epics and Issues */}
      <div className="space-y-4">
        {phases.filter(phase => phase.approved).map((phase) => (
          <Card key={phase.id} className="overflow-hidden">
            <Collapsible
              open={expandedEpics.has(phase.id)}
              onOpenChange={() => toggleEpic(phase.id)}
            >
              <CollapsibleTrigger className="w-full">
                <CardHeader className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {expandedEpics.has(phase.id) ? (
                        <ChevronDown className="w-5 h-5" />
                      ) : (
                        <ChevronRight className="w-5 h-5" />
                      )}
                      <div className="text-left">
                        <CardTitle className="text-lg">{phase.title}</CardTitle>
                        <CardDescription>{phase.description}</CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Badge variant="secondary">
                        {phase.issues.length} issue{phase.issues.length !== 1 ? 's' : ''}
                      </Badge>
                      <Badge variant="outline">
                        {phase.roles.length} role{phase.roles.length !== 1 ? 's' : ''}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <CardContent className="pt-0">
                  {/* Roles */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {phase.roles.map(role => (
                      <Badge key={role} variant="secondary" className="text-xs">
                        <Users className="w-3 h-3 mr-1" />
                        {role}
                      </Badge>
                    ))}
                  </div>

                  {/* Issues */}
                  <div className="space-y-3">
                    {phase.issues.map((issue, index) => {
                      const issueId = `${phase.id}-${index}`;
                      const isEditing = editingIssue === issueId;
                      
                      return (
                        <Card key={index} className={`${selectedIssues.has(issueId) ? 'ring-2 ring-blue-500' : ''}`}>
                          <CardContent className="pt-4">
                            {isEditing && editForm ? (
                              // Edit mode
                              <div className="space-y-4">
                                <div>
                                  <Label htmlFor={`title-${issueId}`}>Title</Label>
                                  <Input
                                    id={`title-${issueId}`}
                                    value={editForm.title}
                                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                                    className="mt-1"
                                  />
                                </div>
                                
                                <div>
                                  <Label htmlFor={`desc-${issueId}`}>Description</Label>
                                  <Textarea
                                    id={`desc-${issueId}`}
                                    value={editForm.description}
                                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                                    rows={4}
                                    className="mt-1"
                                  />
                                </div>
                                
                                <div>
                                  <Label htmlFor={`role-${issueId}`}>Assigned Role</Label>
                                  <Select
                                    value={editForm.role}
                                    onValueChange={(value) => setEditForm({ ...editForm, role: value })}
                                  >
                                    <SelectTrigger id={`role-${issueId}`} className="mt-1">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {availableRoles.map(role => (
                                        <SelectItem key={role} value={role}>
                                          {role}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                </div>
                                
                                <div className="flex justify-end gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={cancelEdit}
                                  >
                                    <X className="w-4 h-4 mr-1" />
                                    Cancel
                                  </Button>
                                  <Button
                                    size="sm"
                                    onClick={() => saveEdit(phase.id, index)}
                                  >
                                    <Save className="w-4 h-4 mr-1" />
                                    Save
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              // View mode
                              <div>
                                <div className="flex items-start justify-between mb-2">
                                  <div className="flex items-start space-x-3 flex-1">
                                    <input
                                      type="checkbox"
                                      checked={selectedIssues.has(issueId)}
                                      onChange={() => toggleIssueSelection(issueId)}
                                      className="mt-1"
                                    />
                                    <div className="flex-1">
                                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                        {issue.title}
                                      </h4>
                                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                        {issue.description}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2 ml-4">
                                    <Badge variant="outline" className="text-xs">
                                      {issue.role}
                                    </Badge>
                                    <Button
                                      size="icon"
                                      variant="ghost"
                                      onClick={() => startEdit(issue, phase.id, index)}
                                    >
                                      <Edit className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      size="icon"
                                      variant="ghost"
                                      onClick={() => deleteIssue(phase.id, index)}
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </div>
                                </div>
                                
                                {/* Preview formatted issue */}
                                <Dialog>
                                  <DialogTrigger asChild>
                                    <Button variant="link" size="sm" className="text-xs">
                                      <FileText className="w-3 h-3 mr-1" />
                                      Preview GitHub Issue
                                    </Button>
                                  </DialogTrigger>
                                  <DialogContent className="max-w-2xl">
                                    <DialogHeader>
                                      <DialogTitle>{issue.title}</DialogTitle>
                                      <DialogDescription>
                                        Preview of how this will appear in GitHub
                                      </DialogDescription>
                                    </DialogHeader>
                                    <div className="mt-4">
                                      {issue && (
                                        <Tabs defaultValue="preview">
                                          <TabsList>
                                            <TabsTrigger value="preview">Preview</TabsTrigger>
                                            <TabsTrigger value="markdown">Markdown</TabsTrigger>
                                          </TabsList>
                                          <TabsContent value="preview" className="prose prose-sm dark:prose-invert max-w-none">
                                            <ReactMarkdown>
                                              {`${issue.description}\n\n**Assigned Role:** ${issue.role}\n**Epic:** ${phase.title}`}
                                            </ReactMarkdown>
                                          </TabsContent>
                                          <TabsContent value="markdown">
                                            <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-4 rounded overflow-auto">
                                              {`${issue.description}\n\n**Assigned Role:** ${issue.role}\n**Epic:** ${phase.title}`}
                                            </pre>
                                          </TabsContent>
                                        </Tabs>
                                      )}
                                    </div>
                                  </DialogContent>
                                </Dialog>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      );
                    })}
                    
                    {/* Add Issue Button */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => addIssue(phase.id)}
                      className="w-full"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Issue
                    </Button>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        ))}
      </div>

      {/* No approved phases message */}
      {phases.filter(p => p.approved).length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-600">No approved phases yet. Please go back and approve phases to see issues here.</p>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onPrevious}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Epic View
        </Button>
        
        <Button 
          onClick={onNext}
          disabled={phases.filter(p => p.approved).length === 0}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
        >
          Continue to GitHub Sync
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
};

export default EpicIssueView;