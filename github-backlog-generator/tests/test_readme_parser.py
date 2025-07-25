"""Unit tests for readme parser module."""

import pytest
from unittest.mock import Mock, patch

from github_backlog_generator.readme_parser import ReadmeParser


class TestReadmeParser:
    """Test cases for ReadmeParser class."""
    
    @pytest.fixture
    def readme_parser(self):
        """Create a ReadmeParser instance."""
        return ReadmeParser()
    
    @pytest.fixture
    def sample_readme_content(self):
        """Sample README content for testing."""
        return """# Awesome E-commerce Platform

A modern, scalable e-commerce platform built with cutting-edge technologies.

## Features
- User authentication and authorization
- Product catalog with search
- Shopping cart and checkout
- Payment processing with Stripe
- Real-time inventory management
- AI-powered product recommendations

## Tech Stack
- **Backend**: Node.js, Express.js, GraphQL
- **Database**: PostgreSQL, Redis
- **Frontend**: React, Next.js, TypeScript
- **Infrastructure**: Docker, Kubernetes, AWS

## Getting Started
1. Clone the repository
2. Install dependencies: `npm install`
3. Run migrations: `npm run migrate`
4. Start the server: `npm start`

## Architecture
The platform follows a microservices architecture with the following services:
- Auth Service: Handles user authentication
- Product Service: Manages product catalog
- Cart Service: Shopping cart operations
- Payment Service: Payment processing
- Recommendation Service: AI recommendations

## License
MIT"""
    
    @pytest.fixture
    def minimal_readme(self):
        """Minimal README content."""
        return """# Simple Project
A basic project with minimal information."""
    
    @pytest.fixture
    def ai_project_readme(self):
        """AI/ML focused project README."""
        return """# AI Assistant Platform

An intelligent assistant powered by large language models.

## Core Features
- Natural language understanding
- Multi-modal AI capabilities (text, image, voice)
- Prompt engineering interface
- Fine-tuning pipeline
- Real-time inference optimization

## ML Stack
- **Models**: GPT-4, Claude, LLaMA
- **Frameworks**: PyTorch, Transformers, LangChain
- **Vector DB**: Pinecone, Weaviate
- **Serving**: TensorRT, Triton
- **Monitoring**: Weights & Biases, MLflow

## Infrastructure
- GPU clusters on AWS
- Distributed training with Horovod
- Model versioning and A/B testing"""
    
    def test_parse_basic_readme(self, readme_parser, sample_readme_content):
        """Test parsing a standard README."""
        result = readme_parser.parse(sample_readme_content)
        
        # Check basic fields
        assert result['title'] == 'Awesome E-commerce Platform'
        assert result['description'] == 'A modern, scalable e-commerce platform built with cutting-edge technologies.'
        assert result['rawContent'] == sample_readme_content
        
        # Check features extraction
        assert 'features' in result
        features = result['features']
        assert len(features) >= 6
        assert any('authentication' in f.lower() for f in features)
        assert any('shopping cart' in f.lower() for f in features)
        assert any('ai' in f.lower() for f in features)
        
        # Check tech stack extraction
        assert 'techStack' in result
        tech_stack = result['techStack']
        assert 'Node.js' in tech_stack
        assert 'PostgreSQL' in tech_stack
        assert 'React' in tech_stack
        assert 'Docker' in tech_stack
        
        # Check domain inference
        assert result['domain'] == 'e-commerce'
    
    def test_parse_minimal_readme(self, readme_parser, minimal_readme):
        """Test parsing minimal README content."""
        result = readme_parser.parse(minimal_readme)
        
        assert result['title'] == 'Simple Project'
        assert result['description'] == 'A basic project with minimal information.'
        assert result['features'] == []
        assert result['techStack'] == []
        assert result['domain'] == 'general'
    
    def test_parse_ai_project(self, readme_parser, ai_project_readme):
        """Test parsing AI/ML project README."""
        result = readme_parser.parse(ai_project_readme)
        
        assert result['title'] == 'AI Assistant Platform'
        assert 'domain' in result
        assert result['domain'] == 'artificial-intelligence'
        
        # Check ML-specific tech stack
        tech_stack = result['techStack']
        assert 'PyTorch' in tech_stack
        assert 'LangChain' in tech_stack
        assert 'TensorRT' in tech_stack
        
        # Check features
        features = result['features']
        assert any('language understanding' in f.lower() for f in features)
        assert any('prompt engineering' in f.lower() for f in features)
    
    def test_extract_features(self, readme_parser):
        """Test feature extraction from different formats."""
        # Test bullet points
        content = """## Features
- Feature 1
- Feature 2
- Feature 3"""
        features = readme_parser._extract_features(content)
        assert len(features) == 3
        assert features[0] == 'Feature 1'
        
        # Test numbered list
        content = """## Features
1. First feature
2. Second feature
3. Third feature"""
        features = readme_parser._extract_features(content)
        assert len(features) == 3
        assert features[1] == 'Second feature'
        
        # Test mixed content
        content = """## What can it do?
- Parse documents
- Extract entities
Some additional text
- Generate summaries"""
        features = readme_parser._extract_features(content)
        assert len(features) >= 2
    
    def test_extract_tech_stack(self, readme_parser):
        """Test technology extraction."""
        content = """## Tech Stack
- Backend: Python, Django, FastAPI
- Frontend: Vue.js, Tailwind CSS
- Database: MongoDB, Redis
- DevOps: GitHub Actions, Terraform"""
        
        tech_stack = readme_parser._extract_tech_stack(content)
        
        assert 'Python' in tech_stack
        assert 'Django' in tech_stack
        assert 'Vue.js' in tech_stack
        assert 'MongoDB' in tech_stack
        assert 'Terraform' in tech_stack
    
    def test_extract_tech_from_badges(self, readme_parser):
        """Test extracting technologies from shield badges."""
        content = """# Project
![Python](https://img.shields.io/badge/Python-3.9-blue)
![Django](https://img.shields.io/badge/Django-4.0-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-blue)"""
        
        tech_stack = readme_parser._extract_tech_stack(content)
        
        assert 'Python' in tech_stack
        assert 'Django' in tech_stack
        assert 'PostgreSQL' in tech_stack
    
    def test_infer_domain(self, readme_parser):
        """Test domain inference from content."""
        # E-commerce indicators
        assert readme_parser._infer_domain("shopping cart checkout payment") == "e-commerce"
        assert readme_parser._infer_domain("product catalog inventory") == "e-commerce"
        
        # AI/ML indicators
        assert readme_parser._infer_domain("machine learning neural network") == "artificial-intelligence"
        assert readme_parser._infer_domain("LLM prompt engineering GPT") == "artificial-intelligence"
        
        # Data indicators
        assert readme_parser._infer_domain("ETL pipeline data warehouse") == "data-analytics"
        assert readme_parser._infer_domain("business intelligence dashboard") == "data-analytics"
        
        # Healthcare indicators
        assert readme_parser._infer_domain("patient records HIPAA medical") == "healthcare"
        assert readme_parser._infer_domain("electronic health records") == "healthcare"
        
        # FinTech indicators
        assert readme_parser._infer_domain("payment processing banking API") == "fintech"
        assert readme_parser._infer_domain("cryptocurrency blockchain wallet") == "fintech"
        
        # Default case
        assert readme_parser._infer_domain("generic project description") == "general"
    
    def test_parse_empty_content(self, readme_parser):
        """Test parsing empty or None content."""
        # Empty string
        result = readme_parser.parse("")
        assert result['title'] == 'Untitled Project'
        assert result['description'] == 'No description available'
        assert result['features'] == []
        assert result['techStack'] == []
        
        # None content
        result = readme_parser.parse(None)
        assert result['title'] == 'Untitled Project'
    
    def test_parse_no_title(self, readme_parser):
        """Test parsing README without H1 title."""
        content = """This is a project without a proper title.
        
## Features
- Feature 1
- Feature 2"""
        
        result = readme_parser.parse(content)
        assert result['title'] == 'Untitled Project'
        assert len(result['features']) == 2
    
    def test_case_insensitive_sections(self, readme_parser):
        """Test that section headers are matched case-insensitively."""
        content = """# Test Project
        
## FEATURES
- Feature 1

## tech stack
- Python

## Technology
- Docker"""
        
        result = readme_parser.parse(content)
        assert len(result['features']) > 0
        assert 'Python' in result['techStack']
        assert 'Docker' in result['techStack']
    
    def test_multiline_description(self, readme_parser):
        """Test extracting multiline descriptions."""
        content = """# My Project

This is a complex project that
spans multiple lines and includes
various technical details.

## Features
- Feature 1"""
        
        result = readme_parser.parse(content)
        assert "complex project" in result['description']
        assert "multiple lines" in result['description']