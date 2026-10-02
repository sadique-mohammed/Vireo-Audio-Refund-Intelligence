import socket

import pytest

from src.vireo.config import RAW_DIR
from src.vireo.load import load_tickets
from src.vireo.pipeline import run_financial


@pytest.fixture(scope="session")
def fin():
    return run_financial(load_tickets(RAW_DIR / "tickets.csv"))


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.fixture
def no_sleep(monkeypatch):
    from src.vireo import reasons

    monkeypatch.setattr(reasons.time, "sleep", lambda seconds: None)
