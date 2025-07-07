# Agent Team Composer - Architecture Diagrams

## 1. Deployment & CI/CD Pipeline

```mermaid
graph TB
    subgraph "Development"
        DEV[Developer] -->|git push| GH[GitHub Repository]
    end

    subgraph "GitHub Actions CI/CD"
        GH -->|PR/Push| CI[CI Pipeline]
        CI -->|Matrix| CI18[Node 18.x Tests]
        CI -->|Matrix| CI20[Node 20.x Tests]

        CI18 --> LINT[ESLint]
        CI20 --> LINT
        LINT --> TC[TypeCheck]
        TC --> TEST[Unit Tests]
        TEST --> BUILD[Build Package]
        BUILD --> VAL[Validate Build]
        VAL --> INT[Integration Tests]

        GH -->|PR Merged to main| AR[Auto Release Workflow]
        AR --> VB[Version Bump]
        VB -->|Labels| MAJ[Major]
        VB -->|Labels| MIN[Minor]
        VB -->|Default| PATCH[Patch]

        VB --> CL[Update CHANGELOG]
        CL --> NPM[NPM Publish]
        NPM --> GR[GitHub Release]
        GR --> COMMENT[PR Comment]
    end

    subgraph "Distribution"
        NPM --> NPMREG[NPM Registry]
        NPMREG --> USER1[npm install -g]
        NPMREG --> USER2[npx usage]

        GH -->|Dockerfile| DOCKER[Docker Build]
        DOCKER --> DHUB[Docker Hub]
        DHUB --> DPROD[Production Deploy]
    end

    subgraph "Package Structure"
        BUILD --> DIST[dist/]
        DIST --> DISTCLI[cli/]
        DIST --> DISTSER[server/]
        DIST --> DISTUI[index.html + assets]
        DIST --> TYPES[TypeScript Definitions]
    end
```

## 2. Networking & API Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        BROWSER[Web Browser]
        CLI[CLI Tool]
    end

    subgraph "Application Server"
        EXPRESS[Express Server :3000]

        subgraph "API Endpoints"
            HEALTH[GET /api/health]
            PROJ[GET/PUT /api/project]
            GEN[POST /api/generate-plan]
            GHAUTH[GET /api/github/auth]
            GHREPO[GET /api/github/repositories]
            GHBRANCH[GET /api/github/branches]
            GHISSUE[POST /api/github/create-issues]
        end

        subgraph "Middleware"
            CORS[CORS Handler]
            ERROR[Error Handler]
            JSON[JSON Parser]
        end
    end

    subgraph "External Services"
        CLAUDE[Anthropic Claude API]
        GITHUB[GitHub API]

        CLAUDE -->|Response| LLMRESP[Project Plan JSON]
        GITHUB -->|Response| GHRESP[Issues/Repos Data]
    end

    subgraph "Data Flow"
        BROWSER -->|HTTP/WS| EXPRESS
        CLI -->|Spawn Process| EXPRESS

        EXPRESS -->|API Key Auth| CLAUDE
        EXPRESS -->|OAuth/Token| GITHUB

        GEN -->|README Content| CLAUDE
        GHISSUE -->|Issues Data| GITHUB
        GHREPO -->|List Repos| GITHUB
    end

    subgraph "Security Layer"
        SANITIZE[Prompt Sanitizer]
        VALIDATE[Input Validation]
        RATELIMIT[Rate Limiting]

        GEN --> SANITIZE
        SANITIZE --> CLAUDE
        GHISSUE --> VALIDATE
        VALIDATE --> GITHUB
    end
```

## 3. System Architecture & Components

```mermaid
graph TB
    subgraph "Frontend - React SPA"
        UI[UI Layer]
        COMP[Components]
        HOOKS[Custom Hooks]

        UI --> PROJECT[ProjectSummary]
        UI --> PHASES[LifecyclePhases]
        UI --> REVIEW[ReviewSubmit]
        UI --> NAV[Navigation]

        HOOKS --> USEPROJ[useProjectData]
        HOOKS --> USETOAST[useToast]
        HOOKS --> USEACCESS[useAccessibility]

        COMP -->|State| STORE[React Query Cache]
        STORE -->|API Calls| API
    end

    subgraph "Backend Services"
        API[REST API Layer]

        subgraph "Core Services"
            LLM[LLM Orchestrator]
            GHS[GitHub Service]
            README[README Parser]
            PROMPT[Prompt Sanitizer]
            ENV[Environment Service]
        end

        API --> LLM
        API --> GHS
        API --> README

        LLM -->|Sanitized| PROMPT
        LLM -->|3 Cascade Calls| ANTHROPIC[Claude API]
    end

    subgraph "CLI Layer"
        CMD[Commander.js]
        INIT[init command]
        VAL[validate command]

        CMD --> INIT
        CMD --> VAL

        INIT -->|1. Check Env| ENV
        INIT -->|2. Parse README| README
        INIT -->|3. Start Server| SERVER[Express Server]
        INIT -->|4. Open Browser| BROWSER
    end

    subgraph "Data Models"
        METADATA[Project Metadata]
        PLAN[Project Plan]
        PHASE[Phase Model]
        EPIC[Epic Model]
        ISSUE[Issue Model]

        README -->|Extract| METADATA
        METADATA -->|Generate| PLAN
        PLAN -->|Contains| PHASE
        PHASE -->|Contains| EPIC
        EPIC -->|Contains| ISSUE
    end

    subgraph "Storage"
        TEMP[Temp JSON File]
        GIT[Git Repository]

        API -->|Read/Write| TEMP
        GHS -->|Push Issues| GIT
    end
