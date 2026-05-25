import os
import base64
import logging
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

# Setup clear logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load local .env variables
load_dotenv()

class EbayClient:
    def __init__(self):
        """Initializes the eBay Client and dynamically configures Sandbox vs Production."""
        self.client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
        
        # 1. Dynamic Environment Detection based on "SBX" presence
        if "SBX" in self.client_id:
            self.env_name = "Sandbox"
            self.base_url = "https://api.sandbox.ebay.com"
            self.oauth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        else:
            self.env_name = "Production"
            self.base_url = "https://api.ebay.com"
            self.oauth_url = "https://api.ebay.com/identity/v1/oauth2/token"
            
        self.access_token: Optional[str] = None
        logging.info(f"🔌 EBAY CLIENT: Initialized in [{self.env_name}] mode.")

    def _get_auth_header(self) -> str:
        """Constructs the Base64 Basic Authorization header for client credentials."""
        credentials_str = f"{self.client_id}:{self.client_secret}"
        encoded_bytes = base64.b64encode(credentials_str.encode("utf-8"))
        encoded_str = encoded_bytes.decode("utf-8")
        return f"Basic {encoded_str}"

    def authenticate(self) -> bool:
        """Executes the OAuth 2.0 Client Credentials flow to secure an Application Access Token."""
        if not self.client_id or not self.client_secret:
            logging.error("❌ EBAY CLIENT: Missing EBAY_CLIENT_ID or EBAY_CLIENT_SECRET in .env!")
            return False

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": self._get_auth_header()
        }
        
        # Requests a general application access token
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }

        try:
            logging.info(f"🔑 EBAY CLIENT: Sending OAuth request to {self.oauth_url}...")
            response = requests.post(self.oauth_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                payload = response.json()
                self.access_token = payload.get("access_token")
                logging.info("✅ EBAY CLIENT: Handshake completed successfully. Access token cached.")
                return True
            else:
                logging.error(f"❌ EBAY CLIENT: Authentication failed! HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ EBAY CLIENT: Exception during authentication: {e}")
            return False

    def search_listings(self, query: str, limit: int = 5) -> List[Dict]:
        """Queries the RESTful eBay Browse API for active auction listings.
        
        Args:
            query: The keyword search query (e.g. 'LeBron James Rookie Topps Chrome')
            limit: The maximum number of results to fetch
        """
        # Ensure we are authenticated
        if not self.access_token:
            success = self.authenticate()
            if not success:
                logging.warning("⚠️ EBAY CLIENT: Skipping search due to authentication failure.")
                return []

        search_endpoint = f"{self.base_url}/buy/browse/v1/item_summary/search"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # We search specifically for auctions to align with the sniper agent
        params = {
            "q": query,
            "filter": "buyingOptions:{AUCTION}",
            "limit": limit
        }

        try:
            logging.info(f"🔍 EBAY CLIENT: Searching active auctions for '{query}' in [{self.env_name}]...")
            response = requests.get(search_endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("itemSummaries", [])
                logging.info(f"✅ EBAY CLIENT: Located {len(items)} items matching '{query}'.")
                return items
            else:
                logging.error(f"❌ EBAY CLIENT: Search failed! HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"❌ EBAY CLIENT: Exception during search request: {e}")
            return []

# Dynamic Interactive dry-run check
if __name__ == "__main__":
    print("\n=======================================================")
    print("      COOPER'S CORNER: EBAY REST CLIENT DRY-RUN")
    print("=======================================================\n")
    client = EbayClient()
    print(f"Detected environment: {client.env_name}")
    print(f"Targeting OAuth server: {client.oauth_url}\n")
    
    print("Step 1: Attempting to secure Application Access Token...")
    if client.authenticate():
        print(f"\n🔑 SUCCESS! Token secured (Truncated): {client.access_token[:30]}...")
        
        print("\nStep 2: Searching active sandbox auctions for 'Michael Jordan Fleer'...")
        results = client.search_listings("Michael Jordan Fleer", limit=2)
        print(f"\nFound {len(results)} items in Sandbox.")
        for item in results:
            print(f" - Title: {item.get('title')}")
            print(f"   Price: {item.get('price', {}).get('value')} {item.get('price', {}).get('currency')}")
            print(f"   Item Link: {item.get('itemWebUrl')}\n")
    else:
        print("\n❌ Handshake failed. Please verify credentials in your .env file.")
    print("=======================================================\n")
