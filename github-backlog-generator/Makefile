.PHONY: test test-unit test-integration test-coverage install install-dev lint format clean init phases epics issues workflow-help

# Install dependencies
install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt
	pip install -e .

# Run all tests
test:
	pytest

# Run only unit tests
test-unit:
	pytest -m "not integration"

# Run only integration tests  
test-integration:
	pytest -m integration

# Run tests with coverage report
test-coverage:
	pytest --cov=github_backlog_generator --cov-report=html --cov-report=term

# Run specific test file
test-file:
	@read -p "Enter test file name (e.g., test_phase_generator.py): " file; \
	pytest tests/$$file -v

# Linting and formatting
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf *.egg-info/
	rm -rf dist/
	rm -rf build/

# Development workflow
dev: install-dev lint test

# Quick test during development
quick-test:
	pytest -x -v --tb=short

# Watch tests (requires pytest-watch)
watch:
	ptw -- -x -v --tb=short

# =============================================================================
# USER WORKFLOW COMMANDS
# =============================================================================

# Interactive project initialization
init:
	@echo "🚀 GitHub Backlog Generator - Project Initialization"
	@echo "=================================================="
	@echo ""
	@echo "Please provide your GitHub repository URL:"
	@read -p "GitHub URL (e.g., https://github.com/owner/repo): " repo_url; \
	if [ -z "$$repo_url" ]; then \
		echo "❌ Error: Repository URL is required"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "🔍 Initializing project: $$repo_url"; \
	echo "📋 This will analyze the README and set up project structure..."; \
	echo ""; \
	github-backlog init "$$repo_url" && \
	echo "" && \
	echo "✅ Project initialized successfully!" && \
	echo "📁 Project data saved to .backlog-* directory" && \
	echo "" && \
	echo "Next steps:" && \
	echo "  make phases  - Create GitHub milestones" && \
	echo "  make epics   - Generate epics for all phases" && \
	echo "  make issues  - Create issues for all epics"

# Create GitHub milestones for all phases
phases:
	@echo "🎯 Creating GitHub Milestones"
	@echo "============================="
	@echo ""
	@if [ ! -d .backlog-* ]; then \
		echo "❌ Error: No project initialized. Run 'make init' first."; \
		exit 1; \
	fi; \
	repo_url=$$(find .backlog-* -name "*.json" | head -1 | xargs grep -o '"repo_url":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo ""); \
	if [ -z "$$repo_url" ]; then \
		echo "Please provide your GitHub repository URL:"; \
		read -p "GitHub URL: " repo_url; \
	fi; \
	echo "🎯 Creating milestones for: $$repo_url"; \
	echo ""; \
	github-backlog milestones "$$repo_url" && \
	echo "" && \
	echo "✅ Milestones created successfully!" && \
	echo "" && \
	echo "Next step:" && \
	echo "  make epics - Generate epics for all phases"

# Generate epics for all phases
epics:
	@echo "📋 Generating Epics for All Phases"
	@echo "=================================="
	@echo ""
	@if [ ! -d .backlog-* ]; then \
		echo "❌ Error: No project initialized. Run 'make init' first."; \
		exit 1; \
	fi; \
	repo_url=$$(find .backlog-* -name "*.json" | head -1 | xargs grep -o '"repo_url":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo ""); \
	if [ -z "$$repo_url" ]; then \
		echo "Please provide your GitHub repository URL:"; \
		read -p "GitHub URL: " repo_url; \
	fi; \
	echo "📋 Generating epics for: $$repo_url"; \
	echo "⏳ This will create epic issues for all 8 phases..."; \
	echo ""; \
	github-backlog generate --all-epics "$$repo_url" && \
	echo "" && \
	echo "✅ Epics generated successfully!" && \
	echo "" && \
	echo "Next step:" && \
	echo "  make issues - Create detailed issues for all epics"

# Generate issues for all epics
issues:
	@echo "✅ Generating Issues for All Epics"
	@echo "=================================="
	@echo ""
	@if [ ! -d .backlog-* ]; then \
		echo "❌ Error: No project initialized. Run 'make init' first."; \
		exit 1; \
	fi; \
	repo_url=$$(find .backlog-* -name "*.json" | head -1 | xargs grep -o '"repo_url":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo ""); \
	if [ -z "$$repo_url" ]; then \
		echo "Please provide your GitHub repository URL:"; \
		read -p "GitHub URL: " repo_url; \
	fi; \
	echo "✅ Generating issues for: $$repo_url"; \
	echo "⏳ This will create detailed task issues for all epics..."; \
	echo "💡 This may take several minutes for large projects."; \
	echo ""; \
	for phase in 1 2 3 4 5 6 7 8; do \
		echo "📝 Processing Phase $$phase..."; \
		github-backlog generate --phase $$phase --all-epics "$$repo_url" || echo "⚠️  Phase $$phase completed with warnings"; \
	done && \
	echo "" && \
	echo "🎉 All issues generated successfully!" && \
	echo "" && \
	echo "📊 View your completed backlog:" && \
	echo "  github-backlog status $$repo_url"

# Display workflow help
workflow-help:
	@echo "🎼 GitHub Backlog Generator - Workflow Commands"
	@echo "==============================================="
	@echo ""
	@echo "Quick Start Workflow:"
	@echo "  make install    - Install dependencies"
	@echo "  make init       - Initialize project (interactive)"
	@echo "  make phases     - Create GitHub milestones"  
	@echo "  make epics      - Generate epics for all phases"
	@echo "  make issues     - Create issues for all epics"
	@echo ""
	@echo "Advanced Options:"
	@echo "  For custom workflows, see run.sh - an example orchestration script"
	@echo "  that demonstrates how to compose CLI commands with cost tracking,"
	@echo "  selective phase processing, and dry-run capabilities."
	@echo ""
	@echo "Prerequisites:"
	@echo "  export ANTHROPIC_API_KEY=your-anthropic-key"
	@echo "  export GITHUB_TOKEN=your-github-token"
	@echo ""
	@echo "Example Complete Workflow:"
	@echo "  make install && make init && make phases && make epics && make issues"