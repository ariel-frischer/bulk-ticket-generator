import requests
from typing import List, Dict, Optional
import streamlit as st
import os


class GreptileAPI:
    def __init__(self):
        self.url = "https://api.greptile.com/v2/query"
        self.headers = {
            "Authorization": f"Bearer {os.environ.get('GREPTILE_API_KEY') or st.session_state.greptile_api_key}",
            "X-GitHub-Token": os.environ.get('GITHUB_TOKEN') or st.session_state.github_token,
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
        payload = {
            "messages": messages,
            "repositories": repositories,
            "sessionId": session_id,
            "stream": stream,
            "genius": genius,
        }

        response = requests.post(self.url, json=payload, headers=self.headers)
        return response
