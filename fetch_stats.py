from pybaseball import batting_stats_bref, pitching_stats_bref
from player import Player
from pitcher import Pitcher
import unicodedata
import re


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


def normalize(name):
    name = fix_name(name)
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_name = nfkd.encode('ascii', 'ignore').decode('ascii')
    return ascii_name.lower().strip().replace(".", "").replace("'", "").replace("-", "")


def find_in_dict(name, d):
    if name in d:
        return d[name]
    target = normalize(name)
    for key, val in d.items():
        if normalize(key) == target:
            return val
    return None


def get_real_players(year=2026, min_pa=40):
    print(f"📊 Loading real {year} batting stats...")
    data = batting_stats_bref(year)
    data = data[data['PA'] >= min_pa]

    players = {}
    for _, row in data.iterrows():
        name = fix_name(row['Name'])
        batting_avg = row['BA'] if row['BA'] > 0 else 0.200
        home_run_rate = row['HR'] / row['PA'] if row['PA'] > 0 else 0.02
        strikeout_rate = row['SO'] / row['PA'] if row['PA'] > 0 else 0.20
        players[name] = Player(name, batting_avg, home_run_rate, strikeout_rate)

    print(f"✅ {len(players)} batters loaded!")
    return players


def get_real_pitchers(year=2026, min_ip=20):
    print(f"📊 Loading real {year} pitching stats...")
    data = pitching_stats_bref(year)
    data = data[data['IP'] >= min_ip]

    pitchers = {}
    for _, row in data.iterrows():
        name = fix_name(row['Name'])
        era = row['ERA'] if row['ERA'] > 0 else 4.50
        strikeout_rate = row['SO'] / row['IP'] if row['IP'] > 0 else 0.20
        walk_rate = row['BB'] / row['IP'] if row['IP'] > 0 else 0.08
        pitchers[name] = Pitcher(name, era, strikeout_rate, walk_rate)

    print(f"✅ {len(pitchers)} pitchers loaded!")
    return pitchers