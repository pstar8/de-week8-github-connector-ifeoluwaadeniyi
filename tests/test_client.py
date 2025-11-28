import pytest
from unittest.mock import Mock, patch
from requests.exceptions import ConnectionError, Timeout

from github_connector import GitHubClient
from github_connector.custom_exceptions import (
    ResourceNotFound,
    AuthenticationError,
    RateLimitExceeded,
    NetworkError,
    GitHubAPIError
)

@pytest.fixture
def client():
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'fake_token_for_testing'}):
        return GitHubClient()


class TestGitHubClientInit:
    def test_init_with_token(self):
        client = GitHubClient(token="test_token")
        assert client.token == "test_token"
    
    def test_init_without_token(self):
        with patch.dict('os.environ', {'GITHUB_TOKEN': 'env_token'}):
            client = GitHubClient()
            assert client.token == "env_token"
    
    def test_init_no_token_anywhere(self):
        with patch.dict('os.environ', {}, clear=True):
            client = GitHubClient()
            assert client.token is None


class TestGetHeaders:
    def test_headers_with_token(self, client):
        headers = client._get_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer fake_token_for_testing"
        assert headers["Accept"] == "application/vnd.github+json"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
    
    def test_headers_without_token(self):
        with patch.dict('os.environ', {}, clear=True):
            client = GitHubClient()
            headers = client._get_headers()
            
            assert "Authorization" not in headers
            assert headers["Accept"] == "application/vnd.github+json"


class TestMakeRequestSuccess:
    @patch('github_connector.client.requests.request')
    def test_successful_request(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test-repo", "stars": 100}
        mock_request.return_value = mock_response
        
        result = client._make_request("GET", "/repos/owner/repo")
        
        assert result == {"name": "test-repo", "stars": 100}
        mock_request.assert_called_once()


class TestMakeRequestErrors:
    @patch('github_connector.client.requests.request')
    def test_404_raises_resource_not_found(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        with pytest.raises(ResourceNotFound) as exc_info:
            client._make_request("GET", "/repos/owner/nonexistent")
        
        assert "nonexistent" in str(exc_info.value)
        assert exc_info.value.status_code == 404
    
    @patch('github_connector.client.requests.request')
    def test_401_raises_authentication_error(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        with pytest.raises(AuthenticationError) as exc_info:
            client._make_request("GET", "/repos/owner/repo")
        
        assert exc_info.value.status_code == 401
    
    @patch('github_connector.client.requests.request')
    def test_429_retries_and_succeeds(self, mock_request, client):
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.headers = {'Retry-After': '1'}
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}
        
        mock_request.side_effect = [mock_response_429, mock_response_429, mock_response_200]
        
        result = client._make_request("GET", "/repos/owner/repo")
        
        assert result == {"success": True}
        assert mock_request.call_count == 3
    
    @patch('github_connector.client.requests.request')
    def test_429_max_retries_raises_exception(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '1'}
        mock_request.return_value = mock_response
        
        with pytest.raises(RateLimitExceeded):
            client._make_request("GET", "/repos/owner/repo")
        
        assert mock_request.call_count == 3
    
    @patch('github_connector.client.requests.request')
    def test_connection_error_retries_and_raises(self, mock_request, client):
        mock_request.side_effect = ConnectionError("Network unreachable")
        
        with pytest.raises(NetworkError) as exc_info:
            client._make_request("GET", "/repos/owner/repo")
        
        assert mock_request.call_count == 3
        assert "Network unreachable" in str(exc_info.value)

class TestPublicMethods:
    @patch('github_connector.client.requests.request')
    def test_get_repo_details(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "full_name": "octocat/Hello-World",
            "stargazers_count": 1500,
            "forks_count": 800
        }
        mock_request.return_value = mock_response
        
        result = client.get_repo_details("octocat", "Hello-World")
        
        assert result["full_name"] == "octocat/Hello-World"
        assert result["stargazers_count"] == 1500
    
    @patch('github_connector.client.requests.request')
    def test_get_latest_release(self, mock_request, client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.0.0",
            "name": "Release 1.0.0",
            "published_at": "2024-01-01T00:00:00Z"
        }
        mock_request.return_value = mock_response
        
        result = client.get_latest_release("python", "cpython")
        
        assert result["tag_name"] == "v1.0.0"
        assert result["name"] == "Release 1.0.0"