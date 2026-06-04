"""Tests for database helper functions: upsert_product, add_tracked_product, get_tracked_products."""
import psycopg2.errors
import pytest
from unittest.mock import MagicMock, patch


def _mock_db(mock_get_db):
    """Wire up a mock get_db context manager and return the cursor mock."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    return mock_cur


# ── upsert_product ────────────────────────────────────────────────────────────

@patch("database.get_db")
def test_upsert_product_returns_product_id(mock_get_db):
    """upsert_product should return the product id from the DB."""
    mock_cur = _mock_db(mock_get_db)
    mock_cur.fetchone.side_effect = [
        {"id": 5}, {"id": 42}]  # site_id, then product_id

    from database import upsert_product
    result = upsert_product("https://ebuyer.com/product",
                            "Test GPU", "ebuyer", "GBP")
    assert result == 42


@patch("database.get_db")
def test_upsert_product_raises_on_db_error(mock_get_db):
    """upsert_product should propagate DB exceptions."""
    mock_get_db.side_effect = Exception("DB connection failed")

    from database import upsert_product
    with pytest.raises(Exception, match="DB connection failed"):
        upsert_product("https://ebuyer.com/product",
                       "Test GPU", "ebuyer", "GBP")


# ── add_tracked_product ───────────────────────────────────────────────────────

@patch("database.get_db")
def test_add_tracked_product_inserts_successfully(mock_get_db):
    """add_tracked_product should execute an INSERT without error."""
    mock_cur = _mock_db(mock_get_db)

    from database import add_tracked_product
    add_tracked_product(user_id=1, product_id=10,
                        target_price=69999, original_price=74999)
    mock_cur.execute.assert_called_once()


@patch("database.get_db")
def test_add_tracked_product_raises_value_error_on_duplicate(mock_get_db):
    """add_tracked_product should raise ValueError when the product is already tracked."""
    mock_cur = _mock_db(mock_get_db)
    mock_cur.execute.side_effect = psycopg2.errors.UniqueViolation

    from database import add_tracked_product
    with pytest.raises(ValueError, match="already tracking"):
        add_tracked_product(user_id=1, product_id=10,
                            target_price=69999, original_price=74999)


# ── get_tracked_products ──────────────────────────────────────────────────────

@patch("database.get_db")
def test_get_tracked_products_returns_list(mock_get_db):
    """get_tracked_products should return the rows fetched from the DB."""
    mock_cur = _mock_db(mock_get_db)
    mock_cur.fetchall.return_value = [
        {
            "product_name": "Test GPU",
            "product_url": "https://ebuyer.com/product",
            "site": "ebuyer",
            "currency": "GBP",
            "target_price": 69999,
            "original_price": 74999,
            "current_price": 72000,
        }
    ]

    from database import get_tracked_products
    result = get_tracked_products(user_id=1)
    assert len(result) == 1
    assert result[0]["product_name"] == "Test GPU"


@patch("database.get_db")
def test_get_tracked_products_returns_empty_list(mock_get_db):
    """get_tracked_products should return an empty list when the user has no tracked products."""
    mock_cur = _mock_db(mock_get_db)
    mock_cur.fetchall.return_value = []

    from database import get_tracked_products
    result = get_tracked_products(user_id=1)
    assert result == []
