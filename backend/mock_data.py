import random
import re
import logging
from datetime import datetime, timedelta
from typing import List, Tuple
from models import CardModel, HistoricalComp, ActiveListing
from ebay_client import EbayClient

# Setup clean logging output
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Standard definitions of top players and cards for mock database and FMV catalogs
ROSTER = {
    "LeBron James": [
        {"year": 2003, "brand": "Topps Chrome", "card_type": "Rookie Card", "fmv_raw": 1800, "fmv_graded_10": 9500, "fmv_graded_9": 4200},
        {"year": 2012, "brand": "Panini Prizm", "card_type": "Silver Prizm", "fmv_raw": 250, "fmv_graded_10": 1100, "fmv_graded_9": 500},
        {"year": 2020, "brand": "Panini Prizm", "card_type": "Base Card", "fmv_raw": 15, "fmv_graded_10": 85, "fmv_graded_9": 35}
    ],
    "Victor Wembanyama": [
        {"year": 2023, "brand": "Panini Prizm", "card_type": "Silver Prizm Rookie", "fmv_raw": 180, "fmv_graded_10": 850, "fmv_graded_9": 350},
        {"year": 2023, "brand": "Panini Select", "card_type": "Rookie Autograph", "fmv_raw": 750, "fmv_graded_10": 3200, "fmv_graded_9": 1400}
    ],
    "Stephen Curry": [
        {"year": 2009, "brand": "Topps Chrome", "card_type": "Rookie Refractor", "fmv_raw": 3000, "fmv_graded_10": 16500, "fmv_graded_9": 7500},
        {"year": 2012, "brand": "Panini Prizm", "card_type": "Base Card", "fmv_raw": 80, "fmv_graded_10": 420, "fmv_graded_9": 180}
    ],
    "Michael Jordan": [
        {"year": 1986, "brand": "Fleer", "card_type": "Rookie Card", "fmv_raw": 2200, "fmv_graded_10": 120000, "fmv_graded_9": 17500, "fmv_graded_8": 6200},
        {"year": 1996, "brand": "Topps Chrome", "card_type": "Base Card", "fmv_raw": 120, "fmv_graded_10": 950, "fmv_graded_9": 300}
    ],
    "Kobe Bryant": [
        {"year": 1996, "brand": "Topps Chrome", "card_type": "Rookie Card", "fmv_raw": 400, "fmv_graded_10": 2400, "fmv_graded_9": 850},
        {"year": 2008, "brand": "Topps", "card_type": "Kobe/LeBron Duel", "fmv_raw": 150, "fmv_graded_10": 780, "fmv_graded_9": 320}
    ],
    "Luka Doncic": [
        {"year": 2018, "brand": "Panini Prizm", "card_type": "Silver Prizm Rookie", "fmv_raw": 220, "fmv_graded_10": 980, "fmv_graded_9": 410}
    ],
    "Nikola Jokic": [
        {"year": 2015, "brand": "Panini Prizm", "card_type": "Rookie Card", "fmv_raw": 110, "fmv_graded_10": 650, "fmv_graded_9": 280}
    ],
    "Anthony Edwards": [
        {"year": 2020, "brand": "Panini Prizm", "card_type": "Silver Prizm Rookie", "fmv_raw": 350, "fmv_graded_10": 1600, "fmv_graded_9": 750}
    ]
}

def generate_comps(card: CardModel, base_fmv: float) -> List[HistoricalComp]:
    """Generates 5 realistic comps with +/- 8% random variance around base FMV."""
    comps = []
    sources = ["eBay Sold", "PWCC Vault", "Goldin Auctions", "Card Ladder"]
    for i in range(5):
        variance = random.uniform(-0.08, 0.08)
        sale_price = round(base_fmv * (1 + variance), 2)
        sale_date = datetime.now() - timedelta(days=random.randint(1, 45))
        comps.append(HistoricalComp(
            card=card,
            sale_price=sale_price,
            sale_date=sale_date,
            source=random.choice(sources),
            url=f"https://www.ebay.com/itm/sold-example-{random.randint(100000, 999999)}"
        ))
    return comps

def get_fmv(player: str, year: int, brand: str, card_type: str, graded: bool, grader: str, grade: float) -> float:
    """Retrieves the base FMV from the spec catalog based on grading/rarity rules."""
    cards_list = ROSTER.get(player, [])
    for c in cards_list:
        # Check matching year, brand, and type
        if c["year"] == year and c["brand"].lower() in brand.lower() and c["card_type"].lower() in card_type.lower():
            if not graded:
                return c["fmv_raw"]
            if grade == 10.0:
                return c["fmv_graded_10"]
            elif grade == 9.0 or grade == 9.5:
                return c.get("fmv_graded_9", c["fmv_graded_10"] * 0.45)
            elif grade == 8.0:
                return c.get("fmv_graded_8", c.get("fmv_graded_9", c["fmv_graded_10"] * 0.45) * 0.6)
            return c["fmv_raw"] * 2.5
            
    # Default fallback calculation if not specifically in database catalog
    base = 150.0
    if graded and grade == 10.0:
        base *= 5.0
    elif graded:
        base *= 2.0
    return base

