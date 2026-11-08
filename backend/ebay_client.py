"""Thin client over eBay's OAuth + Browse API.

Auth: client_credentials grant gives us an application-level token good for
~2 hours. We refresh on 401.

Env: if EBAY_CLIENT_ID contains "SBX" we target sandbox, else production.
"""
from __future__ import annotations

import base64
import logging
import os
import time
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("ebay_client")


class EbayClient:
    def __init__(self) -> None:
        self.client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
        if "SBX" in self.client_id:
            self.env_name = "Sandbox"
            self.base_url = "https://api.sandbox.ebay.com"
        else:
            self.env_name = "Production"
            self.base_url = "https://api.ebay.com"
        self.oauth_url = f"{self.base_url}/identity/v1/oauth2/token"
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    def _basic_auth(self) -> str:
        creds = f"{self.client_id}:{self.client_secret}".encode()
        return "Basic " + base64.b64encode(creds).decode()

    def authenticate(self) -> bool:
        if not self.client_id or not self.client_secret:
            log.error("Missing EBAY_CLIENT_ID / EBAY_CLIENT_SECRET. Set them in .env or environment.")
            return False
        try:
            resp = requests.post(
                self.oauth_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": self._basic_auth(),
                },
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope",
                },
                timeout=10,
            )
        except requests.RequestException as exc:
            log.error("eBay OAuth network error: %s", exc)
            return False
        if resp.status_code != 200:
            log.error("eBay OAuth failed: HTTP %s — %s", resp.status_code, resp.text[:300])
            return False
        body = resp.json()
        self._token = body["access_token"]
        self._token_expires_at = time.time() + body.get("expires_in", 7200) - 60
        log.info("eBay auth OK (%s).", self.env_name)
        return True

    def _token_ok(self) -> bool:
        return bool(self._token) and time.time() < self._token_expires_at

    def search_auctions(self, query: str, limit: int = 10) -> List[Dict]:
        if not self._token_ok() and not self.authenticate():
            return []
        url = f"{self.base_url}/buy/browse/v1/item_summary/search"
        headers = {"Authorization": f"Bearer {self._token}"}
        params = {
            "q": query,
            "filter": "buyingOptions:{AUCTION}",
            "limit": limit,
        }
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
        except requests.RequestException as exc:
            log.error("eBay search network error: %s", exc)
            return []
        if resp.status_code == 401:
            # Token may have expired; refresh once.
            if self.authenticate():
                headers["Authorization"] = f"Bearer {self._token}"
                resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            log.error("eBay search failed %s: %s", resp.status_code, resp.text[:300])
            return []
        return resp.json().get("itemSummaries", [])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    c = EbayClient()
    print("Env:", c.env_name)
    if c.authenticate():
        for item in c.search_auctions("Luka Doncic Prizm Silver Rookie PSA 10", limit=3):
            print("-", item.get("title"), "@", item.get("price", {}).get("value"))
