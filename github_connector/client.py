import os
import logging
import time
from typing import Dict, Any, Optional

import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

from .custom_exceptions import (
    GitHubAPIError,
    ResourceNotFound,
    RateLimitExceeded,
    AuthenticationError,
    NetworkError
)

logger = logging.getLogger(__name__)


class GitHubClient:
    BASE_URL = "https://api.github.com"
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1
    
    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN")
        
        if not self.token:
            logger.warning("No GitHub token provided. Rate limits will be severely restricted.")
        
        logger.info("GitHubClient initialized")
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers
    
    def _make_request(self, method: str, endpoint: str) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        logger.info(f"Making {method} request to {url}")
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.request(method, url, headers=headers, timeout=10)
                
                if response.status_code == 404:
                    logger.error(f"Resource not found: {endpoint}")
                    raise ResourceNotFound(endpoint)
                
                if response.status_code == 401:
                    logger.error("Authentication failed")
                    raise AuthenticationError()
                
                if response.status_code in (429, 403):
                    retry_after = int(response.headers.get('Retry-After', self.INITIAL_BACKOFF * (2 ** attempt)))
                    
                    if attempt < self.MAX_RETRIES - 1:
                        logger.warning(f"Rate limit hit. Retrying in {retry_after}s (attempt {attempt + 1}/{self.MAX_RETRIES})")
                        time.sleep(retry_after)
                        continue
                    else:
                        logger.error("Rate limit exceeded and max retries reached")
                        raise RateLimitExceeded(retry_after)
                
                response.raise_for_status()
                
                logger.info(f"Request successful: {response.status_code}")
                return response.json()
            
            except (ConnectionError, Timeout) as e:
                if attempt < self.MAX_RETRIES - 1:
                    backoff = self.INITIAL_BACKOFF * (2 ** attempt)
                    logger.warning(f"Network error: {e}. Retrying in {backoff}s (attempt {attempt + 1}/{self.MAX_RETRIES})")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"Network error after {self.MAX_RETRIES} attempts")
                    raise NetworkError(e)
            
            except RequestException as e:
                logger.error(f"Request failed: {e}")
                raise GitHubAPIError(f"Request failed: {str(e)}")
        
        raise GitHubAPIError("Max retries exceeded")
    
    def get_repo_details(self, owner: str, repo: str) -> Dict[str, Any]:
        endpoint = f"/repos/{owner}/{repo}"
        return self._make_request("GET", endpoint)
    
    def get_latest_release(self, owner: str, repo: str) -> Dict[str, Any]:
        endpoint = f"/repos/{owner}/{repo}/releases/latest"
        return self._make_request("GET", endpoint)