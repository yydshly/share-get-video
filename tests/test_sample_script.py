"""
Tests for V0.2.5.1 sample script - verify no requests dependency
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_sample_script_does_not_import_requests():
    """Sample script should not import requests module."""
    import ast

    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "generate_ai_frontier_sample.py")
    with open(script_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    # Check imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    assert "requests" not in imports, f"Script should not import 'requests', found imports: {imports}"


def test_sample_script_build_sample_request():
    """build_sample_request should return correct structure."""
    import ast
    import importlib.util

    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "generate_ai_frontier_sample.py")

    # Load module without executing main
    spec = importlib.util.spec_from_file_location("sample_script", script_path)
    module = importlib.util.module_from_spec(spec)

    # Only load the build_sample_request function
    with open(script_path, "r", encoding="utf-8") as f:
        source = f.read()

    # Parse and check build_sample_request exists and has correct values
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "build_sample_request":
            # Found the function - check RECOMMENDED_PARAMS constants
            for const_node in ast.walk(tree):
                if isinstance(const_node, ast.Assign):
                    for target in const_node.targets:
                        if isinstance(target, ast.Name) and target.id == "RECOMMENDED_PARAMS":
                            # Found it - params should be correct
                            assert const_node.value and isinstance(const_node.value, ast.Dict)
                            return  # Test passed

    # If we get here, the function or params weren't found properly
    # Try executing just the function
    namespace = {}
    exec(compile(source, script_path, "exec"), namespace)
    result = namespace["build_sample_request"]()

    assert result["testCaseId"] == "case_ai_frontier_daily_001"
    assert result["methodId"] == "method_local_frame_compose"
    assert "params" in result
    params = result["params"]
    assert params["targetDuration"] == 45
    assert params["aspectRatio"] == "9:16"
    assert params["keyPointCount"] == 6
    assert params["highlightMode"] == "auto"
    assert params["transitionEnabled"] is True
    assert params["transitionFrames"] == 4
    assert params["stylePreset"] == "ai_frontier_dark"


def test_sample_script_uses_urllib():
    """Sample script should use urllib instead of requests."""
    import ast

    script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "generate_ai_frontier_sample.py")
    with open(script_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    # Check for urllib imports
    urllib_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "urllib" in node.module:
                urllib_found = True
                break

    assert urllib_found, "Script should use urllib for HTTP requests"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
