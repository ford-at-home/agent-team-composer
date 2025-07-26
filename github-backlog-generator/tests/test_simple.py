"""Simple tests to verify the package is working"""

def test_import():
    """Test that the main module can be imported"""
    import github_backlog_generator
    assert github_backlog_generator is not None

def test_basic_functionality():
    """Test basic functionality is accessible"""
    from github_backlog_generator.cli_unified import BacklogManager
    assert BacklogManager is not None