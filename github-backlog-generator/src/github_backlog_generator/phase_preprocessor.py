"""Phase preprocessing via LLM evaluation."""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from rich.console import Console

console = Console()


class PhasePreprocessor:
    """Handles LLM-based phase preprocessing and optimization."""
    
    def __init__(self, api_key: str, model: str = 'claude-3-5-sonnet-20241022'):
        self.api_key = api_key
        self.model = model
        self._anthropic_client = None
    
    @property
    def anthropic_client(self):
        """Lazy load Anthropic client."""
        if self._anthropic_client is None:
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._anthropic_client
    
    def should_preprocess_phase(self, phase_number: int) -> bool:
        """Determine if a phase should be preprocessed."""
        return phase_number > 1
    
    def build_preprocessing_prompt(
        self, 
        current_phase: Dict[str, Any],
        prior_phases: List[Dict[str, Any]],
        project_context: Optional[Dict[str, Any]] = None,
        prior_epics: Optional[List[Dict[str, Any]]] = None,
        prior_issues: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build the LLM prompt for phase preprocessing."""
        
        prompt_parts = [
            "# Phase Preprocessing Analysis",
            "",
            "You are an expert project manager analyzing a software development project's phase structure.",
            "Based on the prior phases and their content, evaluate whether the current phase needs modifications.",
            "",
            "## Project Context"
        ]
        
        if project_context:
            prompt_parts.extend([
                f"**Project Title:** {project_context.get('title', 'Unknown')}",
                f"**Domain:** {project_context.get('domain', 'Unknown')}",
                f"**Complexity:** {project_context.get('complexity', 'Unknown')}",
                ""
            ])
        
        # Add prior phases context
        prompt_parts.extend([
            "## Prior Phases Completed",
            ""
        ])
        
        for i, phase in enumerate(prior_phases, 1):
            prompt_parts.extend([
                f"### {i}. {phase['title']}",
                f"**Description:** {phase['description']}",
                f"**Suggested Roles:** {', '.join(phase.get('suggestedRoles', []))}",
                ""
            ])
        
        # Add prior epics/issues if available
        if prior_epics:
            prompt_parts.extend([
                "## Prior Epics Generated",
                ""
            ])
            for epic in prior_epics[:5]:  # Limit to first 5 for brevity
                prompt_parts.append(f"- {epic.get('title', 'Untitled Epic')}")
            if len(prior_epics) > 5:
                prompt_parts.append(f"... and {len(prior_epics) - 5} more epics")
            prompt_parts.append("")
        
        if prior_issues:
            prompt_parts.extend([
                "## Recent Issues Generated",
                ""
            ])
            for issue in prior_issues[:10]:  # Limit to first 10 for brevity
                prompt_parts.append(f"- {issue.get('title', 'Untitled Issue')}")
            if len(prior_issues) > 10:
                prompt_parts.append(f"... and {len(prior_issues) - 10} more issues")
            prompt_parts.append("")
        
        # Add current phase to evaluate
        prompt_parts.extend([
            "## Current Phase to Evaluate",
            "",
            f"**Phase {current_phase['number']}: {current_phase['title']}**",
            f"**Current Description:** {current_phase['description']}",
            f"**Current Suggested Roles:** {', '.join(current_phase.get('suggestedRoles', []))}",
            "",
            "## Analysis Request",
            "",
            "Based on the prior phases and their outcomes, analyze this current phase and determine:",
            "",
            "1. **Relevance**: Is this phase still relevant given what came before?",
            "2. **Timing**: Is this the right time for this phase in the sequence?",
            "3. **Scope**: Should the description be refined based on prior work?",
            "4. **Resources**: Are the suggested roles appropriate given the project evolution?",
            "5. **Dependencies**: Are there new dependencies or prerequisites that should be reflected?",
            "",
            "## Response Format",
            "",
            "Respond with JSON in this exact format:",
            "",
            "```json",
            "{",
            '  "needs_modification": true/false,',
            '  "reasoning": "Brief explanation of why modifications are/aren\'t needed",',
            '  "modifications": {',
            '    "title": "Updated title (only if changed)",',
            '    "description": "Updated description (only if changed)",',
            '    "suggestedRoles": ["role1", "role2"] // only if changed',
            "  }",
            "}",
            "```",
            "",
            "**Important Guidelines:**",
            "- Only suggest modifications if they genuinely improve the phase based on prior context",
            "- Preserve the core intent of the original phase",
            "- Ensure modifications align with the overall project flow",
            "- If no changes are needed, set needs_modification to false and leave modifications empty",
            "",
            "Analyze the phase now:"
        ])
        
        return "\n".join(prompt_parts)
    
    def call_llm_for_preprocessing(self, prompt: str) -> Dict[str, Any]:
        """Call the LLM with the preprocessing prompt."""
        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,  # Lower temperature for more consistent analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text.strip()
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in LLM response")
            
            json_text = response_text[json_start:json_end]
            result = json.loads(json_text)
            
            # Validate response structure
            required_keys = ['needs_modification', 'reasoning']
            for key in required_keys:
                if key not in result:
                    raise ValueError(f"Missing required key '{key}' in LLM response")
            
            return result
            
        except json.JSONDecodeError as e:
            console.print(f"[red]Failed to parse LLM JSON response:[/red] {e}")
            console.print(f"[dim]Raw response:[/dim] {response_text}")
            raise
        except Exception as e:
            console.print(f"[red]LLM preprocessing call failed:[/red] {e}")
            raise
    
    def preprocess_phase(
        self,
        current_phase: Dict[str, Any],
        prior_phases: List[Dict[str, Any]],
        project_context: Optional[Dict[str, Any]] = None,
        prior_epics: Optional[List[Dict[str, Any]]] = None,
        prior_issues: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Preprocess a phase using LLM evaluation."""
        
        phase_number = current_phase['number']
        
        if not self.should_preprocess_phase(phase_number):
            console.print(f"[dim]Phase {phase_number}: Skipping preprocessing (first phase)[/dim]")
            return current_phase
        
        console.print(f"[cyan]Phase {phase_number}: Analyzing phase with LLM...[/cyan]")
        
        # Build the preprocessing prompt
        prompt = self.build_preprocessing_prompt(
            current_phase=current_phase,
            prior_phases=prior_phases,
            project_context=project_context,
            prior_epics=prior_epics,
            prior_issues=prior_issues
        )
        
        try:
            # Call LLM for analysis
            analysis_result = self.call_llm_for_preprocessing(prompt)
            
            needs_modification = analysis_result.get('needs_modification', False)
            reasoning = analysis_result.get('reasoning', 'No reasoning provided')
            modifications = analysis_result.get('modifications', {})
            
            console.print(f"[dim]LLM Analysis:[/dim] {reasoning}")
            
            if needs_modification and modifications:
                # Apply modifications to the phase
                updated_phase = current_phase.copy()
                
                changes_made = []
                for field, new_value in modifications.items():
                    if field in updated_phase and new_value != updated_phase[field]:
                        old_value = updated_phase[field]
                        updated_phase[field] = new_value
                        changes_made.append(f"{field}: '{old_value}' → '{new_value}'")
                
                if changes_made:
                    console.print(f"[green]Phase {phase_number}: Applied {len(changes_made)} modifications[/green]")
                    for change in changes_made:
                        console.print(f"[dim]  - {change}[/dim]")
                    
                    # Add preprocessing metadata
                    updated_phase['preprocessing'] = {
                        'processed_at': datetime.now().isoformat(),
                        'reasoning': reasoning,
                        'modifications_applied': modifications,
                        'original_phase': current_phase
                    }
                    
                    return updated_phase
                else:
                    console.print(f"[yellow]Phase {phase_number}: No actual changes needed[/yellow]")
                    return current_phase
            else:
                console.print(f"[green]Phase {phase_number}: No modifications needed[/green]")
                return current_phase
                
        except Exception as e:
            console.print(f"[red]Phase {phase_number}: Preprocessing failed, using original phase[/red]")
            console.print(f"[dim]Error: {e}[/dim]")
            return current_phase
    
    def preprocess_all_phases(
        self,
        phases: List[Dict[str, Any]],
        project_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Preprocess all phases in sequence, using prior phases as context."""
        
        processed_phases = []
        
        for i, phase in enumerate(phases):
            if i == 0:
                # First phase - no preprocessing
                processed_phases.append(phase)
            else:
                # Preprocess based on all prior phases  
                prior_phases = processed_phases  # Use already processed phases
                
                # Note: prior_epics and prior_issues would be loaded from state
                # For now, we'll preprocess based on phases only
                preprocessed_phase = self.preprocess_phase(
                    current_phase=phase,
                    prior_phases=prior_phases,
                    project_context=project_context
                )
                
                processed_phases.append(preprocessed_phase)
        
        return processed_phases


def preprocess_phases_with_llm(
    phases: List[Dict[str, Any]],
    api_key: str,
    project_context: Optional[Dict[str, Any]] = None,
    model: str = 'claude-3-5-sonnet-20241022'
) -> List[Dict[str, Any]]:
    """Convenience function to preprocess phases with LLM."""
    
    preprocessor = PhasePreprocessor(api_key=api_key, model=model)
    return preprocessor.preprocess_all_phases(phases, project_context)