def parse_card_from_title(title: str, query_player: str) -> CardModel:
    """Parses key card attributes from raw eBay listing titles using regex.
    
    This is an educational text-parser showing Cooper how string indexing, 
    lowercasing, and regex pattern matching convert unstructured marketplace 
    data into clean database objects!
    """
    title_lower = title.lower()
    
    # 1. Player Name
    player = query_player
    for name in ROSTER.keys():
        if name.lower() in title_lower:
            player = name
            break
            
    # 2. Year detection (looks for 4 digit sequences)
    year = 2023
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", title)
    if years:
        year = int(years[0])
        
    # 3. Brand detection
    brand = "Panini Prizm"
    for b in ["topps chrome", "topps", "panini prizm", "prizm", "fleer", "select", "upper deck", "donruss", "optic"]:
        if b in title_lower:
            if b == "prizm":
                brand = "Panini Prizm"
            elif b == "optic":
                brand = "Panini Donruss Optic"
            else:
                brand = b.title()
            break
            
    # 4. Card Type detection
    card_type = "Base Card"
    if "rookie" in title_lower or "rc" in title_lower:
        card_type = "Rookie Card"
    elif "refractor" in title_lower:
        card_type = "Rookie Refractor" if "rookie" in title_lower or "rc" in title_lower else "Refractor"
    elif "silver" in title_lower:
        card_type = "Silver Prizm Rookie" if "rookie" in title_lower or "rc" in title_lower else "Silver Prizm"
    elif "autograph" in title_lower or "auto" in title_lower:
        card_type = "Autograph"
        
    # 5. Graded card parsing
    graded = False
    grader = None
    grade = None
    
    if "psa" in title_lower:
        graded = True
        grader = "PSA"
    elif "bgs" in title_lower or "beckett" in title_lower:
        graded = True
        grader = "BGS"
    elif "sgc" in title_lower:
        graded = True
        grader = "SGC"
        
    if graded:
        grades = re.findall(r"\b(10|9\.5|9|8\.5|8|7)\b", title)
        if grades:
            grade = float(grades[0])
        else:
            grade = 10.0 # Standard gem mint assumption
            
    return CardModel(
        player_name=player,
        year=year,
        brand=brand,
        card_type=card_type,
        graded=graded,
        grader=grader,
        grade=grade
    )

