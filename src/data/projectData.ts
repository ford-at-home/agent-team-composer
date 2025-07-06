
export const projectData = {
  summary: {
    title: "Agent Team Composer",
    description: "A lightweight NPM CLI tool that launches a localhost UI for assembling agent-powered delivery plans based on an 8-phase lifecycle. It auto-detects project requirements from README.md, scaffolds epics and issues, and pushes structured work items to GitHub, optimized for Claude Flow SPARC methodology.",
    domain: "DevOps/Infrastructure",
    repository: "flyingpig/agent-team-composer",
    branch: "main"
  },
  phases: [
    {
      id: "discovery",
      title: "Discovery & Requirements",
      description: "Initial project analysis, stakeholder alignment, and requirement gathering",
      roles: ["Product Owner", "UX Researcher", "AI Architect"],
      approved: false,
      issues: [
        {
          title: "Conduct stakeholder interviews and requirements gathering",
          description: "Interview key stakeholders to understand project goals, constraints, and success criteria. Document functional and non-functional requirements.",
          role: "Product Owner"
        },
        {
          title: "Analyze existing README.md parsing requirements",
          description: "Study various README.md formats and structures to design robust parsing logic for project detection.",
          role: "AI Architect"
        },
        {
          title: "Research user journey for CLI-to-UI workflow",
          description: "Map out the user experience from NPM install to GitHub push, identifying pain points and optimization opportunities.",
          role: "UX Researcher"
        },
        {
          title: "Define Claude Flow SPARC integration requirements",
          description: "Specify how issues should be structured and labeled for optimal Claude Flow SPARC agent consumption.",
          role: "AI Architect"
        }
      ]
    },
    {
      id: "planning",
      title: "Technical Planning & Architecture",
      description: "System design, technology selection, and implementation roadmap",
      roles: ["AI Architect", "Software Engineer", "DevOps Engineer"],
      approved: false,
      issues: [
        {
          title: "Design CLI architecture and command structure",
          description: "Define CLI commands, arguments, and configuration options. Plan for extensibility and different project types.",
          role: "Software Engineer"
        },
        {
          title: "Plan localhost UI architecture and component structure",
          description: "Design React component hierarchy, state management, and API communication patterns for the local UI.",
          role: "Software Engineer"
        },
        {
          title: "Design GitHub API integration strategy",
          description: "Plan authentication, rate limiting, and error handling for GitHub API interactions. Consider both REST and GraphQL approaches.",
          role: "DevOps Engineer"
        },
        {
          title: "Define 8-phase lifecycle and role mapping system",
          description: "Specify the standard 8 phases, default role assignments, and customization capabilities for different project domains.",
          role: "AI Architect"
        }
      ]
    },
    {
      id: "design",
      title: "UI/UX Design & Prototyping",
      description: "User interface design, prototyping, and user experience optimization",
      roles: ["Designer", "UX Researcher", "Product Owner"],
      approved: false,
      issues: [
        {
          title: "Create wireframes for the 3-step UI flow",
          description: "Design wireframes for Project Summary, Lifecycle Phases, and Review & Submit screens with responsive considerations.",
          role: "Designer"
        },
        {
          title: "Design phase configuration interface",
          description: "Create intuitive UI for role assignment, issue preview, and approval workflow. Focus on clarity and efficiency.",
          role: "Designer"
        },
        {
          title: "Develop visual identity and component library",
          description: "Establish color schemes, typography, icons, and reusable UI components that align with developer tool aesthetics.",
          role: "Designer"
        },
        {
          title: "Test usability with target developers",
          description: "Conduct usability testing sessions with developers to validate the workflow and identify improvement opportunities.",
          role: "UX Researcher"
        }
      ]
    },
    {
      id: "development",
      title: "Core Development",
      description: "Implementation of core features, CLI tool, and UI components",
      roles: ["Software Engineer", "AI Architect"],
      approved: false,
      issues: [
        {
          title: "Implement CLI foundation with Commander.js",
          description: "Build the core CLI structure, argument parsing, and project detection logic. Include help system and error handling.",
          role: "Software Engineer"
        },
        {
          title: "Build README.md parsing and project analysis",
          description: "Implement markdown parsing, project type detection, and automatic requirement extraction from repository content.",
          role: "AI Architect"
        },
        {
          title: "Develop React UI components and state management",
          description: "Build the localhost UI with React, implement state management, and create responsive components for all three workflow steps.",
          role: "Software Engineer"
        },
        {
          title: "Implement GitHub API integration",
          description: "Build GitHub authentication, epic/issue creation, labeling system, and error handling for API interactions.",
          role: "Software Engineer"
        },
        {
          title: "Create issue templating and SPARC optimization",
          description: "Implement intelligent issue generation with proper SPARC formatting, role assignment, and context inclusion.",
          role: "AI Architect"
        }
      ]
    },
    {
      id: "integration",
      title: "System Integration & Testing",
      description: "Integration testing, API connections, and end-to-end workflow validation",
      roles: ["Software Engineer", "QA Engineer", "DevOps Engineer"],
      approved: false,
      issues: [
        {
          title: "Implement end-to-end CLI to GitHub workflow",
          description: "Connect all components from CLI execution through UI interaction to GitHub push. Test complete user journey.",
          role: "Software Engineer"
        },
        {
          title: "Build comprehensive test suite",
          description: "Create unit tests, integration tests, and end-to-end tests covering CLI commands, UI interactions, and GitHub API calls.",
          role: "QA Engineer"
        },
        {
          title: "Test GitHub integration with various repository types",
          description: "Validate functionality across different repository structures, permissions, and GitHub configurations.",
          role: "DevOps Engineer"
        },
        {
          title: "Implement error handling and recovery mechanisms",
          description: "Build robust error handling for network issues, authentication failures, and malformed project data.",
          role: "Software Engineer"
        }
      ]
    },
    {
      id: "testing",
      title: "Quality Assurance & Testing",
      description: "Comprehensive testing, bug fixes, and quality validation",
      roles: ["QA Engineer", "Software Engineer"],
      approved: false,
      issues: [
        {
          title: "Execute comprehensive manual testing scenarios",
          description: "Test all user workflows, edge cases, and error conditions across different operating systems and Node.js versions.",
          role: "QA Engineer"
        },
        {
          title: "Perform cross-platform compatibility testing",
          description: "Validate CLI functionality on Windows, macOS, and Linux systems with different terminal environments.",
          role: "QA Engineer"
        },
        {
          title: "Test performance with large repositories",
          description: "Validate tool performance with large README files, complex project structures, and high issue counts.",
          role: "QA Engineer"
        },
        {
          title: "Security testing for GitHub integration",
          description: "Test authentication security, token handling, and ensure no sensitive data is exposed or logged.",
          role: "QA Engineer"
        }
      ]
    },
    {
      id: "deployment",
      title: "Deployment & Distribution",
      description: "NPM packaging, distribution setup, and deployment automation",
      roles: ["DevOps Engineer", "Software Engineer"],
      approved: false,
      issues: [
        {
          title: "Configure NPM package structure and metadata",
          description: "Set up package.json, prepare distribution files, and configure NPM publishing workflow with proper versioning.",
          role: "DevOps Engineer"
        },
        {
          title: "Build automated release pipeline",
          description: "Create CI/CD pipeline for automated testing, building, and NPM publishing with proper release management.",
          role: "DevOps Engineer"
        },
        {
          title: "Implement CLI installation and update mechanisms",
          description: "Ensure smooth global installation, auto-update notifications, and version management for end users.",
          role: "Software Engineer"
        },
        {
          title: "Set up monitoring and analytics",
          description: "Implement usage analytics, error reporting, and performance monitoring for the deployed CLI tool.",
          role: "DevOps Engineer"
        }
      ]
    },
    {
      id: "launch",
      title: "Launch & Documentation",
      description: "Documentation, marketing materials, and go-to-market preparation",
      roles: ["Content Writer", "Product Owner", "DevOps Engineer"],
      approved: false,
      issues: [
        {
          title: "Create comprehensive documentation and tutorials",
          description: "Write installation guide, usage examples, troubleshooting guide, and best practices documentation.",
          role: "Content Writer"
        },
        {
          title: "Develop CLI help system and command reference",
          description: "Build in-tool help system, command descriptions, and interactive guidance for new users.",
          role: "Content Writer"
        },
        {
          title: "Create demo videos and marketing materials",
          description: "Produce demonstration videos, feature highlights, and promotional content for developer community outreach.",
          role: "Content Writer"
        },
        {
          title: "Plan community launch strategy",
          description: "Develop launch timeline, community engagement plan, and feedback collection mechanisms for initial release.",
          role: "Product Owner"
        }
      ]
    }
  ]
};
