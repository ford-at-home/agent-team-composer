"""Phase JSON schema validation and handling."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from rich.console import Console

console = Console()


class PhaseSchemaError(Exception):
    """Exception raised for phase schema validation errors."""
    pass


class PhaseSchema:
    """Handles phase JSON schema validation and processing."""
    
    REQUIRED_FIELDS = ['title', 'description']
    OPTIONAL_FIELDS = ['id', 'dueDate', 'suggestedRoles', 'order']
    
    @classmethod
    def validate_phase(cls, phase: Dict[str, Any], phase_num: int) -> Dict[str, str]:
        """Validate a single phase object."""
        errors = []
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in phase or not phase[field]:
                errors.append(f"Phase {phase_num}: Missing required field '{field}'")
        
        # Validate field types
        if 'title' in phase and not isinstance(phase['title'], str):
            errors.append(f"Phase {phase_num}: 'title' must be a string")
            
        if 'description' in phase and not isinstance(phase['description'], str):
            errors.append(f"Phase {phase_num}: 'description' must be a string")
            
        if 'suggestedRoles' in phase and not isinstance(phase['suggestedRoles'], list):
            errors.append(f"Phase {phase_num}: 'suggestedRoles' must be a list")
            
        if 'order' in phase and not isinstance(phase['order'], int):
            errors.append(f"Phase {phase_num}: 'order' must be an integer")
        
        return errors
    
    @classmethod
    def validate_phases_json(cls, phases_data: Dict[str, Any]) -> List[str]:
        """Validate the entire phases.json structure."""
        errors = []
        
        # Check top-level structure
        if not isinstance(phases_data, dict):
            errors.append("Root must be a dictionary")
            return errors
            
        if 'phases' not in phases_data:
            errors.append("Missing 'phases' key in root object")
            return errors
            
        phases = phases_data['phases']
        if not isinstance(phases, list):
            errors.append("'phases' must be a list")
            return errors
            
        if len(phases) == 0:
            errors.append("'phases' list cannot be empty")
            return errors
        
        # Validate each phase
        for i, phase in enumerate(phases, 1):
            if not isinstance(phase, dict):
                errors.append(f"Phase {i}: Must be a dictionary")
                continue
                
            phase_errors = cls.validate_phase(phase, i)
            errors.extend(phase_errors)
        
        # Check for duplicate titles
        titles = [phase.get('title', '') for phase in phases]
        seen_titles = set()
        for i, title in enumerate(titles, 1):
            if title in seen_titles:
                errors.append(f"Phase {i}: Duplicate title '{title}'")
            seen_titles.add(title)
        
        return errors
    
    @classmethod
    def load_and_validate(cls, file_path: str) -> Dict[str, Any]:
        """Load and validate a phases.json file."""
        path = Path(file_path)
        
        if not path.exists():
            raise PhaseSchemaError(f"Phases file not found: {file_path}")
            
        if not path.is_file():
            raise PhaseSchemaError(f"Path is not a file: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise PhaseSchemaError(f"Invalid JSON in phases file: {e}")
        except Exception as e:
            raise PhaseSchemaError(f"Error reading phases file: {e}")
        
        # Validate schema
        errors = cls.validate_phases_json(data)
        if errors:
            error_msg = "Phase JSON validation errors:\n" + "\n".join(f"  - {error}" for error in errors)
            raise PhaseSchemaError(error_msg)
        
        return data
    
    @classmethod
    def normalize_phases(cls, phases_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize phases data to internal format."""
        phases = phases_data['phases']
        normalized = []
        
        for i, phase in enumerate(phases, 1):
            # Create normalized phase with defaults
            normalized_phase = {
                'number': phase.get('order', i),
                'title': phase['title'],
                'description': phase['description'],
                'id': phase.get('id', cls._generate_id(phase['title'])),
                'dueDate': phase.get('dueDate', cls._generate_due_date(i)),
                'suggestedRoles': phase.get('suggestedRoles', [])
            }
            normalized.append(normalized_phase)
        
        # Sort by order/number
        normalized.sort(key=lambda x: x['number'])
        
        # Renumber to ensure sequential
        for i, phase in enumerate(normalized, 1):
            phase['number'] = i
            
        return normalized
    
    @classmethod
    def _generate_id(cls, title: str) -> str:
        """Generate a phase ID from title."""
        return title.lower().replace(' ', '-').replace('&', 'and')
    
    @classmethod
    def _generate_due_date(cls, phase_num: int) -> str:
        """Generate a due date for a phase."""
        return (datetime.now() + timedelta(days=phase_num * 14)).isoformat()
    
    @classmethod
    def create_sample_phases_json(cls, output_path: Optional[str] = None) -> str:
        """Create a sample phases.json file."""
        sample_data = {
            "phases": [
                {
                    "title": "Discovery & Planning",
                    "description": "Requirements gathering and feasibility analysis",
                    "order": 1,
                    "suggestedRoles": ["analyst", "product_owner"]
                },
                {
                    "title": "Design & Architecture", 
                    "description": "System design and technical planning",
                    "order": 2,
                    "suggestedRoles": ["architect", "designer"]
                },
                {
                    "title": "Development Setup",
                    "description": "Environment and tooling configuration",
                    "order": 3,
                    "suggestedRoles": ["devops", "developer"]
                },
                {
                    "title": "Core Development",
                    "description": "Main feature implementation",
                    "order": 4,
                    "suggestedRoles": ["developer", "tech_lead"]
                },
                {
                    "title": "Testing & QA",
                    "description": "Quality assurance and testing",
                    "order": 5,
                    "suggestedRoles": ["qa_engineer", "developer"]
                },
                {
                    "title": "Documentation",
                    "description": "User and technical documentation",
                    "order": 6,
                    "suggestedRoles": ["technical_writer", "developer"]
                },
                {
                    "title": "Deployment",
                    "description": "Production deployment and DevOps",
                    "order": 7,
                    "suggestedRoles": ["devops", "sre"]
                },
                {
                    "title": "Maintenance & Growth",
                    "description": "Ongoing improvements and scaling",
                    "order": 8,
                    "suggestedRoles": ["developer", "product_owner"]
                }
            ],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "description": "Sample phases configuration for GitHub Backlog Generator"
            }
        }
        
        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
            
            return str(path)
        else:
            return json.dumps(sample_data, indent=2, ensure_ascii=False)
    
    @classmethod
    def display_phases_summary(cls, phases: List[Dict[str, Any]]) -> None:
        """Display a summary of loaded phases."""
        console.print("\n[bold]Loaded Phases:[/bold]\n")
        
        from rich.table import Table
        table = Table(show_header=True)
        table.add_column("Phase", style="cyan", width=5)
        table.add_column("Title", style="green", width=30)
        table.add_column("Description", style="dim", width=50)
        table.add_column("Roles", style="yellow", width=20)
        
        for phase in phases:
            roles_str = ", ".join(phase.get('suggestedRoles', [])[:3])
            if len(phase.get('suggestedRoles', [])) > 3:
                roles_str += "..."
                
            table.add_row(
                str(phase['number']),
                phase['title'],
                phase['description'][:47] + "..." if len(phase['description']) > 50 else phase['description'],
                roles_str
            )
        
        console.print(table)
        console.print(f"\n[green]✓[/green] Loaded {len(phases)} phases successfully")


def load_phases_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Convenience function to load and normalize phases from a file."""
    try:
        raw_data = PhaseSchema.load_and_validate(file_path)
        phases = PhaseSchema.normalize_phases(raw_data)
        return phases
    except PhaseSchemaError as e:
        console.print(f"[red]Error loading phases file:[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error loading phases file:[/red] {e}")
        raise PhaseSchemaError(f"Unexpected error: {e}")