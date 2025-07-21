"""README Parser - Extracts project information from README files."""

import re
from pathlib import Path
from typing import Dict, List, Optional


class ReadmeParser:
    """Parser for extracting structured information from README files."""
    
    def __init__(self):
        self.tech_keywords = [
            'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt', 'gatsby',
            'node.js', 'express', 'fastify', 'nestjs', 'django', 'flask', 'rails',
            'typescript', 'javascript', 'python', 'ruby', 'java', 'go', 'rust',
            'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'dynamodb',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'vercel', 'netlify'
        ]
        
        self.domain_patterns = {
            'web': r'web|website|webapp|frontend|backend|fullstack',
            'mobile': r'mobile|ios|android|react native|flutter',
            'ai': r'ai|machine learning|ml|artificial intelligence|neural|llm',
            'data': r'data|analytics|etl|warehouse|pipeline|processing',
            'api': r'api|rest|graphql|microservice|service',
            'enterprise': r'enterprise|business|erp|crm|b2b',
            'saas': r'saas|software as a service|subscription|cloud',
            'cli': r'cli|command line|terminal|console',
            'game': r'game|gaming|unity|unreal|godot',
            'iot': r'iot|internet of things|embedded|sensor',
            'blockchain': r'blockchain|crypto|web3|smart contract',
            'other': r'.*'
        }
        
        self.complexity_keywords = [
            'microservices', 'distributed', 'scalable', 'real-time', 'enterprise',
            'multi-tenant', 'high availability', 'fault tolerant', 'kubernetes',
            'machine learning', 'ai', 'blockchain', 'big data'
        ]
    
    def parse_readme_file(self, file_path: str) -> Dict[str, any]:
        """Parse a README file from disk."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_readme_content(content)
    
    def parse_readme_content(self, content: str) -> Dict[str, any]:
        """Parse README content and extract structured information."""
        title = self._extract_title(content)
        description = self._extract_description(content)
        features = self._extract_features(content)
        tech_stack = self._extract_tech_stack(content)
        domain = self._detect_domain(content)
        complexity = self._assess_complexity(content, features, tech_stack)
        
        return {
            'title': title,
            'description': description,
            'features': features,
            'techStack': tech_stack,
            'domain': domain,
            'complexity': complexity,
            'rawContent': content
        }
    
    def _extract_title(self, content: str) -> str:
        """Extract the project title from README."""
        match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        return match.group(1).strip() if match else 'Untitled Project'
    
    def _extract_description(self, content: str) -> str:
        """Extract the project description from README."""
        lines = content.split('\n')
        start_index = -1
        
        # Find the first H1 heading
        for i, line in enumerate(lines):
            if re.match(r'^#\s+', line):
                start_index = i
                break
        
        if start_index == -1:
            start_index = 0
        
        description = []
        for i in range(start_index + 1, len(lines)):
            if re.match(r'^##\s+', lines[i]):
                break
            if lines[i].strip():
                description.append(lines[i].strip())
        
        return ' '.join(description) if description else 'No description provided'
    
    def _extract_features(self, content: str) -> List[str]:
        """Extract features from README."""
        feature_patterns = [
            r'## Features?\n((?:[-*] .+?(?:\n|$))+)',
            r'## What (?:does|can) .+?\n((?:[-*] .+?(?:\n|$))+)',
            r'## Functionality\n((?:[-*] .+?(?:\n|$))+)',
            r'## Key Features?\n((?:[-*] .+?(?:\n|$))+)'
        ]
        
        for pattern in feature_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                features = match.group(1).split('\n')
                features = [f.strip().lstrip('*- ') for f in features if f.strip()]
                return [f for f in features if f]
        
        return []
    
    def _extract_tech_stack(self, content: str) -> List[str]:
        """Extract technology stack from README."""
        tech_stack = set()
        
        # Check for explicit tech stack sections
        tech_patterns = [
            r'## Tech(?:nology)? Stack\n((?:[-*] .+?(?:\n|$))+)',
            r'## Built With\n((?:[-*] .+?(?:\n|$))+)',
            r'## Technologies\n((?:[-*] .+?(?:\n|$))+)'
        ]
        
        for pattern in tech_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                items = match.group(1).split('\n')
                items = [item.strip().lstrip('*- ') for item in items if item.strip()]
                tech_stack.update(items)
        
        # Scan for keywords
        content_lower = content.lower()
        for keyword in self.tech_keywords:
            if keyword in content_lower:
                tech_stack.add(keyword.replace('.', '').title())
        
        return list(tech_stack)
    
    def _detect_domain(self, content: str) -> str:
        """Detect the project domain from README content."""
        scores = {}
        
        for domain, pattern in self.domain_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            scores[domain] = len(matches)
        
        # Find domain with highest score
        max_score = max(scores.values())
        if max_score == 0:
            return 'other'
        
        for domain, score in scores.items():
            if score == max_score and domain != 'other':
                return domain
        
        return 'other'
    
    def _assess_complexity(self, content: str, features: List[str], tech_stack: List[str]) -> str:
        """Assess project complexity based on various factors."""
        score = 0
        
        # Feature count
        if len(features) > 10:
            score += 3
        elif len(features) > 5:
            score += 2
        elif len(features) > 0:
            score += 1
        
        # Tech stack diversity
        if len(tech_stack) > 8:
            score += 3
        elif len(tech_stack) > 4:
            score += 2
        elif len(tech_stack) > 0:
            score += 1
        
        # Complexity keywords
        content_lower = content.lower()
        for keyword in self.complexity_keywords:
            if keyword in content_lower:
                score += 1
        
        # Integration mentions
        integration_matches = re.findall(r'integrat(?:e|ion|ing)', content, re.IGNORECASE)
        if len(integration_matches) > 5:
            score += 2
        elif len(integration_matches) > 2:
            score += 1
        
        if score >= 8:
            return 'complex'
        elif score >= 4:
            return 'moderate'
        else:
            return 'simple'