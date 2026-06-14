from pybaseball import batting_stats_bref, pitching_stats_bref
from player import Player
from pitcher import Pitcher
import unicodedata
import re
import statsapi


def fix_name(name):
    if '\\x' not in name:
        return name
    parts = re.split(r'(\\x[0-9a-fA-F]{2})', name)
    result_bytes = b''
    for part in parts:
        if re.match(r'^\\x[0-9a-fA-F]{2}$', part):
            result_bytes += bytes([int(part[2:], 16)])
        else:
            result_bytes += part.encode('utf-8')
    try:
        return result_bytes.decode('utf-8')
    except:
        return name


def normalize_for_match(name):
    try:
        name = name.encode('latin-1').decode('utf-8')
    except:
        pass
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_name = nfkd.encode('ascii', 'ignore').decode('ascii')
    return ascii_name.lower().strip().replace(".", "").replace("'", "").replace("-", "")


TEAM_MAP = {
    "Arizona": "Arizona Diamondbacks",
    "Athletics": "Oakland Athletics",
    "Atlanta": "Atlanta Braves",
    "Baltimore": "Baltimore Orioles",
    "Boston": "Boston Red Sox",
    "Cincinnati": "Cincinnati Reds",
    "Cleveland": "Cleveland Guardians",
    "Colorado": "Colorado Rockies",
    "Detroit": "Detroit Tigers",
    "Houston": "Houston Astros",
    "Kansas City": "Kansas City Royals",
    "Miami": "Miami Marlins",
    "Milwaukee": "Milwaukee Brewers",
    "Minnesota": "Minnesota Twins",
    "Philadelphia": "Philadelphia Phillies",
    "Pittsburgh": "Pittsburgh Pirates",
    "San Diego": "San Diego Padres",
    "San Francisco": "San Francisco Giants",
    "Seattle": "Seattle Mariners",
    "St. Louis": "St. Louis Cardinals",
    "Tampa Bay": "Tampa Bay Rays",
    "Texas": "Texas Rangers",
    "Toronto": "Toronto Blue Jays",
    "Washington": "Washington Nationals",
}

AMBIGUOUS_TEAM_IDS = {
    "New York": {
        "team_a": "New York Yankees", "team_a_id": 147,
        "team_b": "New York Mets", "team_b_id": 121,
    },
    "Chicago": {
        "team_a": "Chicago White Sox", "team_a_id": 145,
        "team_b": "Chicago Cubs", "team_b_id": 112,
    },
    "Los Angeles": {
        "team_a": "Los Angeles Angels", "team_a_id": 108,
        "team_b": "Los Angeles Dodgers", "team_b_id": 119,
    },
}

ALL_TEAM_IDS = {
    "Arizona Diamondbacks": 109, "Atlanta Braves": 144, "Baltimore Orioles": 110,
    "Boston Red Sox": 111, "Chicago Cubs": 112, "Chicago White Sox": 145,
    "Cincinnati Reds": 113, "Cleveland Guardians": 114, "Colorado Rockies": 115,
    "Detroit Tigers": 116, "Houston Astros": 117, "Kansas City Royals": 118,
    "Los Angeles Angels": 108, "Los Angeles Dodgers": 119, "Miami Marlins": 146,
    "Milwaukee Brewers": 158, "Minnesota Twins": 142, "New York Mets": 121,
    "New York Yankees": 147, "Oakland Athletics": 133, "Philadelphia Phillies": 143,
    "Pittsburgh Pirates": 134, "San Diego Padres": 135, "San Francisco Giants": 137,
    "Seattle Mariners": 136, "St. Louis Cardinals": 138, "Tampa Bay Rays": 139,
    "Texas Rangers": 140, "Toronto Blue Jays": 141, "Washington Nationals": 120,
}

LIVE_ROSTERS = {}
ALL_PITCHERS = {}
HANDEDNESS_DATA = {}
ACTIVE_ROSTERS = {}


