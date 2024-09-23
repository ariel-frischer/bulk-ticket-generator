import requests
import json
from typing import List, Dict, Optional
import urllib.parse
import aiohttp
import asyncio


class GreptileAPI:
    def __init__(self, greptile_api_key: str, github_token: str):
        self.base_url = "https://api.greptile.com/v2"
        self.headers = {
            "Authorization": f"Bearer {greptile_api_key}",
            "X-GitHub-Token": github_token,
            "Content-Type": "application/json",
        }

    async def get_repository_info(self, repository_id: str) -> Dict:
        url = f"{self.base_url}/repositories/{repository_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                return await response.json()

    async def index_repository(self, remote: str, repository: str, branch: str) -> Dict:
        url = f"{self.base_url}/repositories"
        payload = {
            "remote": remote,
            "repository": repository,
            "branch": branch,
            "reload": True,
            "notify": True,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=self.headers
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def is_repository_indexed(
        self, remote: str, repository: str, branch: str
    ) -> bool:
        readable_repository_id = f"{remote}:{branch}:{repository}"
        repository_id = urllib.parse.quote_plus(readable_repository_id)

        try:
            response = await self.get_repository_info(repository_id)
            return response.get("status") == "completed"
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return False
            raise

    async def ensure_repository_indexed(
        self, remote: str, repository: str, branch: str
    ) -> bool:
        if not await self.is_repository_indexed(remote, repository, branch):
            print(f"Repository {remote}/{repository} not indexed. Indexing now...")
            await self.index_repository(remote, repository, branch)
        return True

    async def query_async(
        self,
        messages: List[Dict[str, str]],
        repositories: List[Dict[str, str]],
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
    ) -> aiohttp.ClientResponse:
        for repo in repositories:
            await self.ensure_repository_indexed(
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

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=self.headers
            ) as response:
                response.raise_for_status()
                return await response.json()

    def query(
        self,
        messages: List[Dict[str, str]],
        repositories: List[Dict[str, str]],
        session_id: Optional[str] = None,
        stream: bool = False,
        genius: bool = True,
    ) -> requests.Response:
        return asyncio.run(
            self.query_async(messages, repositories, session_id, stream, genius)
        )
