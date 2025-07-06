#!/bin/bash

echo "Creating labels for Agent Team Composer..."

# Epic labels
gh label create "epic" --description "Epic issue containing multiple tasks" --color "5319E7"

# Priority labels
gh label create "priority:high" --description "High priority" --color "D93F0B"
gh label create "priority:medium" --description "Medium priority" --color "FBCA04"
gh label create "priority:low" --description "Low priority" --color "0E8A16"

# Component labels
gh label create "ui" --description "User interface related" --color "7057FF"
gh label create "github" --description "GitHub integration" --color "0366D6"
gh label create "ai" --description "AI/LLM integration" --color "006B75"
gh label create "devops" --description "DevOps and deployment" --color "C2E0C6"
gh label create "security" --description "Security related" --color "EE0701"
gh label create "integration" --description "Integration work" --color "1D76DB"
gh label create "sparc" --description "SPARC optimization" --color "B60205"

# Phase labels
gh label create "phase:development" --description "Development phase" --color "BFDADC"
gh label create "phase:deployment" --description "Deployment phase" --color "D4C5F9"

# Role labels
gh label create "role:frontend" --description "Frontend developer task" --color "C5DEF5"
gh label create "role:backend" --description "Backend developer task" --color "BFD4F2"
gh label create "role:fullstack" --description "Full-stack developer task" --color "F9D0C4"
gh label create "role:devops" --description "DevOps engineer task" --color "FEF2C0"
gh label create "role:ai-engineer" --description "AI engineer task" --color "D2DAE1"

# SPARC labels
gh label create "sparc-enabled:true" --description "Optimized for SPARC agents" --color "0E8A16"

# Sprint labels
gh label create "sprint:1" --description "Sprint 1" --color "D876E3"
gh label create "sprint:2" --description "Sprint 2" --color "D876E3"
gh label create "sprint:3" --description "Sprint 3" --color "D876E3"

echo "✨ Labels created!"