def get_real_listings() -> List[Tuple[ActiveListing, float]]:
    """Returns active listings mapped from either live eBay REST API queries 
    or our high-fidelity basketball simulator fallback.
    """
    listings = []
    ebay = EbayClient()
    
    # Check if we can successfully complete the OAuth handshake
    if ebay.authenticate():
        try:
            # Monitored queries to run in Sandbox
            search_queries = [
                ("LeBron James Topps Chrome", "LeBron James"),
                ("Victor Wembanyama Prizm", "Victor Wembanyama"),
                ("Michael Jordan Fleer", "Michael Jordan"),
                ("Anthony Edwards Prizm", "Anthony Edwards")
            ]
            
            raw_items = []
            for query, player in search_queries:
                items = ebay.search_listings(query, limit=2)
                for item in items:
                    raw_items.append((item, player))
                    
            if raw_items:
                logging.info(f"🔌 EBAY API: Mapping {len(raw_items)} live auctions from Sandbox...")
                for item, player in raw_items:
                    price_val = float(item.get("price", {}).get("value", "0.0"))
                    
                    # Resolve shipping cost
                    shipping_cost = 0.0
                    shipping_options = item.get("shippingOptions", [])
                    if shipping_options:
                        shipping_cost = float(shipping_options[0].get("shippingCost", {}).get("value", "0.0"))
                        
                    # Resolve listing end date (convert ISO string to python datetime object)
                    end_time_str = item.get("itemEndDate", "")
                    if end_time_str:
                        # Convert Zulu to offsets for robust iso format parsing
                        end_time_str = end_time_str.replace("Z", "+00:00")
                        end_time = datetime.fromisoformat(end_time_str)
                    else:
                        end_time = datetime.now() + timedelta(minutes=random.randint(10, 180))
                        
                    # Parse card attributes from title
                    title = item.get("title", "Unknown sports card")
                    card = parse_card_from_title(title, player)
                    fmv = get_fmv(card.player_name, card.year, card.brand, card.card_type, card.graded, card.grader, card.grade)
                    
                    # Convert to active listing
                    listings.append((ActiveListing(
                        listing_id=item.get("itemId", f"ebay-{random.randint(100, 999)}"),
                        title=title,
                        card=card,
                        current_price=price_val,
                        buy_it_now=False,
                        end_time=end_time,
                        shipping_cost=shipping_cost,
                        url=item.get("itemWebUrl", "https://www.ebay.com"),
                        image_url=item.get("image", {}).get("imageUrl")
                    ), fmv))
                
                return listings
                
        except Exception as e:
            logging.error(f"⚠️ EBAY API: Error parsing live API responses: {e}")
            
    # FAIL-SAFE FALLBACK STRATEGY (Engages if sandbox is empty or credentials fail)
    logging.info("⚠️ EBAY API: Empty Sandbox or authentication error. Engaging premium simulated roster fallback.")
    
    # 1. LeBron James 2003 Topps Chrome Rookie PSA 10 (GOOD DEAL!)
    card1 = CardModel(player_name="LeBron James", year=2003, brand="Topps Chrome", card_type="Rookie Card", graded=True, grader="PSA", grade=10.0)
    fmv1 = get_fmv("LeBron James", 2003, "Topps Chrome", "Rookie Card", True, "PSA", 10.0)
    listings.append((ActiveListing(
        listing_id="ebay-101",
        title="2003 Topps Chrome LeBron James #111 ROOKIE RC PSA 10 GEM MINT L@@K!",
        card=card1,
        current_price=6950.00,  # Undervalued vs $9500 FMV
        buy_it_now=False,
        end_time=datetime.now() + timedelta(minutes=4),
        shipping_cost=15.00,
        url="https://www.ebay.com/itm/111000101",
        image_url="https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"
    ), fmv1))

    # 2. Victor Wembanyama 2023 Panini Prizm Silver PSA 10 (GOOD DEAL!)
    card2 = CardModel(player_name="Victor Wembanyama", year=2023, brand="Panini Prizm", card_type="Silver Prizm Rookie", graded=True, grader="PSA", grade=10.0)
    fmv2 = get_fmv("Victor Wembanyama", 2023, "Panini Prizm", "Silver Prizm Rookie", True, "PSA", 10.0)
    listings.append((ActiveListing(
        listing_id="ebay-102",
        title="2023 Panini Prizm Victor Wembanyama Silver Prizm #136 Rookie PSA 10",
        card=card2,
        current_price=580.00,  # Undervalued vs $850 FMV
        buy_it_now=False,
        end_time=datetime.now() + timedelta(minutes=18),
        shipping_cost=5.00,
        url="https://www.ebay.com/itm/111000102",
        image_url="https://images.unsplash.com/photo-1519766304817-4f37bda74a27?w=500"
    ), fmv2))

    # 3. Michael Jordan 1986 Fleer Rookie PSA 8 (GREAT SNIPE DEAL!)
    card3 = CardModel(player_name="Michael Jordan", year=1986, brand="Fleer", card_type="Rookie Card", graded=True, grader="PSA", grade=8.0)
    fmv3 = get_fmv("Michael Jordan", 1986, "Fleer", "Rookie Card", True, "PSA", 8.0)
    listings.append((ActiveListing(
        listing_id="ebay-103",
        title="1986 Fleer Michael Jordan Rookie Card RC #57 PSA 8 NM-MT - Beautiful Centering",
        card=card3,
        current_price=4150.00,  # Undervalued vs $6200 FMV
        buy_it_now=False,
        end_time=datetime.now() + timedelta(seconds=25),  # 3s sniping opportunity
        shipping_cost=25.00,
        url="https://www.ebay.com/itm/111000103",
        image_url="https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=500"
    ), fmv3))

    # 4. Anthony Edwards 2020 Panini Prizm Silver PSA 10 (GOOD DEAL!)
    card4 = CardModel(player_name="Anthony Edwards", year=2020, brand="Panini Prizm", card_type="Silver Prizm Rookie", graded=True, grader="PSA", grade=10.0)
    fmv4 = get_fmv("Anthony Edwards", 2020, "Panini Prizm", "Silver Prizm Rookie", True, "PSA", 10.0)
    listings.append((ActiveListing(
        listing_id="ebay-105",
        title="2020 Panini Prizm Anthony Edwards Silver Prizm RC #258 PSA 10 Gem Mint",
        card=card4,
        current_price=1180.00,  # Undervalued vs $1600 FMV
        buy_it_now=False,
        end_time=datetime.now() + timedelta(minutes=45),
        shipping_cost=10.00,
        url="https://www.ebay.com/itm/111000105",
        image_url="https://images.unsplash.com/photo-1505666287802-931dc83948e9?w=500"
    ), fmv4))

    return listings

if __name__ == "__main__":
    print("\n--- Card Scout Listing Fetcher Test ---")
    data = get_real_listings()
    print(f"Successfully loaded {len(data)} items for evaluation.")
    for item, fmv in data:
        print(f" - Title: {item.title}")
        print(f"   Price: ${item.current_price:.2f} | Comps FMV: ${fmv:.2f}")
