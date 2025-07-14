import { config } from 'dotenv';
import express from 'express';
import cors from 'cors';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import { promisify } from 'util';
import { ProjectData } from '../types';
import { GitHubService } from '../services/github-service';
import { z } from 'zod';
import { errorHandler, asyncHandler } from '../utils/error-handler';
import { TelemetryService } from '../services/telemetry';
import { ResilienceManager } from '../services/resilience';

// Load environment variables from .env file
config();

const execAsync = promisify(exec);

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
  const telemetry = TelemetryService.getInstance();
  const resilience = ResilienceManager.getInstance();
  
  res.json({ 
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    metrics: {
      extractionSuccessRate: telemetry.getExtractionSuccessRate(),
      methodSuccessRates: telemetry.getMethodSuccessRates(),
      resilience: resilience.getStatus()
    }
  });
});

// Telemetry endpoint for monitoring
app.get('/api/telemetry', (req, res) => {
  const telemetry = TelemetryService.getInstance();
  
  res.json({
    report: JSON.parse(telemetry.generateDailyReport()),
    commonErrors: telemetry.getMostCommonErrors()
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

// API endpoint to get README content from the current working directory
app.get('/api/readme', asyncHandler(async (req, res) => {
  try {
    const readmePath = path.join(process.cwd(), 'README.md');
    const content = await fs.readFile(readmePath, 'utf8');
    res.json({ content });
  } catch (error) {
    if (error.code === 'ENOENT') {
      return res.status(404).json({ 
        error: 'README.md not found',
        details: 'No README.md file found in the current directory'
      });
    }
    throw error;
  }
}));

// API endpoint for AI form population
app.post('/api/populate-form', asyncHandler(async (req, res) => {
  const { readmeContent, existingData } = req.body;
  
  if (!readmeContent) {
    return res.status(400).json({
      error: 'Missing README content',
      details: 'README content is required for AI form population'
    });
  }
  
  try {
    // Import the AI form populator
    const { populateFormWithAI } = await import('../services/ai-form-populator.js');
    
    // Call the AI service
    const suggestions = await populateFormWithAI(readmeContent, existingData);
    
    res.json(suggestions);
  } catch (error) {
    console.error('AI form population error:', error);
    
    // Check if it's an API key error
    if (error.message?.includes('API key') || error.message?.includes('authentication')) {
      return res.status(401).json({
        error: 'Authentication required',
        details: 'Please ensure ANTHROPIC_API_KEY environment variable is set'
      });
    }
    
    res.status(500).json({
      error: 'Failed to populate form with AI',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}));

// API endpoint to update project data
app.put('/api/project', async (req, res) => {
  projectData = req.body;
  
  // Save to temp file if path is available
  if (dataFilePath) {
    await fs.writeFile(dataFilePath, JSON.stringify(projectData, null, 2));
  }
  
  res.json({ success: true });
});

// API endpoint to generate ONLY phases
app.post('/api/generate-phases', asyncHandler(async (req, res) => {
  const { metadata, readmeContent } = req.body;
  
  try {
    const { LLMOrchestrator } = await import('../services/llm-orchestrator');
    const orchestrator = new LLMOrchestrator();
    
    // Generate ONLY the phases (8 SDLC phases)
    const phases = await orchestrator.generatePhases({
      title: metadata.title,
      description: metadata.description,
      domain: metadata.domain,
      features: metadata.features || []
    }, readmeContent);
    
    // Convert to the format the UI expects - auto-approve all phases
    const formattedPhases = phases.map((phase: { id: string; title: string; description: string; suggestedRoles?: string[] }) => ({
      id: phase.id,
      title: phase.title,
      description: phase.description,
      roles: phase.suggestedRoles || [],
      issues: [], // No issues yet
      approved: true // Auto-approve all phases
    }));
    
    res.json({ phases: formattedPhases });
  } catch (error) {
    console.error('Phase generation error:', error);
    res.status(500).json({ 
      error: 'Failed to generate phases',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}));

// API endpoint to generate epics for approved phases
app.post('/api/generate-epics', asyncHandler(async (req, res) => {
  const { phases, metadata } = req.body;
  
  if (!phases || !Array.isArray(phases)) {
    return res.status(400).json({ 
      error: 'Missing phases array',
      details: 'phases parameter is required and must be an array'
    });
  }
  
  try {
    const { LLMOrchestrator } = await import('../services/llm-orchestrator');
    const orchestrator = new LLMOrchestrator();
    
    // Filter to only approved phases
    const approvedPhases = phases.filter((phase: { approved: boolean }) => phase.approved);
    
    if (approvedPhases.length === 0) {
      return res.json({ phases: phases }); // Return unchanged if no approved phases
    }
    
    console.log(`Generating epics for ${approvedPhases.length} approved phases...`);
    
    // Generate epics using the same method as in generateProjectPlan
    const phasesWithEpics = await orchestrator.generateEpicsForApprovedPhases(
      approvedPhases,
      metadata || { title: 'Project', description: 'Project description' }
    );
    
    // Merge back with non-approved phases
    const allPhases = phases.map((phase: { id: string }) => {
      const updatedPhase = phasesWithEpics.find((p: { id: string }) => p.id === phase.id);
      return updatedPhase || phase;
    });
    
    res.json({ phases: allPhases });
  } catch (error) {
    console.error('Epic generation error:', error);
    res.status(500).json({ 
      error: 'Failed to generate epics',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}));

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
  repository: z.string().regex(/^[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+$/).optional(), // Made optional, will use from UI
  phases: z.array(z.any()), // Will be validated in GitHubService
  milestoneMap: z.record(z.string(), z.number()).optional() // Optional milestone mapping
});

// API endpoint to check GitHub authentication
app.get('/api/github/auth', asyncHandler(async (req, res) => {
  const githubService = new GitHubService();
  const authStatus = await githubService.checkAuthentication();
  
  // Add more debug info
  const debugInfo = {
    ...authStatus,
    hasToken: !!process.env.GITHUB_TOKEN,
    tokenPreview: process.env.GITHUB_TOKEN ? `${process.env.GITHUB_TOKEN.substring(0, 4)}...` : 'None'
  };
  
  res.json(debugInfo);
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

// API endpoint to test milestone permissions for a repository
app.post('/api/github/test-milestone-permissions', asyncHandler(async (req, res) => {
  const { repository } = req.body;
  
  if (!repository) {
    return res.status(400).json({ 
      error: 'Repository parameter required'
    });
  }
  
  const githubService = new GitHubService();
  
  try {
    // Check authentication first
    const authStatus = await githubService.checkAuthentication();
    if (!authStatus.authenticated) {
      return res.status(401).json({ 
        error: 'GitHub authentication required',
        details: authStatus.error || 'Please set GITHUB_TOKEN environment variable'
      });
    }
    
    // Parse repository
    const parts = repository.split('/');
    if (parts.length !== 2) {
      return res.status(400).json({ 
        error: 'Invalid repository format. Expected: owner/repo'
      });
    }
    
    const [owner, repo] = parts;
    
    // Check repository access
    const repoResponse = await githubService.octokit.repos.get({ owner, repo });
    
    // Check if issues are enabled
    if (!repoResponse.data.has_issues) {
      return res.json({
        canCreateMilestones: false,
        reason: 'Repository has issues disabled',
        details: 'Issues must be enabled to create milestones'
      });
    }
    
    // Test milestone permissions
    await githubService.octokit.issues.listMilestones({
      owner,
      repo,
      state: 'all',
      per_page: 1
    });
    
    res.json({
      canCreateMilestones: true,
      repository: repository,
      hasIssues: repoResponse.data.has_issues,
      permissions: repoResponse.data.permissions
    });
    
  } catch (error) {
    const err = error as { status?: number; message?: string };
    
    if (err.status === 404) {
      return res.json({
        canCreateMilestones: false,
        reason: 'Repository not found or no access',
        details: 'Check repository name and token permissions'
      });
    } else if (err.status === 403) {
      return res.json({
        canCreateMilestones: false,
        reason: 'Permission denied',
        details: 'GitHub token needs repo permissions to access milestones'
      });
    }
    
    return res.status(500).json({ 
      error: 'Failed to test milestone permissions',
      details: err.message || 'Unknown error'
    });
  }
}));

// API endpoint to create GitHub milestones and issues
app.post('/api/github/create-milestones-and-issues', async (req, res) => {
  try {
    // Validate input
    const validatedInput = CreateIssuesSchema.parse(req.body);
    const { repository, phases } = validatedInput;
    
    console.log(`Creating milestones and issues for ${repository}...`);
    
    // Use GitHub API
    const githubService = new GitHubService();
    
    // Check authentication first
    const authStatus = await githubService.checkAuthentication();
    if (!authStatus.authenticated) {
      return res.status(401).json({ 
        error: 'GitHub authentication required',
        details: authStatus.error || 'Please set GITHUB_TOKEN environment variable with proper permissions'
      });
    }
    
    // Step 1: Create milestones
    const milestoneResults = await githubService.createMilestones(repository, phases);
    
    // Step 2: Create milestone map
    const milestoneMap = new Map<string, number>();
    milestoneResults.forEach(result => {
      milestoneMap.set(result.phase, result.milestoneNumber);
    });
    
    // Step 3: Create issues with milestone associations
    const issueResults = await githubService.createIssuesFromPhases(repository, phases, milestoneMap);
    
    res.json({ 
      success: true, 
      milestones: milestoneResults,
      issues: issueResults 
    });
    
  } catch (error) {
    console.error('GitHub creation error:', error);
    
    if (error instanceof z.ZodError) {
      return res.status(400).json({ 
        error: 'Invalid request data',
        details: error.errors
      });
    }
    
    res.status(500).json({ 
      error: 'Failed to create GitHub milestones and issues',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// API endpoint to create GitHub issues only (legacy)
app.post('/api/github/create-issues', async (req, res) => {
  try {
    // Validate input
    const validatedInput = CreateIssuesSchema.parse(req.body);
    const { repository, phases, milestoneMap } = validatedInput;
    
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
    
    // Convert milestone map from object back to Map
    const milestoneMapInstance = milestoneMap ? new Map(Object.entries(milestoneMap)) : undefined;
    
    // Create issues with milestone associations
    const results = await githubService.createIssuesFromPhases(repository, phases, milestoneMapInstance);
    
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

// Function to kill processes on a specific port
async function killPortProcess(port: number): Promise<void> {
  try {
    // Find process using the port
    const { stdout } = await execAsync(`lsof -ti:${port}`);
    if (stdout.trim()) {
      const pids = stdout.trim().split('\n');
      for (const pid of pids) {
        if (pid) {
          try {
            await execAsync(`kill -9 ${pid}`);
            console.log(`Killed process ${pid} on port ${port}`);
          } catch (error) {
            // Process may already be dead, ignore
          }
        }
      }
    }
  } catch (error) {
    // No process found on port, which is fine
  }
}

// Function to clean up common ports used by agent-team-composer
async function cleanupPorts(): Promise<void> {
  console.log('Cleaning up any existing agent-team-composer processes...');
  const ports = [3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010];
  
  // Kill all ports sequentially to be more aggressive
  for (const port of ports) {
    await killPortProcess(port);
  }
  
  // Also kill any node processes that might be agent-team-composer
  try {
    await execAsync('pkill -f "agent-team-composer"');
    console.log('Killed any existing agent-team-composer processes');
  } catch (error) {
    // No processes found, which is fine
  }
  
  // Give it a moment for processes to fully terminate
  await new Promise(resolve => setTimeout(resolve, 2000));
}

export async function startServer(port: number, tempDataPath: string): Promise<string> {
  // Load project data
  dataFilePath = tempDataPath;
  const dataContent = await fs.readFile(tempDataPath, 'utf8');
  projectData = JSON.parse(dataContent);
  
  // Determine the package root directory (where the dist files are located)
  // When running from npm/npx, __dirname will be inside the installed package
  const currentFileUrl = import.meta.url;
  const currentFilePath = fileURLToPath(currentFileUrl);
  const currentDir = path.dirname(currentFilePath);
  
  // Navigate up from dist/server to the package root
  const packageRoot = path.resolve(currentDir, '..', '..');
  const distPath = path.join(packageRoot, 'dist');
  
  // Always serve the built files from the package, not from cwd
  // This ensures we serve Agent Composer UI, not the user's local files
  try {
    // Check if dist directory exists in the package
    await fs.access(distPath);
    
    // Serve static files from the package's dist directory with no-cache headers
    app.use(express.static(distPath, {
      setHeaders: (res, path) => {
        // Prevent caching during development
        res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
        res.setHeader('Pragma', 'no-cache');
        res.setHeader('Expires', '0');
      }
    }));
    
    // Fallback to index.html for client-side routing
    app.get('*', (req, res) => {
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
      res.setHeader('Pragma', 'no-cache');
      res.setHeader('Expires', '0');
      res.sendFile(path.join(distPath, 'index.html'));
    });
  } catch (error) {
    console.error('Could not find built files in package directory:', distPath);
    console.error('This may indicate the package was not built properly.');
    throw new Error('Agent Composer UI files not found. Please reinstall the package.');
  }
  
  return new Promise((resolve, reject) => {
    // Start with port 0 to get any available port
    const server = app.listen(0, () => {
      const address = server.address();
      const actualPort = typeof address === 'string' ? parseInt(address) : address?.port || 3000;
      const url = `http://localhost:${actualPort}`;
      console.log(`Server running at ${url}`);
      resolve(url);
      
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
    
    server.on('error', (err: NodeJS.ErrnoException) => {
      reject(err);
    });
  });
}