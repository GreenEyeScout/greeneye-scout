from auto_rosters import build_auto_rosters, find_pitcher
from inning import simulate_inning
from pitcher import Pitcher
import random
import requests
import statsapi
from datetime import datetime, timedelta


ODDS_API_KEY = "439bc802948590bfe717abda18d2421c"


BALLPARKS = {
    "Arizona Diamondbacks": {"lat": 33.445, "lon": -112.067, "name": "Chase Field", "roof": True, "pf": 1.04},
    "Atlanta Braves": {"lat": 33.891, "lon": -84.468, "name": "Truist Park", "roof": False, "pf": 1.01},
    "Baltimore Orioles": {"lat": 39.284, "lon": -76.622, "name": "Camden Yards", "roof": False, "pf": 1.03},
    "Boston Red Sox": {"lat": 42.346, "lon": -71.098, "name": "Fenway Park", "roof": False, "pf": 1.08},
    "Chicago Cubs": {"lat": 41.948, "lon": -87.656, "name": "Wrigley Field", "roof": False, "pf": 1.05},
    "Chicago White Sox": {"lat": 41.830, "lon": -87.634, "name": "Guaranteed Rate", "roof": False, "pf": 1.02},
    "Cincinnati Reds": {"lat": 39.097, "lon": -84.508, "name": "Great American BP", "roof": False, "pf": 1.06},
    "Cleveland Guardians": {"lat": 41.496, "lon": -81.685, "name": "Progressive Field", "roof": False, "pf": 0.98},
    "Colorado Rockies": {"lat": 39.756, "lon": -104.994, "name": "Coors Field", "roof": False, "pf": 1.30},
    "Detroit Tigers": {"lat": 42.339, "lon": -83.049, "name": "Comerica Park", "roof": False, "pf": 0.96},
    "Houston Astros": {"lat": 29.757, "lon": -95.355, "name": "Minute Maid Park", "roof": True, "pf": 1.03},
    "Kansas City Royals": {"lat": 39.051, "lon": -94.480, "name": "Kauffman Stadium", "roof": False, "pf": 1.00},
    "Los Angeles Angels": {"lat": 33.800, "lon": -117.883, "name": "Angel Stadium", "roof": False, "pf": 0.97},
    "Los Angeles Dodgers": {"lat": 34.074, "lon": -118.240, "name": "Dodger Stadium", "roof": False, "pf": 0.97},
    "Miami Marlins": {"lat": 25.778, "lon": -80.220, "name": "loanDepot Park", "roof": True, "pf": 0.90},
    "Milwaukee Brewers": {"lat": 43.028, "lon": -87.971, "name": "American Family", "roof": True, "pf": 1.02},
    "Minnesota Twins": {"lat": 44.982, "lon": -93.278, "name": "Target Field", "roof": False, "pf": 1.00},
    "New York Mets": {"lat": 40.757, "lon": -73.846, "name": "Citi Field", "roof": False, "pf": 0.94},
    "New York Yankees": {"lat": 40.829, "lon": -73.927, "name": "Yankee Stadium", "roof": False, "pf": 1.07},
    "Oakland Athletics": {"lat": 38.581, "lon": -121.494, "name": "Sutter Health Park", "roof": False, "pf": 1.00},
    "Philadelphia Phillies": {"lat": 39.906, "lon": -75.167, "name": "Citizens Bank Park", "roof": False, "pf": 1.05},
    "Pittsburgh Pirates": {"lat": 40.447, "lon": -80.006, "name": "PNC Park", "roof": False, "pf": 0.93},
    "San Diego Padres": {"lat": 32.707, "lon": -117.157, "name": "Petco Park", "roof": False, "pf": 0.92},
    "San Francisco Giants": {"lat": 37.778, "lon": -122.389, "name": "Oracle Park", "roof": False, "pf": 0.93},
    "Seattle Mariners": {"lat": 47.591, "lon": -122.333, "name": "T-Mobile Park", "roof": True, "pf": 0.93},
    "St. Louis Cardinals": {"lat": 38.623, "lon": -90.193, "name": "Busch Stadium", "roof": False, "pf": 0.97},
    "Tampa Bay Rays": {"lat": 27.768, "lon": -82.653, "name": "Tropicana Field", "roof": True, "pf": 0.95},
    "Texas Rangers": {"lat": 32.747, "lon": -97.083, "name": "Globe Life Field", "roof": True, "pf": 0.99},
    "Toronto Blue Jays": {"lat": 43.641, "lon": -79.389, "name": "Rogers Centre", "roof": True, "pf": 1.01},
    "Washington Nationals": {"lat": 38.873, "lon": -77.008, "name": "Nationals Park", "roof": False, "pf": 1.00},
}

