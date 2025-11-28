import logging
from dotenv import load_dotenv

from github_connector import GitHubClient
from github_connector.custom_exceptions import (
    GitHubAPIError,
    ResourceNotFound,
    AuthenticationError,
    RateLimitExceeded
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()


def main():
    """Demonstrates usage of the GitHubClient library."""
    
    client = GitHubClient()
    try:
        print("\n[1] Fetching repository details for 'octocat/Hello-World'...")
        repo_details = client.get_repo_details("octocat", "Hello-World")
        
        print(f"\nRepository: {repo_details['full_name']}")
        print(f"Description: {repo_details['description']}")
        print(f"Stars: {repo_details['stargazers_count']}")
        print(f"Forks: {repo_details['forks_count']}")
        print(f"Language: {repo_details['language']}")
        print(f"Open Issues: {repo_details['open_issues_count']}")
        
    except ResourceNotFound as e:
        print(f"\ Error: {e.message}")
    except AuthenticationError as e:
        print(f"\ Error: {e.message}")
    except GitHubAPIError as e:
        print(f"\ API Error: {e.message}")
    
    try:
        print("[2] Fetching latest release for 'python/cpython'...")
        release = client.get_latest_release("python", "cpython")
        
        print(f"\nLatest Release: {release['tag_name']}")
        print(f"Name: {release['name']}")
        print(f"Published: {release['published_at']}")
        print(f"Author: {release['author']['login']}")
        
    except ResourceNotFound as e:
        print(f"\ Error: {e.message}")
    except GitHubAPIError as e:
        print(f"\ API Error: {e.message}")
    
    try:
        print("[3] Testing error handling with non-existent repo...")
        client.get_repo_details("thisdoesnotexist12345", "norepo67890")
        
    except ResourceNotFound as e:
        print(f"\n✓ Correctly caught error: {e.message}")
    except GitHubAPIError as e:
        print(f"\ Unexpected error: {e.message}")
    
if __name__ == "__main__":
    main()