def parse_roster_names(roster_text):
    names = []
    for line in roster_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('---'):
            continue
        parts = line.split()
        if len(parts) >= 3:
            name = ' '.join(parts[2:])
            names.append(normalize_for_match(name))
    return names


def pull_live_rosters():
    print("📋 Pulling live rosters from MLB...")
    live_rosters = {}
    for city, info in AMBIGUOUS_TEAM_IDS.items():
        for team_key in ["team_a", "team_b"]:
            team_name = info[team_key]
            team_id = info[f"{team_key}_id"]
            try:
                roster_text = statsapi.roster(team_id)
                names = parse_roster_names(roster_text)
                live_rosters[team_name] = names
                print(f"  ✅ {team_name}: {len(names)} players")
            except:
                live_rosters[team_name] = []
    return live_rosters


def pull_all_active_rosters():
    print("🏥 Loading active rosters for injury detection...")
    active = {}
    for team_name, team_id in ALL_TEAM_IDS.items():
        try:
            roster_text = statsapi.roster(team_id)
            names = parse_roster_names(roster_text)
            active[team_name] = names
        except:
            active[team_name] = []
    total = sum(len(v) for v in active.values())
    print(f"  ✅ {total} active players across {len(active)} teams")
    return active


def pull_handedness():
    print("🔄 Loading player handedness data from MLB...")
    handedness = {}
    try:
        data = statsapi.get('sports_players', {'sportId': 1, 'season': 2026})
        for player in data.get('people', []):
            name = player.get('fullName', '')
            bat_side = player.get('batSide', {}).get('code', 'R')
            pitch_hand = player.get('pitchHand', {}).get('code', 'R')
            norm = normalize_for_match(name)
            handedness[norm] = {"bats": bat_side, "throws": pitch_hand}
        print(f"  ✅ Handedness loaded for {len(handedness)} players!")
    except Exception as e:
        print(f"  ⚠️  Could not load handedness: {e}")
    return handedness


def get_handedness(name, default_bats="R", default_throws="R"):
    norm = normalize_for_match(name)
    if norm in HANDEDNESS_DATA:
        return HANDEDNESS_DATA[norm]["bats"], HANDEDNESS_DATA[norm]["throws"]
    return default_bats, default_throws


def is_player_active(player_name, team_name):
    if team_name not in ACTIVE_ROSTERS or not ACTIVE_ROSTERS[team_name]:
        return True
    norm = normalize_for_match(player_name)
    for active_name in ACTIVE_ROSTERS[team_name]:
        if norm in active_name or active_name in norm:
            return True
    return False


def get_team_name(tm_value, player_name=""):
    if ',' in str(tm_value):
        tm_value = tm_value.split(',')[-1].strip()
    if tm_value in TEAM_MAP:
        return TEAM_MAP[tm_value]
    if tm_value in AMBIGUOUS_TEAM_IDS:
        info = AMBIGUOUS_TEAM_IDS[tm_value]
        name_norm = normalize_for_match(fix_name(player_name))
        for team_key in ["team_a", "team_b"]:
            team_name = info[team_key]
            if team_name in LIVE_ROSTERS:
                for roster_name in LIVE_ROSTERS[team_name]:
                    if name_norm in roster_name or roster_name in name_norm:
                        return team_name
        return info["team_b"]
    return None