TEAM_NAME_MAP = {
    "Arizona Diamondbacks": "Arizona Diamondbacks",
    "Atlanta Braves": "Atlanta Braves",
    "Baltimore Orioles": "Baltimore Orioles",
    "Boston Red Sox": "Boston Red Sox",
    "Chicago Cubs": "Chicago Cubs",
    "Chicago White Sox": "Chicago White Sox",
    "Cincinnati Reds": "Cincinnati Reds",
    "Cleveland Guardians": "Cleveland Guardians",
    "Colorado Rockies": "Colorado Rockies",
    "Detroit Tigers": "Detroit Tigers",
    "Houston Astros": "Houston Astros",
    "Kansas City Royals": "Kansas City Royals",
    "Los Angeles Angels": "Los Angeles Angels",
    "Los Angeles Dodgers": "Los Angeles Dodgers",
    "Miami Marlins": "Miami Marlins",
    "Milwaukee Brewers": "Milwaukee Brewers",
    "Minnesota Twins": "Minnesota Twins",
    "New York Mets": "New York Mets",
    "New York Yankees": "New York Yankees",
    "Oakland Athletics": "Oakland Athletics",
    "Philadelphia Phillies": "Philadelphia Phillies",
    "Pittsburgh Pirates": "Pittsburgh Pirates",
    "San Diego Padres": "San Diego Padres",
    "San Francisco Giants": "San Francisco Giants",
    "Seattle Mariners": "Seattle Mariners",
    "St. Louis Cardinals": "St. Louis Cardinals",
    "Tampa Bay Rays": "Tampa Bay Rays",
    "Texas Rangers": "Texas Rangers",
    "Toronto Blue Jays": "Toronto Blue Jays",
    "Washington Nationals": "Washington Nationals",
    "Athletics": "Oakland Athletics",
}


def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation,relative_humidity_2m&temperature_unit=fahrenheit&wind_speed_unit=mph"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        current = data["current"]
        return {"temp_f": current["temperature_2m"], "wind_mph": current["wind_speed_10m"],
                "precip": current["precipitation"], "humidity": current["relative_humidity_2m"]}
    except:
        return None


def calc_weather_modifier(weather, has_roof):
    if not weather or has_roof:
        return {"hr_mod": 1.0, "hit_mod": 1.0, "label": "🏟️  Dome/Roof closed"}
    temp = weather["temp_f"]
    wind = weather["wind_mph"]
    humidity = weather["humidity"]
    temp_mod = max(0.90, min(1.15, 1.0 + ((temp - 72) * 0.003)))
    wind_mod = max(0.92, min(1.10, 1.0 + (wind * 0.002 * random.choice([-1, 1]))))
    humid_mod = max(0.97, min(1.03, 1.0 - ((humidity - 50) * 0.0005)))
    hr_mod = temp_mod * wind_mod * humid_mod
    hit_mod = max(0.97, min(1.05, 1.0 + ((temp - 72) * 0.001)))
    if weather["precip"] > 0:
        label = f"🌧️  {temp:.0f}°F, {wind:.0f}mph wind, Rain!"
    elif temp > 90:
        label = f"🔥 {temp:.0f}°F, {wind:.0f}mph wind, Hot!"
    elif temp < 55:
        label = f"🥶 {temp:.0f}°F, {wind:.0f}mph wind, Cold!"
    else:
        label = f"☀️  {temp:.0f}°F, {wind:.0f}mph wind"
    return {"hr_mod": hr_mod, "hit_mod": hit_mod, "label": label}


def prob_to_moneyline(prob):
    if prob <= 0 or prob >= 1:
        return "+100"
    if prob >= 0.5:
        return f"{-round((prob / (1 - prob)) * 100)}"
    else:
        return f"+{round(((1 - prob) / prob) * 100)}"


def moneyline_to_prob(ml):
    if ml < 0:
        return abs(ml) / (abs(ml) + 100)
    else:
        return 100 / (ml + 100)