```

## 4. User Workflow & Usage in the Wild

```mermaid
graph TB
    subgraph "User Journey"
        START[User with README.md]
        INSTALL[npx agent-team-composer init]

        START --> INSTALL
        INSTALL --> CHECK{Environment OK?}

        CHECK -->|No API Key| FAIL1[Error: Missing ANTHROPIC_API_KEY]
        CHECK -->|No GitHub| WARN[Warning: GitHub CLI Optional]
        CHECK -->|All Good| PARSE

        PARSE[Parse README.md]
        PARSE --> META[Extract Metadata]
        META --> AI[Claude Generates Plan]

        AI -->|Phase 1| P1[Generate Phases]
        P1 -->|Phase 2| P2[Generate Epics]
        P2 -->|Phase 3| P3[Format Issues]

        P3 --> BROWSER[Browser Opens localhost:3000]
    end

    subgraph "Web UI Wizard"
        BROWSER --> STEP1[1. Parse Product]
        STEP1 -->|Review/Edit| STEP2[2. Sprint View]
        STEP2 -->|Approve Phases| STEP3[3. Epic View]
        STEP3 -->|Review Roles| STEP4[4. Issues View]
        STEP4 -->|Final Review| STEP5[5. GitHub Sync]

        STEP5 --> SELECTREPO[Select Repository]
        SELECTREPO --> SELECTBRANCH[Select Branch]
        SELECTBRANCH --> PUSH[Push to GitHub]
    end

    subgraph "GitHub Integration"
        PUSH --> GHAPI[GitHub API]
        GHAPI --> CREATEISSUES[Create Issues]
        GHAPI --> CREATEEPICS[Create Epics]

        CREATEISSUES --> LABELS[Add Labels]
        LABELS --> SPARC[sparc-enabled:true]
        LABELS --> ROLE[role:developer]
        LABELS --> PHASE[phase:implementation]
        LABELS --> EPICREF[epic:epic-id]
    end

    subgraph "SPARC Agent Execution"
        SPARC --> CLAUDEFLOW[Claude Flow SPARC]
        CLAUDEFLOW --> AGENTS[AI Agents]

        AGENTS --> DEV[Developer Agent]
        AGENTS --> TEST[Tester Agent]
        AGENTS --> REVIEW[Reviewer Agent]

        DEV -->|Works on| ISSUE1[Issue #1]
        TEST -->|Tests| ISSUE2[Issue #2]
        REVIEW -->|Reviews| PR[Pull Requests]
    end

    subgraph "Success Metrics"
        PUSH --> SUCCESS[✓ Created X Epics]
        SUCCESS --> METRICS[✓ Created Y Issues]
        METRICS --> ROLES[✓ Assigned Z Roles]
        ROLES --> READY[Ready for SPARC Execution]
    end
```

## Key Insights

### Architecture Highlights

- **Modular Design**: Clear separation between CLI, API, UI, and services
- **AI-Powered**: Claude 3 Sonnet generates comprehensive project plans
- **Progressive Enhancement**: Works with just Anthropic API, GitHub integration optional
- **SPARC-Ready**: Output formatted for autonomous agent execution

### Deployment Features

- **Zero Config**: Works with `npx` without installation
- **Multi-Platform**: NPM package, Docker container, or source
- **Automated Releases**: Semantic versioning with changelog generation
- **Matrix Testing**: Ensures compatibility across Node versions

### Networking & Security

- **API Gateway Pattern**: Express server handles all external API calls
- **Security Layers**: Input sanitization, prompt injection prevention
- **Graceful Degradation**: Continues working if optional services unavailable
- **Stateless Design**: Temporary storage cleared on completion

### Real-World Usage

- **Rapid Project Planning**: README → Full project plan in minutes
- **Agent Team Coordination**: Automatic role assignment for AI agents
- **GitHub-Native**: Creates issues/epics directly in repositories
- **Iterative Workflow**: Review and customize at each step
