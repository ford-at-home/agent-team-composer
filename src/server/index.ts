import express from 'express';
import cors from 'cors';
import { promises as fs } from 'fs';
import path from 'path';
import { createServer } from 'vite';
import { ProjectData } from '../types';
import { GitHubService } from '../services/github-service';
import { z } from 'zod';
import { errorHandler, asyncHandler } from '../utils/error-handler';

const app = express();
// Configure CORS for production
const corsOptions = {
  origin: process.env.NODE_ENV === 'production' 
    ? process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000']
    : true,
  credentials: true,
  maxAge: 86400 // 24 hours
};
app.use(cors(corsOptions));
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

let projectData: ProjectData | null = null;
let dataFilePath: string | null = null;

// API endpoint to get project data
app.get('/api/project', (req, res) => {
  if (!projectData) {
    return res.status(404).json({ error: 'No project data loaded' });
  }
  res.json(projectData);
});

// API endpoint to update project data
app.put('/api/project', async (req, res) => {
  projectData = req.body;
  
  // Save to temp file if path is available
  if (dataFilePath) {
    await fs.writeFile(dataFilePath, JSON.stringify(projectData, null, 2));
  }
  
  res.json({ success: true });
});

// API endpoint to generate project plan from parsed metadata
app.post('/api/generate-plan', asyncHandler(async (req, res) => {
  const { metadata, readmeContent } = req.body;
  
  if (!metadata || !readmeContent) {
    return res.status(400).json({ 
      error: 'Missing required fields',
      details: 'Both metadata and readmeContent are required'
    });
  }
  
  try {
    // Import the LLM orchestrator
    const { generateProjectPlan } = await import('../services/llm-orchestrator');
    
    // Generate the project plan
    const projectPlan = await generateProjectPlan(metadata, readmeContent);
    
    // Save to temp file
    projectData = projectPlan;
    if (dataFilePath) {
      await fs.writeFile(dataFilePath, JSON.stringify(projectData, null, 2));
    }
    
    res.json(projectPlan);
  } catch (error) {
    console.error('Plan generation error:', error);
    res.status(500).json({ 
      error: 'Failed to generate project plan',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}));

// Input validation schema
const CreateIssuesSchema = z.object({
  repository: z.string().regex(/^[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+$/),
  phases: z.array(z.any()) // Will be validated in GitHubService
});

// API endpoint to check GitHub authentication
app.get('/api/github/auth', asyncHandler(async (req, res) => {
  const githubService = new GitHubService();
  const authStatus = await githubService.checkAuthentication();
  res.json(authStatus);
}));

// API endpoint to get user repositories
app.get('/api/github/repositories', asyncHandler(async (req, res) => {
  const githubService = new GitHubService();
  
  // Check authentication first
  const authStatus = await githubService.checkAuthentication();
  if (!authStatus.authenticated) {
    return res.status(401).json({ 
      error: 'GitHub authentication required',
      details: 'Please set GITHUB_TOKEN environment variable'
    });
  }
  
  // Fetch repositories
  const repos = await githubService.getUserRepositories();
  res.json(repos);
}));

// API endpoint to get repository branches
app.get('/api/github/branches', asyncHandler(async (req, res) => {
  const { repo } = req.query;
  
  if (!repo || typeof repo !== 'string') {
    return res.status(400).json({ 
      error: 'Repository parameter required'
    });
  }
  
  const githubService = new GitHubService();
  const branches = await githubService.getRepositoryBranches(repo);
  res.json(branches);
}));

// API endpoint to create GitHub issues
app.post('/api/github/create-issues', async (req, res) => {
  try {
    // Validate input
    const validatedInput = CreateIssuesSchema.parse(req.body);
    const { repository, phases } = validatedInput;
    
    console.log(`Creating issues for ${repository}...`);
    
    // Use GitHub API instead of CLI
    const githubService = new GitHubService();
    
    // Check authentication first
    const authStatus = await githubService.checkAuthentication();
    if (!authStatus.authenticated) {
      return res.status(401).json({ 
        error: 'GitHub authentication required',
        details: 'Please set GITHUB_TOKEN environment variable'
      });
    }
    
    // Create issues
    const results = await githubService.createIssuesFromPhases(repository, phases);
    
    res.json({ success: true, results });
    
  } catch (error) {
    console.error('GitHub creation error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({ 
        error: 'Invalid request data',
        details: error.errors
      });
    }
    
    res.status(500).json({ 
      error: 'Failed to create GitHub issues',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export async function startServer(port: number, tempDataPath: string): Promise<string> {
  // Load project data
  dataFilePath = tempDataPath;
  const dataContent = await fs.readFile(tempDataPath, 'utf8');
  projectData = JSON.parse(dataContent);
  
  // In development, use Vite dev server
  if (process.env.NODE_ENV !== 'production') {
    // Create Vite server
    const vite = await createServer({
      root: process.cwd(),
      server: {
        middlewareMode: true,
        cors: true
      }
    });
    
    // Use vite's connect instance as middleware
    app.use(vite.middlewares);
  } else {
    // In production, serve built files
    app.use(express.static(path.join(process.cwd(), 'dist')));
    
    // Fallback to index.html for client-side routing
    app.get('*', (req, res) => {
      res.sendFile(path.join(process.cwd(), 'dist', 'index.html'));
    });
  }
  
  return new Promise((resolve) => {
    const server = app.listen(port, () => {
      const url = `http://localhost:${port}`;
      console.log(`Server running at ${url}`);
      resolve(url);
    });
    
    // Graceful shutdown
    process.on('SIGINT', () => {
      console.log('\nShutting down server...');
      server.close();
      
      // Clean up temp file
      if (dataFilePath) {
        fs.unlink(dataFilePath).catch(() => {});
      }
      
      process.exit(0);
    });
  });
}