def get_live_odds():
    if ODDS_API_KEY == "YOUR_KEY_HERE":
        return None
    try:
        url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/"
        params = {"apiKey": ODDS_API_KEY, "regions": "us", "markets": "h2h,totals", "oddsFormat": "american"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        odds_by_game = {}
        for game in data:
            home = TEAM_NAME_MAP.get(game.get("home_team", ""), game.get("home_team", ""))
            away = TEAM_NAME_MAP.get(game.get("away_team", ""), game.get("away_team", ""))
            key = f"{away}@{home}"
            best = {"home_ml": None, "away_ml": None, "total": None}
            for book in game.get("bookmakers", [])[:1]:
                for market in book.get("markets", []):
                    if market["key"] == "h2h":
                        for outcome in market["outcomes"]:
                            mapped = TEAM_NAME_MAP.get(outcome["name"], outcome["name"])
                            if mapped == home:
                                best["home_ml"] = outcome["price"]
                            elif mapped == away:
                                best["away_ml"] = outcome["price"]
                    elif market["key"] == "totals":
                        for outcome in market["outcomes"]:
                            if outcome["name"] == "Over":
                                best["total"] = outcome.get("point", None)
                                break
            odds_by_game[key] = best
        return odds_by_game
    except Exception as e:
        print(f"⚠️  Could not fetch odds: {e}")
        return None


def simulate_game_quick(home_batters, home_pitcher, home_bullpen,
                        away_batters, away_pitcher, away_bullpen,
                        park_factor=1.0):
    home_score = 0
    away_score = 0
    away_idx = 0
    home_idx = 0
    cur_home_p = home_pitcher
    cur_away_p = away_pitcher

    for inning in range(1, 19):
        if inning == 7:
            if home_bullpen:
                cur_home_p = home_bullpen[0]
            if away_bullpen:
                cur_away_p = away_bullpen[0]

        away_runs, away_idx, _ = simulate_inning(away_batters, cur_home_p, away_idx, None,
            home_team=False, quiet=True, park_factor=park_factor)
        away_score += away_runs

        # Walk-off: skip bottom half if home team already leads in 9th+
        if inning >= 9 and home_score > away_score:
            break

        home_runs, home_idx, _ = simulate_inning(home_batters, cur_away_p, home_idx, None,
            home_team=True, quiet=True, park_factor=park_factor)
        home_score += home_runs

        if inning >= 9 and home_score != away_score:
            break

    return home_score, away_score


def get_todays_games(date=None):
    if date is None:
        date = datetime.now().strftime('%m/%d/%Y')
    print(f"📅 Fetching MLB schedule for {date}...")
    sched = statsapi.schedule(date=date)
    games = []
    for game in sched:
        games.append({
            "away": game["away_name"],
            "home": game["home_name"],
            "away_pitcher": game.get("away_probable_pitcher", "TBD"),
            "home_pitcher": game.get("home_probable_pitcher", "TBD"),
        })
    return games


def run_monte_carlo(teams, home_name, away_name, num_sims, home_sp=None, away_sp=None):
    if home_name not in teams or away_name not in teams:
        return None
    home_data = teams[home_name]
    away_data = teams[away_name]

    actual_home_sp = home_sp if home_sp else home_data["starter"]
    actual_away_sp = away_sp if away_sp else away_data["starter"]

    park_factor = 1.0
    if home_name in BALLPARKS:
        park_factor = BALLPARKS[home_name]["pf"]

    home_wins = 0
    away_wins = 0
    total_home_runs = 0
    total_away_runs = 0
    total_runs_list = []
    home_rl_wins = 0
    away_rl_wins = 0

    for i in range(num_sims):
        home_score, away_score = simulate_game_quick(
            home_data["batters"], actual_home_sp, home_data["bullpen"],
            away_data["batters"], actual_away_sp, away_data["bullpen"],
            park_factor
        )
        total = home_score + away_score
        total_runs_list.append(total)
        total_home_runs += home_score
        total_away_runs += away_score
        if home_score > away_score:
            home_wins += 1
            if home_score - away_score >= 2:
                home_rl_wins += 1
        else:
            away_wins += 1
            if away_score - home_score >= 2:
                away_rl_wins += 1

    avg_total = sum(total_runs_list) / num_sims
    over_under = {}
    for line in [5.5, 6.5, 7.5, 8.5, 9.5, 10.5]:
        overs = sum(1 for t in total_runs_list if t > line)
        over_under[line] = overs / num_sims

    return {
        "home_pct": home_wins / num_sims,
        "away_pct": away_wins / num_sims,
        "avg_home_runs": total_home_runs / num_sims,
        "avg_away_runs": total_away_runs / num_sims,
        "avg_total": avg_total,
        "over_under": over_under,
        "home_rl": home_rl_wins / num_sims,
        "away_rl": away_rl_wins / num_sims,
        "home_sp_name": actual_home_sp.name,
        "away_sp_name": actual_away_sp.name,
        "park_factor": park_factor,
    }


def print_game_card(away_name, home_name, result, weather_info, game, ballpark_name, odds=None):
    print(f"\n  ⚾ {away_name} @ {home_name}")
    if ballpark_name:
        print(f"     📍 {ballpark_name} (Park Factor: {result['park_factor']:.2f})")
    if weather_info:
        print(f"     {weather_info['label']}")

    print(f"     🎯 SP: {result['away_sp_name']} vs {result['home_sp_name']}")
    if game:
        sched_away = game['away_pitcher']
        sched_home = game['home_pitcher']
        if sched_away != result['away_sp_name'] or sched_home != result['home_sp_name']:
            print(f"     📋 Scheduled: {sched_away} vs {sched_home}")

    away_ml = prob_to_moneyline(result['away_pct'])
    home_ml = prob_to_moneyline(result['home_pct'])

    print(f"     ┌──────────────────────────────────────────────────────┐")
    print(f"     │  MONEYLINE              SIM         MARKET    EDGE  │")

    if odds and odds.get("home_ml") is not None:
        home_market = moneyline_to_prob(odds["home_ml"])
        away_market = moneyline_to_prob(odds["away_ml"])
        home_edge = (result['home_pct'] - home_market) * 100
        away_edge = (result['away_pct'] - away_market) * 100
        he = f"+{home_edge:.1f}%" if home_edge > 0 else f"{home_edge:.1f}%"
        ae = f"+{away_edge:.1f}%" if away_edge > 0 else f"{away_edge:.1f}%"
        hs = " 🔥" if home_edge > 3 else ""
        as_ = " 🔥" if away_edge > 3 else ""
        print(f"     │  {away_name:<20} {result['away_pct']*100:5.1f}%  {away_market*100:5.1f}% ({odds['away_ml']:+d}) {ae:>6}{as_:<3}│")
        print(f"     │  {home_name:<20} {result['home_pct']*100:5.1f}%  {home_market*100:5.1f}% ({odds['home_ml']:+d}) {he:>6}{hs:<3}│")
    else:
        print(f"     │  {away_name:<20} {result['away_pct']*100:5.1f}%  ({away_ml:>5})               │")
        print(f"     │  {home_name:<20} {result['home_pct']*100:5.1f}%  ({home_ml:>5})               │")

    print(f"     │                                                      │")
    print(f"     │  RUN LINE (-1.5)                                     │")
    print(f"     │  {away_name:<20} {result['away_rl']*100:5.1f}%                          │")
    print(f"     │  {home_name:<20} {result['home_rl']*100:5.1f}%                          │")
    print(f"     │                                                      │")

    ou_line = ""
    if odds and odds.get("total"):
        ou_line = f"  Line: {odds['total']}"
    print(f"     │  TOTAL RUNS  (avg: {result['avg_total']:.1f}){ou_line:<25}│")

    for line in [6.5, 7.5, 8.5, 9.5]:
        over_pct = result['over_under'][line] * 100
        under_pct = 100 - over_pct
        print(f"     │    O/U {line}:  Over {over_pct:4.1f}% | Under {under_pct:4.1f}%              │")

    print(f"     │                                                      │")
    print(f"     │  PREDICTED SCORE: {result['avg_away_runs']:.1f} - {result['avg_home_runs']:.1f}                        │")
    print(f"     └──────────────────────────────────────────────────────┘")


def main():
    teams = build_auto_rosters()

    while True:
        print("\n" + "=" * 60)
        print("🎯 MLB PREDICTOR — Monte Carlo + Weather + Odds + Park Factors")
        print("=" * 60)
        print("\n  1. Predict TODAY's games")
        print("  2. Predict TOMORROW's games")
        print("  3. Predict a custom matchup")
        print("  0. Quit")

        choice = input("\nEnter choice: ").strip()

        if choice == "0":
            print("\nGoodbye! ⚾")
            return

        if choice in ["1", "2"]:
            if choice == "1":
                date = datetime.now().strftime('%m/%d/%Y')
                label = "TODAY"
            else:
                tomorrow = datetime.now() + timedelta(days=1)
                date = tomorrow.strftime('%m/%d/%Y')
                label = "TOMORROW"

            games = get_todays_games(date)
            if not games:
                print(f"\n❌ No games found for {date}")
                continue

            print(f"\n📅 {len(games)} games found for {label} ({date})")

            print("📊 Fetching live odds...")
            all_odds = get_live_odds()
            if all_odds:
                print(f"✅ Live odds loaded!")
            else:
                print("⚠️  Running without live odds")

            try:
                num_sims = int(input("\nSimulations per game? (default 10000): ").strip() or "10000")
            except ValueError:
                num_sims = 10000

            print(f"\n⏳ Running {num_sims} sims per game...\n")
            print(f"{'─' * 60}")

            edges = []

            for game in games:
                away_name = TEAM_NAME_MAP.get(game["away"], game["away"])
                home_name = TEAM_NAME_MAP.get(game["home"], game["home"])

                home_sp = None
                away_sp = None

                if game["home_pitcher"] != "TBD":
                    home_sp = find_pitcher(game["home_pitcher"])
                    if home_sp:
                        print(f"  ✅ Found {game['home_pitcher']} (ERA: {home_sp.era:.2f})")
                    else:
                        print(f"  ⚠️  {game['home_pitcher']} not found — using team default")

                if game["away_pitcher"] != "TBD":
                    away_sp = find_pitcher(game["away_pitcher"])
                    if away_sp:
                        print(f"  ✅ Found {game['away_pitcher']} (ERA: {away_sp.era:.2f})")
                    else:
                        print(f"  ⚠️  {game['away_pitcher']} not found — using team default")

                weather_info = None
                ballpark_name = None
                if home_name in BALLPARKS:
                    bp = BALLPARKS[home_name]
                    ballpark_name = bp["name"]
                    weather = get_weather(bp["lat"], bp["lon"])
                    weather_info = calc_weather_modifier(weather, bp["roof"])

                result = run_monte_carlo(teams, home_name, away_name, num_sims, home_sp, away_sp)

                game_odds = None
                if all_odds:
                    key = f"{away_name}@{home_name}"
                    game_odds = all_odds.get(key, None)

                if result:
                    print_game_card(away_name, home_name, result, weather_info, game, ballpark_name, game_odds)

                    if game_odds and game_odds.get("home_ml"):
                        home_market = moneyline_to_prob(game_odds["home_ml"])
                        away_market = moneyline_to_prob(game_odds["away_ml"])
                        home_edge = (result['home_pct'] - home_market) * 100
                        away_edge = (result['away_pct'] - away_market) * 100
                        if home_edge > 2:
                            edges.append((home_name, home_edge, "HOME", game_odds["home_ml"], result['home_sp_name']))
                        if away_edge > 2:
                            edges.append((away_name, away_edge, "AWAY", game_odds["away_ml"], result['away_sp_name']))
                else:
                    print(f"\n  ⚾ {game['away']} @ {game['home']} — ⚠️  Team not found")

            print(f"\n{'─' * 60}")
            print(f"✅ {len(games)} games | {num_sims} sims | Actual SPs + Weather + Park Factors + Odds")

            if edges:
                edges.sort(key=lambda x: x[1], reverse=True)
                print(f"\n{'=' * 60}")
                print(f"🔥 BEST EDGES — Value Bets")
                print(f"{'=' * 60}\n")
                for team, edge, side, ml, sp in edges:
                    stars = "🔥🔥🔥" if edge > 10 else "🔥🔥" if edge > 5 else "🔥"
                    print(f"  {stars} {team:<22} Edge: +{edge:.1f}%  ML: {ml:+d}  SP: {sp}")
                print(f"\n  ⚠️  Edges >5% = strong value | >10% = verify starter is correct")
            elif all_odds:
                print(f"\n  No significant edges found (all within 2%)")

        elif choice == "3":
            team_list = sorted(teams.keys())
            print("\nTeams:")
            for i, name in enumerate(team_list, 1):
                print(f"  {i:2}. {name}")
            try:
                away_pick = int(input("\nAway team number: "))
                home_pick = int(input("Home team number: "))
                num_sims = int(input("Simulations (default 10000): ").strip() or "10000")
            except ValueError:
                print("Invalid input.")
                continue
            away_name = team_list[away_pick - 1]
            home_name = team_list[home_pick - 1]
            weather_info = None
            ballpark_name = None
            if home_name in BALLPARKS:
                bp = BALLPARKS[home_name]
                ballpark_name = bp["name"]
                weather = get_weather(bp["lat"], bp["lon"])
                weather_info = calc_weather_modifier(weather, bp["roof"])
            print(f"\n⏳ Simulating {away_name} @ {home_name} x{num_sims}...")
            result = run_monte_carlo(teams, home_name, away_name, num_sims)
            if result:
                print_game_card(away_name, home_name, result, weather_info, None, ballpark_name, None)


if __name__ == "__main__":
    main()