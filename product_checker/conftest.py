"""Pytest configuration for product_checker tests."""
from dotenv import load_dotenv


def pytest_configure(config):
    """Load environment variables from .env file before running tests."""
    load_dotenv()
