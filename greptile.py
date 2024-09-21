import requests
import json
from typing import List, Dict, Optional
import urllib.parse
# import time


class GreptileAPI:
    def __init__(self, greptile_api_key: str, github_token: str):
        self.base_url = "https://api.greptile.com/v2"
        self.headers = {
            "Authorization": f"Bearer {greptile_api_key}",
            "X-GitHub-Token": github_token,
            "Content-Type": "application/json",
        }

    def get_repository_info(self, repository_id: str) -> Dict:
        url = f"{self.base_url}/repositories/{repository_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def index_repository(self, remote: str, repository: str, branch: str) -> Dict:
        url = f"{self.base_url}/repositories"
        payload = {
            "remote": remote,
            "repository": repository,
            "branch": branch,
            "reload": True,
            "notify": True,
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def is_repository_indexed(self, remote: str, repository: str, branch: str) -> bool:
        readable_repository_id = f"{remote}:{branch}:{repository}"
        repository_id = urllib.parse.quote_plus(readable_repository_id)

        try:
            response = self.get_repository_info(repository_id)
            return response.get("status") == "completed"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return False
            raise

    def ensure_repository_indexed(
        self, remote: str, repository: str, branch: str
    ) -> bool:
        if not self.is_repository_indexed(remote, repository, branch):
            print(f"Repository {remote}/{repository} not indexed. Indexing now...")
            self.index_repository(remote, repository, branch)
        return True

    def query(
        self,
        messages: List[Dict[str, str]],
        repositories: List[Dict[str, str]],
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
    ) -> requests.Response:
        for repo in repositories:
            self.ensure_repository_indexed(
                repo["remote"], repo["repository"], repo["branch"]
            )

        url = f"{self.base_url}/query"
        payload = {
            "messages": messages,
            "repositories": repositories,
            "sessionId": session_id,
            "stream": stream,
            "genius": genius,
        }

        response = requests.post(url, json=payload, headers=self.headers)

        try:
            json_response = response.json()
            print(f"JSON response: {json_response}")
        except json.JSONDecodeError:
            print("Failed to decode JSON response")

        if response.status_code != 200:
            print(f"Error response: {response.text}")

        return response
