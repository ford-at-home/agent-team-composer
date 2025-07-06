export interface ProjectSummary {
  title: string;
  description: string;
  domain: string;
  repository: string;
  branch: string;
}

export interface Issue {
  title: string;
  description: string;
  role: string;
}

export interface Phase {
  id: string;
  title: string;
  description: string;
  roles: string[];
  issues: Issue[];
  approved: boolean;
}

export interface ProjectData {
  summary: ProjectSummary;
  phases: Phase[];
}

export interface LLMPhaseGeneration {
  phases: Array<{
    id: string;
    title: string;
    description: string;
    suggestedRoles: string[];
  }>;
}

export interface LLMEpicGeneration {
  phaseId: string;
  roles: string[];
  tasks: Array<{
    title: string;
    description: string;
    suggestedRole: string;
  }>;
}

export interface GitHubIssue {
  title: string;
  body: string;
  labels: string[];
  assignees?: string[];
}

export interface GitHubEpic {
  title: string;
  body: string;
  labels: string[];
  issues: GitHubIssue[];
}