def build_auto_rosters(year=2026):
    global ALL_PITCHERS, LIVE_ROSTERS, HANDEDNESS_DATA, ACTIVE_ROSTERS

    LIVE_ROSTERS = pull_live_rosters()
    ACTIVE_ROSTERS = pull_all_active_rosters()
    HANDEDNESS_DATA = pull_handedness()

    print(f"📊 Auto-building rosters from {year} data...")

    bat_data = batting_stats_bref(year)
    bat_data = bat_data[bat_data['PA'] >= 40]

    pitch_data = pitching_stats_bref(year)
    pitch_data = pitch_data[pitch_data['IP'] >= 10]

    teams = {}
    injured_players = []

    for _, row in bat_data.iterrows():
        name = fix_name(row['Name'])
        team_name = get_team_name(row['Tm'], name)
        if not team_name:
            continue
        if team_name not in teams:
            teams[team_name] = {"batters": [], "starter": None, "bullpen": []}

        batting_avg = row['BA'] if row['BA'] > 0 else 0.200
        home_run_rate = row['HR'] / row['PA'] if row['PA'] > 0 else 0.02
        strikeout_rate = row['SO'] / row['PA'] if row['PA'] > 0 else 0.20

        bats, _ = get_handedness(name)
        player = Player(name, batting_avg, home_run_rate, strikeout_rate, bats)
        teams[team_name]["batters"].append((row['PA'], player))

    # Sort by PA and take top players, filtering out injured
    for team_name in teams:
        teams[team_name]["batters"].sort(key=lambda x: x[0], reverse=True)
        active_batters = []
        for pa, player in teams[team_name]["batters"]:
            if is_player_active(player.name, team_name):
                active_batters.append(player)
            else:
                injured_players.append((player.name, team_name))
            if len(active_batters) >= 9:
                break
        teams[team_name]["batters"] = active_batters

    team_pitchers = {}

    for _, row in pitch_data.iterrows():
        name = fix_name(row['Name'])
        team_name = get_team_name(row['Tm'], name)

        era = row['ERA'] if row['ERA'] > 0 else 4.50
        strikeout_rate = row['SO'] / row['IP'] if row['IP'] > 0 else 0.20
        walk_rate = row['BB'] / row['IP'] if row['IP'] > 0 else 0.08

        _, throws = get_handedness(name, default_throws="R")
        pitcher_obj = Pitcher(name, era, strikeout_rate, walk_rate, throws)

        ALL_PITCHERS[name] = pitcher_obj
        ALL_PITCHERS[normalize_for_match(name)] = pitcher_obj

        if not team_name:
            continue
        if team_name not in team_pitchers:
            team_pitchers[team_name] = []
        team_pitchers[team_name].append((row['IP'], pitcher_obj))

    for team_name in team_pitchers:
        team_pitchers[team_name].sort(key=lambda x: x[0], reverse=True)
        pitchers_list = [p for _, p in team_pitchers[team_name]]
        if team_name not in teams:
            teams[team_name] = {"batters": [], "starter": None, "bullpen": []}
        if len(pitchers_list) >= 1:
            teams[team_name]["starter"] = pitchers_list[0]
        if len(pitchers_list) >= 2:
            teams[team_name]["bullpen"] = pitchers_list[1:4]

    default_pitcher = Pitcher("Generic Pitcher", 4.50, 0.20, 0.08, "R")
    for team_name in teams:
        if not teams[team_name]["starter"]:
            teams[team_name]["starter"] = default_pitcher
        if not teams[team_name]["bullpen"]:
            teams[team_name]["bullpen"] = [default_pitcher]
        teams[team_name]["pitcher"] = teams[team_name]["starter"]

    print(f"✅ {len(teams)} teams built automatically!")
    print(f"✅ {len(ALL_PITCHERS)//2} pitchers indexed!")

    if injured_players:
        print(f"\n🏥 INJURED / IL PLAYERS DETECTED ({len(injured_players)}):")
        for name, team in injured_players[:20]:
            print(f"  🚑 {name} ({team}) — NOT on active roster")
        if len(injured_players) > 20:
            print(f"  ... and {len(injured_players) - 20} more")

    return teams


def find_pitcher(name):
    if name in ALL_PITCHERS:
        return ALL_PITCHERS[name]
    normalized = normalize_for_match(name)
    if normalized in ALL_PITCHERS:
        return ALL_PITCHERS[normalized]
    for key, pitcher in ALL_PITCHERS.items():
        if isinstance(key, str) and len(name.split()) > 0:
            if name.split()[-1].lower() in key.lower():
                if name.split()[0][0].lower() in key.lower():
                    return pitcher
    return None