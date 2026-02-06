"""Shared test fixtures."""

import pytest
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent.parent / "examples" / "calculator_test"


@pytest.fixture
def examples_dir():
    return EXAMPLES_DIR


@pytest.fixture
def sample_project_yaml(examples_dir):
    return examples_dir / "project.yaml"


@pytest.fixture
def sample_test_yaml(examples_dir):
    return examples_dir / "tests" / "test_basic_addition.yaml"
