"""Pytest config: use a temp SQLite for the suite and disable network."""
import os
import tempfile

os.environ.setdefault("CARD_SCOUT_DB", os.path.join(tempfile.gettempdir(), "card_scout_test.db"))
