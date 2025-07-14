#!/usr/bin/env node

import { Command } from 'commander';
import { promises as fs } from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import chalk from 'chalk';
import ora from 'ora';
import { config } from 'dotenv';
import { validateEnvironment } from '../services/environment.js';
import { startServer } from '../server/index.js';

config();

const program = new Command();

program
  .name('agent-team-composer')
  .description('CLI tool to generate agent-powered delivery plans from README.md')
  .version('1.0.0');

program
  .command('init')
  .description('Initialize agent team composer in current repository')
  .option('-p, --port <port>', 'Port for localhost UI', '3000')
  .option('-r, --readme <path>', 'Path to README.md file', 'README.md')
  .option('--skip-gh-check', 'Skip GitHub CLI verification')
  .option('--fresh', 'Force fresh generation, ignoring any cached progress')
  .action(async (options) => {
    const spinner = ora();
    
    try {
      // Step 1: Validate environment
      spinner.start('Validating environment...');
      const envCheck = await validateEnvironment(options.skipGhCheck);
      
      if (!envCheck.isValid) {
        spinner.fail('Environment validation failed');
        console.error(chalk.red('\nMissing requirements:'));
        envCheck.missing.forEach(item => {
          console.error(chalk.red(`  - ${item}`));
        });
        
        if (envCheck.missing.includes('GitHub CLI')) {
          console.log(chalk.yellow('\nTo install GitHub CLI:'));
          console.log(chalk.gray('  brew install gh (macOS)'));
          console.log(chalk.gray('  winget install --id GitHub.cli (Windows)'));
          console.log(chalk.gray('  https://github.com/cli/cli#installation (Other)'));
        }
        
        if (envCheck.missing.includes('ANTHROPIC_API_KEY')) {
          console.log(chalk.yellow('\nTo set Anthropic API key:'));
          console.log(chalk.gray('  export ANTHROPIC_API_KEY=your-api-key'));
        }
        
        process.exit(1);
      }
      spinner.succeed('Environment validated');
      
      // Step 2: Check for existing data or create minimal placeholder
      const tempDataPath = path.join(process.cwd(), '.agent-team-composer-data.json');
      
      try {
        // Check if we have existing data
        await fs.access(tempDataPath);
        spinner.succeed('Found existing project data');
      } catch {
        // Create minimal placeholder data - NO LLM CALLS
        const placeholderData = {
          title: "Project",
          description: "Initializing...",
          phases: [],
          metadata: {
            initialized: false,
            timestamp: new Date().toISOString()
          }
        };
        await fs.writeFile(tempDataPath, JSON.stringify(placeholderData, null, 2));
        spinner.succeed('Created initial data structure');
      }
      
      // Step 3: Start server and launch UI immediately
      spinner.start('Starting localhost UI...');
      const serverUrl = await startServer(parseInt(options.port), tempDataPath);
      spinner.succeed(`UI started at ${serverUrl}`);
      
      // Step 4: Open browser
      console.log(chalk.blue('\nOpening browser...'));
      const start = process.platform === 'darwin' ? 'open' : 
                   process.platform === 'win32' ? 'start' : 'xdg-open';
      spawn(start, [serverUrl], { shell: true });
      
      console.log(chalk.green('\n✅ Agent Team Composer is ready!'));
      console.log(chalk.gray('\nPress Ctrl+C to stop the server'));
      
      // Handle process termination
      process.on('SIGINT', () => {
        console.log(chalk.yellow('\n\nShutting down server...'));
        process.exit(0);
      });
      
      process.on('SIGTERM', () => {
        console.log(chalk.yellow('\n\nShutting down server...'));
        process.exit(0);
      });
      
    } catch (error) {
      spinner.fail('An error occurred');
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

program
  .command('validate')
  .description('Validate environment setup')
  .action(async () => {
    const spinner = ora('Checking environment...').start();
    const envCheck = await validateEnvironment(false);
    
    if (envCheck.isValid) {
      spinner.succeed('All requirements met!');
      console.log(chalk.green('\n✅ Ready to use agent-team-composer'));
    } else {
      spinner.fail('Missing requirements');
      console.error(chalk.red('\nMissing:'));
      envCheck.missing.forEach(item => {
        console.error(chalk.red(`  - ${item}`));
      });
    }
  });

program.parse();