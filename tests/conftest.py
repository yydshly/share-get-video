"""
conftest.py - Pytest configuration
Ensures test environment isolation from .env loading.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def clean_minimax_env(monkeypatch):
    """
    Before each test: remove MINIMAX_API_KEY from os.environ so that
    TTS client tests can control the configured state via patch.dict().

    After each test: restore to original value (or leave unset).
    """
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
