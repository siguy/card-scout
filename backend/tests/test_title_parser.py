from backend.title_parser import parse_title


def test_lebron_psa_10_rookie():
    c = parse_title("2003 Topps Chrome LeBron James #111 ROOKIE RC PSA 10 GEM MINT", "LeBron James")
    assert c.year == 2003
    assert c.brand == "Topps Chrome"
    assert c.card_type in {"Rookie", "Refractor Rookie"}
    assert c.graded and c.grader == "PSA" and c.grade == 10.0


def test_luka_silver_prizm_rookie():
    c = parse_title("2018-19 Luka Doncic Panini Prizm Silver Prizm RC #280 PSA 10", "Luka Doncic")
    assert c.year == 2018
    assert c.brand == "Panini Prizm"
    assert c.card_type == "Silver Prizm Rookie"
    assert c.graded and c.grade == 10.0


def test_raw_card_has_no_grader():
    c = parse_title("2023 Panini Prizm Victor Wembanyama Silver Prizm Rookie RC", "Victor Wembanyama")
    assert not c.graded
    assert c.grader is None
    assert c.grade is None


def test_jordan_psa_8_fleer():
    c = parse_title("1986 Fleer Michael Jordan Rookie Card RC #57 PSA 8 NM-MT", "Michael Jordan")
    assert c.year == 1986
    assert c.brand == "Fleer"
    assert c.graded and c.grader == "PSA" and c.grade == 8.0
