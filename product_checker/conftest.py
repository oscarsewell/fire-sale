"""Pytest configuration for product_checker tests."""

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def pytest_configure(config):
    """Load environment variables from .env file before running tests."""
    if load_dotenv is not None:
        load_dotenv()
