import random
from datetime import datetime, timedelta
from typing import List, Tuple
from models import CardModel, HistoricalComp, ActiveListing, DetectedDeal

# Standard definitions of top players and cards
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
    ]
}

def generate_comps(card: CardModel, base_fmv: float) -> List[HistoricalComp]:
    """Generates 5 realistic comps with +/- 10% random variance around base FMV."""
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
    """Retrieves the hardcoded base FMV from the spec configs."""
    cards_list = ROSTER.get(player, [])
    for c in cards_list:
        if c["year"] == year and c["brand"] == brand and c["card_type"] == card_type:
            if not graded:
                return c["fmv_raw"]
            if grade == 10.0:
                return c["fmv_graded_10"]
            elif grade == 9.0 or grade == 9.5:
                return c.get("fmv_graded_9", c["fmv_graded_10"] * 0.45)
            elif grade == 8.0:
                return c.get("fmv_graded_8", c.get("fmv_graded_9", c["fmv_graded_10"] * 0.45) * 0.6)
            return c["fmv_raw"] * 2.5
    return 100.0  # Default fallback

def get_real_listings() -> List[Tuple[ActiveListing, float]]:
    """Returns list of active listings with their matching True Fair Market Value."""
    listings = []
    
    # 1. LeBron James 2003 Topps Chrome Rookie PSA 10 (GOOD DEAL!)
    card1 = CardModel(player_name="LeBron James", year=2003, brand="Topps Chrome", card_type="Rookie Card", graded=True, grader="PSA", grade=10.0)
    fmv1 = get_fmv("LeBron James", 2003, "Topps Chrome", "Rookie Card", True, "PSA", 10.0)
    listings.append((ActiveListing(
        listing_id="ebay-101",
        title="2003 Topps Chrome LeBron James #111 ROOKIE RC PSA 10 GEM MINT L@@K!",
        card=card1,
        current_price=6950.00,  # Highly undervalued vs $9500 FMV
        buy_it_now=False,
        end_time=datetime.now() + timedelta(minutes=4),  # Ends very soon!
        shipping_cost=15.00,
        url="https://www.ebay.com/itm/111000101",
        image_url="https://images.unsplash.com/photo-1546519638-68e109498ffc?w=500"  # Sports action photo placeholder
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
        end_time=datetime.now() + timedelta(seconds=25),  # Sniping opportunity right away!
        shipping_cost=25.00,
        url="https://www.ebay.com/itm/111000103",
        image_url="https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=500"
    ), fmv3))

    # 4. Stephen Curry 2009 Topps Chrome Rookie Refractor PSA 9 (Fairly Priced)
    card4 = CardModel(player_name="Stephen Curry", year=2009, brand="Topps Chrome", card_type="Rookie Refractor", graded=True, grader="PSA", grade=9.0)
    fmv4 = get_fmv("Stephen Curry", 2009, "Topps Chrome", "Rookie Refractor", True, "PSA", 9.0)
    listings.append((ActiveListing(
        listing_id="ebay-104",
        title="2009 Stephen Curry Topps Chrome Refractor Rookie /499 PSA 9 MINT",
        card=card4,
        current_price=7400.00,  # Fair price vs $7500 FMV
        buy_it_now=False,
        end_time=datetime.now() + timedelta(hours=3),
        shipping_cost=10.00,
        url="https://www.ebay.com/itm/111000104",
        image_url="https://images.unsplash.com/photo-1505666287802-931dc83948e9?w=500"
    ), fmv4))

    # 5. Luka Doncic 2018 Panini Prizm Silver PSA 10 (GOOD DEAL!)
    card5 = CardModel(player_name="Luka Doncic", year=2018, brand="Panini Prizm", card_type="Silver Prizm Rookie", graded=True, grader="PSA", grade=10.0)
    fmv5 = get_fmv("Luka Doncic", 2018, "Panini Prizm", "Silver Prizm Rookie", True, "PSA", 10.0)
    listings.append((ActiveListing(
        listing_id="ebay-105",
        title="2018-19 Luka Doncic Panini Prizm Silver Prizm RC #280 PSA 10 GEM MINT",
        card=card5,
        current_price=690.00,  # Undervalued vs $980 FMV
        buy_it_now=False,
        end_time=datetime.now() + timedelta(minutes=45),
        shipping_cost=5.00,
        url="https://www.ebay.com/itm/111000105",
        image_url="https://images.unsplash.com/photo-1608245365831-2451976ab5a4?w=500"
    ), fmv5))

    return listings
