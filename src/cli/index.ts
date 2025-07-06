#!/usr/bin/env node

import { Command } from 'commander';
import { promises as fs } from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import chalk from 'chalk';
import ora from 'ora';
import { config } from 'dotenv';
import { validateEnvironment } from '../services/environment';
import { parseReadme } from '../services/readme-parser';
import { generateProjectPlan } from '../services/llm-orchestrator';
import { startServer } from '../server';

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
      
      // Step 2: Read and parse README
      spinner.start('Reading README.md...');
      const readmePath = path.resolve(process.cwd(), options.readme);
      
      try {
        const readmeContent = await fs.readFile(readmePath, 'utf-8');
        const projectInfo = await parseReadme(readmeContent);
        spinner.succeed('README.md parsed successfully');
        
        console.log(chalk.blue('\nDetected project:'));
        console.log(chalk.gray(`  Title: ${projectInfo.title}`));
        console.log(chalk.gray(`  Domain: ${projectInfo.domain}`));
        
        // Step 3: Generate project plan using LLM cascade
        spinner.start('Generating project plan with Claude...');
        const projectData = await generateProjectPlan(projectInfo, readmeContent);
        spinner.succeed('Project plan generated');
        
        console.log(chalk.green(`\nGenerated ${projectData.phases.length} phases with ${projectData.phases.reduce((acc, p) => acc + p.issues.length, 0)} total tasks`));
        
        // Step 4: Save project data to temp file for server
        const tempDataPath = path.join(process.cwd(), '.agent-team-composer-data.json');
        await fs.writeFile(tempDataPath, JSON.stringify(projectData, null, 2));
        
        // Step 5: Start server and launch UI
        spinner.start('Starting localhost UI...');
        const serverUrl = await startServer(parseInt(options.port), tempDataPath);
        spinner.succeed(`UI started at ${serverUrl}`);
        
        // Step 6: Open browser
        console.log(chalk.blue('\nOpening browser...'));
        const start = process.platform === 'darwin' ? 'open' : 
                     process.platform === 'win32' ? 'start' : 'xdg-open';
        spawn(start, [serverUrl], { shell: true });
        
        console.log(chalk.green('\n✅ Agent Team Composer is ready!'));
        console.log(chalk.gray('\nPress Ctrl+C to stop the server'));
        
      } catch (error) {
        if (error.code === 'ENOENT') {
          spinner.fail(`README.md not found at ${readmePath}`);
          console.error(chalk.red('\nPlease ensure you have a README.md file in your repository'));
        } else {
          throw error;
        }
      }
      
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