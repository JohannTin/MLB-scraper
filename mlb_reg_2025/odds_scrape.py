import json
import re
import csv
from datetime import datetime

# Add your team name to code mapping here
TEAM_CODE_MAP = {
    "Arizona Diamondbacks": "ARI",
    "Arizona": "ARI",
    "Atlanta Braves": "ATL",
    "Atlanta": "ATL",
    "Baltimore Orioles": "BAL",
    "Baltimore": "BAL",
    "Boston Red Sox": "BOS",
    "Boston": "BOS",
    "Chicago White Sox": "CWS",
    "Chi. White Sox": "CWS",
    "White Sox": "CWS",
    "Chicago Cubs": "CHC",
    "Chi. Cubs": "CHC",
    "Cubs": "CHC",
    "Cincinnati Reds": "CIN",
    "Cincinnati": "CIN",
    "Cleveland Guardians": "CLE",
    "Cleveland": "CLE",
    "Colorado Rockies": "COL",
    "Colorado": "COL",
    "Detroit Tigers": "DET",
    "Detroit": "DET",
    "Houston Astros": "HOU",
    "Houston": "HOU",
    "Kansas City Royals": "KC",
    "Kansas City": "KC",
    "Los Angeles Angels": "LAA",
    "LA Angels": "LAA",
    "Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "LA Dodgers": "LAD",
    "Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Miami": "MIA",
    "Milwaukee Brewers": "MIL",
    "Milwaukee": "MIL",
    "Minnesota Twins": "MIN",
    "Minnesota": "MIN",
    "New York Yankees": "NYY",
    "NY Yankees": "NYY",
    "Yankees": "NYY",
    "New York Mets": "NYM",
    "NY Mets": "NYM",
    "Mets": "NYM",
    "Oakland Athletics": "OAK",
    "Oakland": "OAK",
    "Philadelphia Phillies": "PHI",
    "Philadelphia": "PHI",
    "Pittsburgh Pirates": "PIT",
    "Pittsburgh": "PIT",
    "San Diego Padres": "SD",
    "San Diego": "SD",
    "San Francisco Giants": "SF",
    "San Francisco": "SF",
    "Seattle Mariners": "SEA",
    "Seattle": "SEA",
    "St. Louis Cardinals": "STL",
    "St. Louis": "STL",
    "Tampa Bay Rays": "TB",
    "Tampa Bay": "TB",
    "Texas Rangers": "TEX",
    "Texas": "TEX",
    "Toronto Blue Jays": "TOR",
    "Toronto": "TOR",
    "Washington Nationals": "WSH",
    "Washington": "WSH"
}

def extract_odds_from_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        raise ValueError("Could not find embedded JSON data in HTML.")

    data = json.loads(match.group(1))
    games = data["props"]["pageProps"]["oddsTables"][0]["oddsTableModel"]["gameRows"]

    results = []
    for game in games:
        gv = game["gameView"]
        # Convert date from yyyy-mm-dd to dd-mm-yyyy
        date_iso = gv["startDate"][:10]
        date = datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d-%m-%Y")
        team1_full = gv["awayTeam"]["displayName"]
        team2_full = gv["homeTeam"]["displayName"]
        team1 = TEAM_CODE_MAP.get(team1_full, team1_full)
        team2 = TEAM_CODE_MAP.get(team2_full, team2_full)
        pitcher1 = f"{gv['awayStarter']['firstName']} {gv['awayStarter']['lastName']}"
        pitcher2 = f"{gv['homeStarter']['firstName']} {gv['homeStarter']['lastName']}"
        # Find bet365 odds
        bet365 = next((o for o in game["oddsViews"] if o and o.get("sportsbook") == "bet365"), None)
        if bet365:
            odds = bet365["currentLine"]
            away_odds = odds['awayOdds']
            home_odds = odds['homeOdds']
        else:
            away_odds = "N/A"
            home_odds = "N/A"
        results.append({
            "date": date,
            "team1": team1,
            "team2": team2,
            "pitcher1": pitcher1,
            "pitcher2": pitcher2,
            "away_odds": away_odds,
            "home_odds": home_odds
        })
    return results

def save_to_csv(data, csv_path):
    if not data:
        print("No data to save.")
        return
    keys = data[0].keys()
    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    games = extract_odds_from_html("odds/march18odds")
    save_to_csv(games, "odds/march18odds.csv")
    print(f"Saved {len(games)} games to odds/march18odds.csv")