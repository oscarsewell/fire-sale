"""Test file for lambda_handler.py"""
import json
import pytest
from unittest.mock import Mock, patch
from lambda_handler import lambda_handler, get_db_credentials


# Tests for get_db_credentials
@patch.dict('os.environ', {
    'DB_HOST': 'localhost',
    'DB_USER': 'testuser',
    'DB_PASSWORD': 'testpass',
    'DB_PORT': '5432',
    'DB_NAME': 'testdb'
})
def test_get_db_credentials_from_environment():
    """Should retrieve credentials from environment variables"""
    result = get_db_credentials()

    assert result['host'] == 'localhost'
    assert result['username'] == 'testuser'
    assert result['password'] == 'testpass'
    assert result['port'] == 5432
    assert result['dbname'] == 'testdb'


@patch('lambda_handler.secrets_client')
@patch.dict('os.environ', {
    'DB_SECRET_ARN': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:db-creds'
}, clear=True)
def test_get_db_credentials_from_secrets_manager(mock_secrets_client):
    """Should retrieve credentials from AWS Secrets Manager"""
    mock_secrets_client.get_secret_value.return_value = {
        'SecretString': json.dumps({
            'host': 'db.example.com',
            'username': 'admin',
            'password': 'secret',
            'port': '5432',
            'dbname': 'mydb'
        })
    }

    result = get_db_credentials()

    assert result['host'] == 'db.example.com'
    assert result['username'] == 'admin'


# Tests for lambda_handler
@patch('lambda_handler.psycopg2.connect')
@patch('lambda_handler.get_db_credentials')
@patch.dict('os.environ', {'DB_HOST': 'localhost'})
def test_lambda_handler_processes_notifications(mock_get_creds, mock_connect):
    """Should process both defunct products and price alerts"""
    mock_get_creds.return_value = {
        'host': 'localhost',
        'port': 5432,
        'username': 'user',
        'password': 'pass',
        'dbname': 'db'
    }

    mock_connection = Mock()
    mock_connect.return_value = mock_connection

    event = {
        "inserted": 5,
        "defunct_products": [
            {"product_id": 100, "url": "https://example.com/product1"}
        ]
    }

    with patch('lambda_handler.process_defunct_products') as mock_defunct:
        mock_defunct.return_value = [{
            "recipient": "user@example.com",
            "channel": "email",
            "subject": "Product No Longer Available",
            "body": "Your product is gone",
            "product_id": 100,
            "user_id": 1
        }]

        with patch('lambda_handler.get_tracking_records') as mock_tracking:
            mock_tracking.return_value = [{
                "user_id": 2,
                "product_id": 101,
                "target_price": 50,
                "original_price": 100,
                "email": None,
                "discord": "user2",
            }]

            with patch('lambda_handler.get_product_records') as mock_products:
                mock_products.return_value = [{
                    "product_id": 101,
                    "product_url": "https://example.com/product2",
                    "website_name": "Store",
                    "currency": "GBP",
                    "latest_price": 45,
                }]

                with patch('lambda_handler.process_notifications') as mock_notifications:
                    mock_notifications.return_value = {
                        "emails": [],
                        "discord": [{
                            "recipient": "user2",
                            "channel": "discord",
                            "message": "Price alert!",
                            "product_id": 101,
                            "user_id": 2
                        }]
                    }

                    result = lambda_handler(event, None)

    assert result['statusCode'] == 200
    assert len(result['body']['emails']) == 1
    assert len(result['body']['discord']) == 1
    mock_connection.close.assert_called_once()


@patch('lambda_handler.psycopg2.connect')
@patch('lambda_handler.get_db_credentials')
@patch.dict('os.environ', {'DB_HOST': 'localhost'})
def test_lambda_handler_handles_errors(mock_get_creds, mock_connect):
    """Should return error response when processing fails"""
    mock_get_creds.return_value = {
        'host': 'localhost',
        'port': 5432,
        'username': 'user',
        'password': 'pass',
        'dbname': 'db'
    }

    mock_connection = Mock()
    mock_connect.return_value = mock_connection

    event = {
        "inserted": 5,
        "defunct_products": [
            {"product_id": 100, "url": "https://example.com/product1"}
        ]
    }

    with patch('lambda_handler.process_defunct_products') as mock_defunct:
        mock_defunct.side_effect = Exception('Processing error')

        result = lambda_handler(event, None)

    assert result['statusCode'] == 500
    assert result['body']['emails'] == []
    assert result['body']['discord'] == []
    mock_connection.close.assert_called_once()


@patch('lambda_handler.psycopg2.connect')
@patch('lambda_handler.get_db_credentials')
@patch.dict('os.environ', {'DB_HOST': 'localhost'})
def test_lambda_handler_response_format(mock_get_creds, mock_connect):
    """Should return response with correct Lambda format"""
    mock_get_creds.return_value = {
        'host': 'localhost',
        'port': 5432,
        'username': 'user',
        'password': 'pass',
        'dbname': 'db'
    }

    mock_connection = Mock()
    mock_connect.return_value = mock_connection

    event = {"inserted": 5, "defunct_products": []}

    with patch('lambda_handler.process_defunct_products') as mock_defunct:
        mock_defunct.return_value = []

        with patch('lambda_handler.get_tracking_records') as mock_tracking:
            mock_tracking.return_value = []

            with patch('lambda_handler.get_product_records') as mock_products:
                mock_products.return_value = []

                result = lambda_handler(event, None)

    assert 'statusCode' in result
    assert 'body' in result
    assert 'emails' in result['body']
    assert 'discord' in result['body']
    assert isinstance(result['body']['emails'], list)
    assert isinstance(result['body']['discord'], list)
