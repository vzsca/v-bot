"""
Twitch API client.
"""

import os

import aiohttp


class TwitchAPI:
    def __init__(self):
        self.client_id = os.getenv("TWITCH_CLIENT_ID")
        self.client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        self.access_token = None

    async def authenticate(self) -> bool:
        if not self.client_id or not self.client_secret:
            return False

        url = "https://id.twitch.tv/oauth2/token"

        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status != 200:
                    return False

                data = await response.json()
                self.access_token = data.get("access_token")

                return self.access_token is not None

    async def get_stream(self, username: str):
        if not self.access_token:
            if not await self.authenticate():
                return None

        url = "https://api.twitch.tv/helix/streams"

        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }

        params = {
            "user_login": username,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                params=params,
            ) as response:

                if response.status == 401:
                    self.access_token = None
                    return await self.get_stream(username)

                if response.status != 200:
                    return None

                data = await response.json()

                if not data.get("data"):
                    return None

                return data["data"][0]
