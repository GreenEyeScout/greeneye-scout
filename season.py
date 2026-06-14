from auto_rosters import build_auto_rosters
from inning import simulate_inning
from pitcher import Pitcher
import random


DIVISIONS = {
    "AL East": ["New York Yankees", "Boston Red Sox", "Toronto Blue Jays", "Baltimore Orioles", "Tampa Bay Rays"],
    "AL Central": ["Cleveland Guardians", "Chicago White Sox", "Minnesota Twins", "Detroit Tigers", "Kansas City Royals"],
    "AL West": ["Houston Astros", "Texas Rangers", "Seattle Mariners", "Los Angeles Angels", "Oakland Athletics"],
    "NL East": ["Atlanta Braves", "New York Mets", "Philadelphia Phillies", "Miami Marlins", "Washington Nationals"],
    "NL Central": ["Chicago Cubs", "Milwaukee Brewers", "St. Louis Cardinals", "Cincinnati Reds", "Pittsburgh Pirates"],
    "NL West": ["Los Angeles Dodgers", "San Diego Padres", "San Francisco Giants", "Arizona Diamondbacks", "Colorado Rockies"],
}


def simulate_game_quiet(home_batters, home_pitcher, home_bullpen, away_batters, away_pitcher, away_bullpen):
    home_score = 0
    away_score = 0
    away_lineup_idx = 0
    home_lineup_idx = 0

    current_home_pitcher = home_pitcher
    current_away_pitcher = away_pitcher
    home_pitcher_changed = False
    away_pitcher_changed = False

    inning = 1

    while True:
        if inning >= 7 and not home_pitcher_changed and home_bullpen:
            current_home_pitcher = home_bullpen[0]
            home_pitcher_changed = True

        if inning >= 7 and not away_pitcher_changed and away_bullpen:
            current_away_pitcher = away_bullpen[0]
            away_pitcher_changed = True

        away_runs, away_lineup_idx, _ = simulate_inning(away_batters, current_home_pitcher, away_lineup_idx, None, home_team=False, quiet=True)
        away_score += away_runs

        home_runs, home_lineup_idx, _ = simulate_inning(home_batters, current_away_pitcher, home_lineup_idx, None, home_team=True, quiet=True)
        home_score += home_runs

        if inning >= 9 and home_score != away_score:
            break

        inning += 1

        if inning > 18:
            break

    return home_score, away_score


def generate_schedule(team_names):
    schedule = []

    # Find each team's division
    team_div = {}
    for div, div_teams in DIVISIONS.items():
        for t in div_teams:
            if t in team_names:
                team_div[t] = div

    # Division games: 19 per opponent (76 total)
    # Non-division games: ~86 total spread across 25 opponents (~3-4 each)
    for team in team_names:
        for opponent in team_names:
            if team >= opponent:
                continue

            same_div = team_div.get(team) == team_div.get(opponent)

            if same_div:
                games = 19
            else:
                games = 4

            for g in range(games):
                if g % 2 == 0:
                    schedule.append((team, opponent))
                else:
                    schedule.append((opponent, team))

    random.shuffle(schedule)
    return schedule


def simulate_season(teams):
    team_names = sorted(teams.keys())

    print("\n" + "=" * 50)
    print("🏆 FULL SEASON SIMULATOR — 2026 MLB SEASON 🏆")
    print("=" * 50)

    # Generate schedule
    schedule = generate_schedule(team_names)

    print(f"\n📅 {len(schedule)} games scheduled")
    print("⏳ Simulating season...\n")

    # Track records
    records = {}
    for name in team_names:
        records[name] = {"W": 0, "L": 0, "RS": 0, "RA": 0}

    # Simulate all games
    total = len(schedule)
    for i, (away_name, home_name) in enumerate(schedule):
        away_data = teams[away_name]
        home_data = teams[home_name]

        home_score, away_score = simulate_game_quiet(
            home_data["batters"], home_data["starter"], home_data["bullpen"],
            away_data["batters"], away_data["starter"], away_data["bullpen"]
        )

        # Record results
        records[home_name]["RS"] += home_score
        records[home_name]["RA"] += away_score
        records[away_name]["RS"] += away_score
        records[away_name]["RA"] += home_score

        if home_score > away_score:
            records[home_name]["W"] += 1
            records[away_name]["L"] += 1
        elif away_score > home_score:
            records[away_name]["W"] += 1
            records[home_name]["L"] += 1
        else:
            records[home_name]["W"] += 1
            records[away_name]["L"] += 1

        # Progress update every 200 games
        if (i + 1) % 200 == 0:
            print(f"  ⚾ {i + 1}/{total} games complete...")

    print(f"  ⚾ {total}/{total} games complete!")

    # Display standings by division
    print("\n" + "=" * 60)
    print("📊 FINAL 2026 MLB STANDINGS")
    print("=" * 60)

    for div_name, div_teams in DIVISIONS.items():
        print(f"\n🏟️  {div_name}")
        print(f"  {'TEAM':<26} {'W':>4} {'L':>4} {'PCT':>6} {'RS':>5} {'RA':>5} {'DIFF':>5}")
        print(f"  {'─' * 55}")

        div_records = []
        for team in div_teams:
            if team in records:
                r = records[team]
                total_games = r["W"] + r["L"]
                pct = r["W"] / total_games if total_games > 0 else 0
                diff = r["RS"] - r["RA"]
                div_records.append((team, r["W"], r["L"], pct, r["RS"], r["RA"], diff))

        div_records.sort(key=lambda x: x[3], reverse=True)

        for team, w, l, pct, rs, ra, diff in div_records:
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            print(f"  {team:<26} {w:4d} {l:4d} {pct:6.3f} {rs:5d} {ra:5d} {diff_str:>5}")

    # Overall league standings
    print("\n" + "=" * 60)
    print("🏆 TOP 10 TEAMS IN BASEBALL")
    print("=" * 60)
    print(f"  {'TEAM':<26} {'W':>4} {'L':>4} {'PCT':>6}")
    print(f"  {'─' * 42}")

    all_records = []
    for team, r in records.items():
        total_games = r["W"] + r["L"]
        pct = r["W"] / total_games if total_games > 0 else 0
        all_records.append((team, r["W"], r["L"], pct))

    all_records.sort(key=lambda x: x[3], reverse=True)

    for i, (team, w, l, pct) in enumerate(all_records[:10], 1):
        print(f"  {i:2d}. {team:<24} {w:4d} {l:4d} {pct:6.3f}")

    # Worst teams
    print(f"\n💀 BOTTOM 5 TEAMS")
    print(f"  {'─' * 42}")
    for i, (team, w, l, pct) in enumerate(all_records[-5:], 26):
        print(f"  {i:2d}. {team:<24} {w:4d} {l:4d} {pct:6.3f}")


# LOAD EVERYTHING
print("📊 Loading rosters...")
teams = build_auto_rosters()

# Check we have all 30 teams
missing = []
for div, div_teams in DIVISIONS.items():
    for t in div_teams:
        if t not in teams:
            missing.append(t)

if missing:
    print(f"⚠️  Missing teams: {missing}")
    print("Season will run with available teams only.")

# RUN THE SEASON
simulate_season(teams)