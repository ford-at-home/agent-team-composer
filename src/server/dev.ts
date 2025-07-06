import { startServer } from './index';
import { promises as fs } from 'fs';
import path from 'path';

// Create mock project data for development
const mockProjectData = {
  summary: {
    title: "Agent Team Composer",
    description: "A CLI tool that transforms README files into GitHub project plans",
    domain: "devtools",
    repository: "ford-at-home/project-delivery-navigator",
    branch: "main"
  },
  phases: [
    {
      id: "discovery",
      title: "Discovery & Requirements",
      description: "Initial project analysis and requirement gathering",
      roles: ["Product Owner", "UX Researcher", "AI Architect"],
      approved: true,
      issues: [
        {
          title: "Analyze README parsing requirements",
          description: "Study various README formats to design robust parsing logic",
          role: "AI Architect"
        },
        {
          title: "Define user journey for CLI-to-UI workflow",
          description: "Map out the user experience from NPM install to GitHub push",
          role: "UX Researcher"
        }
      ]
    },
    {
      id: "development",
      title: "Core Development",
      description: "Implementation of core features",
      roles: ["Frontend Developer", "Backend Developer", "AI Engineer"],
      approved: true,
      issues: [
        {
          title: "Implement CLI foundation",
          description: "Build the core CLI structure with argument parsing",
          role: "Backend Developer"
        },
        {
          title: "Build React UI components",
          description: "Create the localhost UI with React and state management",
          role: "Frontend Developer"
        }
      ]
    }
  ]
};

async function startDev() {
  // Create temp file with mock data
  const tempPath = path.join(process.cwd(), '.agent-team-composer-dev.json');
  await fs.writeFile(tempPath, JSON.stringify(mockProjectData, null, 2));
  
  console.log('Starting development server with mock data...');
  
  // Start server
  await startServer(3000, tempPath);
}

startDev().catch(console.error);