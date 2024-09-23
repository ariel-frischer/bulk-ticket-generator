import requests
import os
from typing import List, Dict, Optional


class GreptileAPI:
    def __init__(self):
        self.url = "https://api.greptile.com/v2/query"
        self.headers = {
            "Authorization": f"Bearer {os.environ.get('GREPTILE_API_KEY')}",
            "X-GitHub-Token": os.environ.get("GITHUB_TOKEN"),
            "Content-Type": "application/json",
        }

    def query(
        self,
        messages: List[Dict[str, str]],
        repositories: List[Dict[str, str]],
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
    ) -> requests.Response:
        """
        Send a query to the Greptile API.

        :param messages: List of message dictionaries with 'id', 'content', and 'role'
        :param repositories: List of repository dictionaries with 'remote', 'branch', and 'repository'
        :param session_id: Optional session ID
        :param stream: Whether to stream the response
        :param genius: Whether to use the genius feature
        :return: Response from the Greptile API
        """
        payload = {
            "messages": messages,
            "repositories": repositories,
            "sessionId": session_id,
            "stream": stream,
            "genius": genius,
        }

        response = requests.post(self.url, json=payload, headers=self.headers)
        return response


# Example usage:
# greptile = GreptileAPI()
# response = greptile.query(
#     messages=[{"id": "1", "content": "What are the main functions in the codebase?", "role": "user"}],
#     repositories=[{"remote": "https://github.com/username/repo.git", "branch": "main", "repository": "repo"}]
# )
# print(response.text)
