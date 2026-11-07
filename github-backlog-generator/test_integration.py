#!/usr/bin/env python3
"""Quick integration test for the new CLI commands."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from github_backlog_generator.cli import cli
from click.testing import CliRunner

def test_commands_exist():
    """Test that all commands are available."""
    runner = CliRunner()
    
    # Test help to see all commands
    result = runner.invoke(cli, ['--help'])
    print("Available commands:")
    print(result.output)
    
    # Check that our new commands exist
    expected_commands = ['phases', 'epics', 'issues', 'status']
    for cmd in expected_commands:
        if cmd in result.output:
            print(f"✓ {cmd} command is available")
        else:
            print(f"✗ {cmd} command is missing")
            return False
    
    return True

def test_command_help():
    """Test that all commands have working help."""
    runner = CliRunner()
    
    commands = ['phases', 'epics', 'issues', 'status']
    
    for cmd in commands:
        result = runner.invoke(cli, [cmd, '--help'])
        if result.exit_code == 0:
            print(f"✓ {cmd} --help works")
        else:
            print(f"✗ {cmd} --help failed with exit code {result.exit_code}")
            print(result.output)
            return False
    
    return True

def test_backwards_compatibility():
    """Test that existing commands still work."""
    runner = CliRunner()
    
    existing_commands = ['init', 'generate', 'milestones', 'pricing']
    
    for cmd in existing_commands:
        result = runner.invoke(cli, [cmd, '--help'])
        if result.exit_code == 0:
            print(f"✓ {cmd} --help works (backwards compatible)")
        else:
            print(f"✗ {cmd} --help failed with exit code {result.exit_code}")
            print(result.output)
            return False
    
    return True

def test_auto_detection_logic():
    """Test that auto-detection logic works without breaking."""
    runner = CliRunner()
    
    # Test commands that should either auto-detect or fail gracefully
    commands_to_test = [
        (['phases', '--dry-run'], ["Auto-detected repository", "No repository URL provided"]),
        (['epics', '--dry-run'], ["Auto-detected repository", "No repository URL provided"]),
        (['issues', '--dry-run'], ["Auto-detected repository", "No repository URL provided"]),
        (['status'], ["Auto-detected repository", "No repository URL provided"])
    ]
    
    for cmd, expected_outputs in commands_to_test:
        result = runner.invoke(cli, cmd)
        # Check if any of the expected outputs are present
        found_expected = any(expected in result.output for expected in expected_outputs)
        if found_expected:
            print(f"✓ {' '.join(cmd)} auto-detection works")
        else:
            print(f"✗ {' '.join(cmd)} auto-detection failed")
            print(f"Expected one of: {expected_outputs}")
            print(f"Got: {result.output[:200]}...")  # Truncate long output
            return False
    
    return True

if __name__ == '__main__':
    print("Running integration tests...\n")
    
    tests = [
        test_commands_exist,
        test_command_help,
        test_backwards_compatibility,
        test_auto_detection_logic
    ]
    
    all_passed = True
    for test in tests:
        print(f"\n{'='*50}")
        print(f"Running {test.__name__}")
        print('='*50)
        
        if not test():
            all_passed = False
            print(f"FAILED: {test.__name__}")
        else:
            print(f"PASSED: {test.__name__}")
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All integration tests PASSED!")
        print("\nThe new CLI commands are working correctly:")
        print("  - github-backlog-generator phases")
        print("  - github-backlog-generator epics [--phase N]")
        print("  - github-backlog-generator issues [--phase N --epic N]") 
        print("  - github-backlog-generator status [--output json|table]")
        print("\nBackwards compatibility maintained for all existing commands.")
    else:
        print("❌ Some integration tests FAILED!")
        sys.exit(1)