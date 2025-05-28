"""Tests for HTTP operation tools."""

from unittest.mock import Mock, patch

from konseho.tools.http_ops import http_get, http_post


class TestHttpGet:
    """Test the http_get tool."""

    @patch("requests.get")
    def test_successful_get(self, mock_get):
        """Test successful GET request."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Hello, World!"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.json.return_value = None
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = http_get("https://example.com")

        assert result["status_code"] == 200
        assert result["text"] == "Hello, World!"
        assert "headers" in result
        assert "error" not in result
        mock_get.assert_called_once_with(
            "https://example.com", headers=None, timeout=10
        )

    @patch("requests.get")
    def test_get_with_json_response(self, mock_get):
        """Test GET request with JSON response."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"key": "value"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = http_get("https://api.example.com/data")

        assert result["status_code"] == 200
        assert result["json"] == {"key": "value"}
        assert result["text"] == '{"key": "value"}'

    @patch("requests.get")
    def test_get_with_headers(self, mock_get):
        """Test GET request with custom headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_response.headers = {}
        mock_response.json.return_value = None
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        custom_headers = {"Authorization": "Bearer token123"}
        result = http_get("https://example.com", headers=custom_headers)

        assert result["status_code"] == 200
        mock_get.assert_called_once_with(
            "https://example.com", headers=custom_headers, timeout=10
        )

    @patch("requests.get")
    def test_get_with_timeout(self, mock_get):
        """Test GET request with custom timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_response.headers = {}
        mock_response.json.return_value = None
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = http_get("https://example.com", timeout=30)

        assert result["status_code"] == 200
        mock_get.assert_called_once_with(
            "https://example.com", headers=None, timeout=30
        )

    @patch("requests.get")
    def test_get_error_response(self, mock_get):
        """Test GET request with error response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.headers = {}
        mock_response.json.return_value = None
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        result = http_get("https://example.com/missing")

        assert result["status_code"] == 404
        assert result["text"] == "Not Found"
        # Should still return the response, not an error
        assert "error" not in result

    @patch("requests.get")
    def test_get_connection_error(self, mock_get):
        """Test GET request with connection error."""
        mock_get.side_effect = Exception("Connection refused")

        result = http_get("https://unreachable.com")

        assert "error" in result
        assert "Connection refused" in result["error"]

    def test_invalid_url(self):
        """Test GET request with invalid URL."""
        result = http_get("not-a-url")

        assert "error" in result
        assert "invalid" in result["error"].lower() or "url" in result["error"].lower()


class TestHttpPost:
    """Test the http_post tool."""

    @patch("requests.post")
    def test_successful_post_with_data(self, mock_post):
        """Test successful POST request with form data."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.text = "Created"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.json.return_value = None
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = http_post(
            "https://example.com/create", data={"name": "test", "value": "123"}
        )

        assert result["status_code"] == 201
        assert result["text"] == "Created"
        mock_post.assert_called_once_with(
            "https://example.com/create",
            data={"name": "test", "value": "123"},
            json=None,
            headers=None,
            timeout=10,
        )

    @patch("requests.post")
    def test_post_with_json(self, mock_post):
        """Test POST request with JSON data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 123}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"id": 123}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = http_post(
            "https://api.example.com/items", json={"name": "item", "quantity": 5}
        )

        assert result["status_code"] == 200
        assert result["json"] == {"id": 123}
        mock_post.assert_called_once_with(
            "https://api.example.com/items",
            data=None,
            json={"name": "item", "quantity": 5},
            headers=None,
            timeout=10,
        )

    @patch("requests.post")
    def test_post_with_headers(self, mock_post):
        """Test POST request with custom headers."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_response.headers = {}
        mock_response.json.return_value = None
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        custom_headers = {"Authorization": "Bearer token", "X-Custom-Header": "value"}

        result = http_post(
            "https://example.com/api", json={"data": "test"}, headers=custom_headers
        )

        assert result["status_code"] == 200
        mock_post.assert_called_once_with(
            "https://example.com/api",
            data=None,
            json={"data": "test"},
            headers=custom_headers,
            timeout=10,
        )

    @patch("requests.post")
    def test_post_empty_body(self, mock_post):
        """Test POST request with no data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_response.headers = {}
        mock_response.json.return_value = None
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = http_post("https://example.com/ping")

        assert result["status_code"] == 200
        mock_post.assert_called_once_with(
            "https://example.com/ping", data=None, json=None, headers=None, timeout=10
        )

    @patch("requests.post")
    def test_post_error_response(self, mock_post):
        """Test POST request with error response."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad Request"}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"error": "Bad Request"}
        mock_response.raise_for_status.side_effect = Exception("400 Bad Request")
        mock_post.return_value = mock_response

        result = http_post("https://example.com/api", json={"bad": "data"})

        assert result["status_code"] == 400
        assert result["json"] == {"error": "Bad Request"}
        # Should return response, not error
        assert "error" not in result

    @patch("requests.post")
    def test_post_timeout(self, mock_post):
        """Test POST request timeout."""
        mock_post.side_effect = Exception("Request timed out")

        result = http_post("https://slow.example.com", timeout=1)

        assert "error" in result
        assert (
            "timed out" in result["error"].lower()
            or "timeout" in result["error"].lower()
        )

    def test_post_invalid_url(self):
        """Test POST with invalid URL."""
        result = http_post("not://valid.url")

        assert "error" in result
        assert "invalid" in result["error"].lower() or "url" in result["error"].lower()
