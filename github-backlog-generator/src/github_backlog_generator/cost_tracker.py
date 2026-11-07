"""Cost and timing tracking utilities for CLI operations."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class APICall:
    """Represents a single API call with cost and timing data."""
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    duration: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OperationSummary:
    """Summary of costs and timing for an operation."""
    operation: str
    total_calls: int
    total_cost: float
    total_duration: float
    total_input_tokens: int
    total_output_tokens: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CostTracker:
    """Tracks API costs and timing for CLI operations."""
    
    # Anthropic Claude API Pricing (per 1M tokens)
    MODEL_PRICING = {
        'claude-3-5-sonnet-20241022': {'input': 3.0, 'output': 15.0},
        'claude-3-5-haiku-20241022': {'input': 0.8, 'output': 4.0},
        'claude-sonnet-4-20250514': {'input': 3.0, 'output': 15.0},
    }
    
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir
        self.api_calls: List[APICall] = []
        self.session_start = time.time()
        
        # Load existing tracking data if available
        if project_dir:
            self.tracking_file = project_dir / "cost_tracking.json"
            self._load_tracking_data()
        else:
            self.tracking_file = None
    
    def _load_tracking_data(self):
        """Load existing tracking data from file."""
        if self.tracking_file and self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    data = json.load(f)
                    self.api_calls = [
                        APICall(**call_data) 
                        for call_data in data.get('api_calls', [])
                    ]
            except Exception:
                # If loading fails, start fresh
                self.api_calls = []
    
    def _save_tracking_data(self):
        """Save tracking data to file."""
        if not self.tracking_file:
            return
            
        self.tracking_file.parent.mkdir(exist_ok=True)
        
        data = {
            'project_start': datetime.now().isoformat(),
            'api_calls': [call.to_dict() for call in self.api_calls],
            'total_cost': self.get_total_cost(),
            'total_calls': len(self.api_calls),
        }
        
        with open(self.tracking_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API call."""
        if model not in self.MODEL_PRICING:
            # Default to sonnet pricing
            model = 'claude-3-5-sonnet-20241022'
        
        pricing = self.MODEL_PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        
        return input_cost + output_cost
    
    def track_api_call(self, operation: str, model: str, input_tokens: int, 
                      output_tokens: int, duration: float):
        """Track a single API call."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        api_call = APICall(
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            duration=duration,
            timestamp=datetime.now().isoformat()
        )
        
        self.api_calls.append(api_call)
        self._save_tracking_data()
    
    def get_total_cost(self) -> float:
        """Get total cost for all tracked calls."""
        return sum(call.cost for call in self.api_calls)
    
    def get_total_duration(self) -> float:
        """Get total duration for all tracked calls."""
        return sum(call.duration for call in self.api_calls)
    
    def get_operation_summary(self) -> List[OperationSummary]:
        """Get summary by operation type."""
        operations = {}
        
        for call in self.api_calls:
            if call.operation not in operations:
                operations[call.operation] = {
                    'calls': 0,
                    'cost': 0.0,
                    'duration': 0.0,
                    'input_tokens': 0,
                    'output_tokens': 0
                }
            
            op = operations[call.operation]
            op['calls'] += 1
            op['cost'] += call.cost
            op['duration'] += call.duration
            op['input_tokens'] += call.input_tokens
            op['output_tokens'] += call.output_tokens
        
        return [
            OperationSummary(
                operation=op_name,
                total_calls=data['calls'],
                total_cost=data['cost'],
                total_duration=data['duration'],
                total_input_tokens=data['input_tokens'],
                total_output_tokens=data['output_tokens']
            )
            for op_name, data in operations.items()
        ]
    
    def format_cost_report(self) -> str:
        """Format a comprehensive cost report."""
        if not self.api_calls:
            return "No API calls tracked yet."
        
        total_cost = self.get_total_cost()
        total_duration = self.get_total_duration()
        total_calls = len(self.api_calls)
        
        report = [
            "💰 COST & TIMING REPORT",
            "=" * 40,
            f"Total API Calls: {total_calls}",
            f"Total Cost: ${total_cost:.4f}",
            f"Total API Time: {total_duration:.2f}s",
            "",
            "BY OPERATION:",
            "-" * 40
        ]
        
        for summary in self.get_operation_summary():
            report.extend([
                f"{summary.operation}:",
                f"  Calls: {summary.total_calls}",
                f"  Cost: ${summary.total_cost:.4f}",
                f"  Time: {summary.total_duration:.2f}s",
                f"  Tokens: {summary.total_input_tokens:,} in, {summary.total_output_tokens:,} out",
                ""
            ])
        
        return "\n".join(report)
    
    def format_timing_report(self) -> str:
        """Format a timing-focused report."""
        if not self.api_calls:
            return "No API calls tracked yet."
        
        total_duration = self.get_total_duration()
        session_duration = time.time() - self.session_start
        
        report = [
            "⏱️  TIMING REPORT", 
            "=" * 30,
            f"Session Duration: {session_duration:.2f}s",
            f"API Call Time: {total_duration:.2f}s",
            f"Non-API Time: {session_duration - total_duration:.2f}s",
            "",
            "BY OPERATION:",
            "-" * 30
        ]
        
        for summary in self.get_operation_summary():
            avg_time = summary.total_duration / summary.total_calls if summary.total_calls > 0 else 0
            report.extend([
                f"{summary.operation}:",
                f"  Total: {summary.total_duration:.2f}s",
                f"  Average: {avg_time:.2f}s per call",
                f"  Calls: {summary.total_calls}",
                ""
            ])
        
        return "\n".join(report)
    
    def get_cost_estimate(self, operation: str, model: str = None) -> float:
        """Get cost estimate for an operation based on historical data."""
        if model is None:
            model = os.getenv('GITHUB_BACKLOG_MODEL', 'claude-3-5-sonnet-20241022')
        
        # Get historical average for this operation
        matching_calls = [call for call in self.api_calls if call.operation == operation]
        
        if matching_calls:
            avg_input = sum(call.input_tokens for call in matching_calls) // len(matching_calls)
            avg_output = sum(call.output_tokens for call in matching_calls) // len(matching_calls)
        else:
            # Fallback estimates
            estimates = {
                'phase_generation': (5000, 3000),
                'epic_generation': (4000, 2000),
                'task_generation': (3000, 1000),
                'task_description': (2000, 1000),
                'readme_analysis': (1500, 500)
            }
            avg_input, avg_output = estimates.get(operation, (2000, 1000))
        
        return self.calculate_cost(model, avg_input, avg_output)


# Context manager for tracking operations
class OperationTracker:
    """Context manager for tracking individual operations."""
    
    def __init__(self, cost_tracker: CostTracker, operation: str, model: str = None):
        self.cost_tracker = cost_tracker
        self.operation = operation
        self.model = model or os.getenv('GITHUB_BACKLOG_MODEL', 'claude-3-5-sonnet-20241022')
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:  # Only track successful operations
            duration = time.time() - self.start_time
            # In a real implementation, you'd get actual token counts from the API response
            # For now, we'll use estimates based on operation type
            input_tokens, output_tokens = self._estimate_tokens()
            
            self.cost_tracker.track_api_call(
                self.operation, self.model, input_tokens, output_tokens, duration
            )
    
    def _estimate_tokens(self) -> tuple[int, int]:
        """Estimate token usage for the operation."""
        estimates = {
            'phase_generation': (5000, 3000),
            'epic_generation': (4000, 2000), 
            'task_generation': (3000, 1000),
            'task_description': (2000, 1000),
            'readme_analysis': (1500, 500)
        }
        return estimates.get(self.operation, (2000, 1000))


def create_cost_tracker(project_dir: Optional[Path] = None) -> CostTracker:
    """Factory function to create a cost tracker."""
    return CostTracker(project_dir)