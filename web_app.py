import streamlit as st
from auto_rosters import build_auto_rosters, find_pitcher
from inning import simulate_inning
from pitcher import Pitcher
import random
import requests
import statsapi
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="GreenEye Scout", page_icon="🟢", layout="wide")

st.markdown("""
<style>
    .game-card { background: linear-gradient(135deg, #1a1f2e 0%, #0e1117 100%); border: 1px solid #2ecc71; border-radius: 12px; padding: 20px; margin: 10px 0; }
    .team-header { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
    .team-logo { width: 40px; height: 40px; }
    .best-bet { background: linear-gradient(135deg, #1a3a1a 0%, #0e1117 100%); border: 2px solid #2ecc71; border-radius: 12px; padding: 20px; margin: 10px 0; }
    .score-live { background: #1a1f2e; border: 1px solid #333; border-radius: 8px; padding: 12px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

LOGO_MAP = {"Arizona Diamondbacks": "ari", "Atlanta Braves": "atl", "Baltimore Orioles": "bal", "Boston Red Sox": "bos", "Chicago Cubs": "chc", "Chicago White Sox": "chw", "Cincinnati Reds": "cin", "Cleveland Guardians": "cle", "Colorado Rockies": "col", "Detroit Tigers": "det", "Houston Astros": "hou", "Kansas City Royals": "kc", "Los Angeles Angels": "laa", "Los Angeles Dodgers": "lad", "Miami Marlins": "mia", "Milwaukee Brewers": "mil", "Minnesota Twins": "min", "New York Mets": "nym", "New York Yankees": "nyy", "Oakland Athletics": "oak", "Philadelphia Phillies": "phi", "Pittsburgh Pirates": "pit", "San Diego Padres": "sd", "San Francisco Giants": "sf", "Seattle Mariners": "sea", "St. Louis Cardinals": "stl", "Tampa Bay Rays": "tb", "Texas Rangers": "tex", "Toronto Blue Jays": "tor", "Washington Nationals": "wsh"}
PARK_FACTORS = {"Arizona Diamondbacks": 1.04, "Atlanta Braves": 1.01, "Baltimore Orioles": 1.03, "Boston Red Sox": 1.08, "Chicago Cubs": 1.05, "Chicago White Sox": 1.02, "Cincinnati Reds": 1.06, "Cleveland Guardians": 0.98, "Colorado Rockies": 1.30, "Detroit Tigers": 0.96, "Houston Astros": 1.03, "Kansas City Royals": 1.00, "Los Angeles Angels": 0.97, "Los Angeles Dodgers": 0.97, "Miami Marlins": 0.90, "Milwaukee Brewers": 1.02, "Minnesota Twins": 1.00, "New York Mets": 0.94, "New York Yankees": 1.07, "Oakland Athletics": 1.00, "Philadelphia Phillies": 1.05, "Pittsburgh Pirates": 0.93, "San Diego Padres": 0.92, "San Francisco Giants": 0.93, "Seattle Mariners": 0.93, "St. Louis Cardinals": 0.97, "Tampa Bay Rays": 0.95, "Texas Rangers": 0.99, "Toronto Blue Jays": 1.01, "Washington Nationals": 1.00}
BALLPARK_NAMES = {"Arizona Diamondbacks": "Chase Field", "Atlanta Braves": "Truist Park", "Baltimore Orioles": "Camden Yards", "Boston Red Sox": "Fenway Park", "Chicago Cubs": "Wrigley Field", "Chicago White Sox": "Guaranteed Rate Field", "Cincinnati Reds": "Great American Ball Park", "Cleveland Guardians": "Progressive Field", "Colorado Rockies": "Coors Field", "Detroit Tigers": "Comerica Park", "Houston Astros": "Minute Maid Park", "Kansas City Royals": "Kauffman Stadium", "Los Angeles Angels": "Angel Stadium", "Los Angeles Dodgers": "Dodger Stadium", "Miami Marlins": "loanDepot Park", "Milwaukee Brewers": "American Family Field", "Minnesota Twins": "Target Field", "New York Mets": "Citi Field", "New York Yankees": "Yankee Stadium", "Oakland Athletics": "Sutter Health Park", "Philadelphia Phillies": "Citizens Bank Park", "Pittsburgh Pirates": "PNC Park", "San Diego Padres": "Petco Park", "San Francisco Giants": "Oracle Park", "Seattle Mariners": "T-Mobile Park", "St. Louis Cardinals": "Busch Stadium", "Tampa Bay Rays": "Tropicana Field", "Texas Rangers": "Globe Life Field", "Toronto Blue Jays": "Rogers Centre", "Washington Nationals": "Nationals Park"}
TEAM_NAME_MAP = {"Arizona Diamondbacks": "Arizona Diamondbacks", "Atlanta Braves": "Atlanta Braves", "Baltimore Orioles": "Baltimore Orioles", "Boston Red Sox": "Boston Red Sox", "Chicago Cubs": "Chicago Cubs", "Chicago White Sox": "Chicago White Sox", "Cincinnati Reds": "Cincinnati Reds", "Cleveland Guardians": "Cleveland Guardians", "Colorado Rockies": "Colorado Rockies", "Detroit Tigers": "Detroit Tigers", "Houston Astros": "Houston Astros", "Kansas City Royals": "Kansas City Royals", "Los Angeles Angels": "Los Angeles Angels", "Los Angeles Dodgers": "Los Angeles Dodgers", "Miami Marlins": "Miami Marlins", "Milwaukee Brewers": "Milwaukee Brewers", "Minnesota Twins": "Minnesota Twins", "New York Mets": "New York Mets", "New York Yankees": "New York Yankees", "Oakland Athletics": "Oakland Athletics", "Philadelphia Phillies": "Philadelphia Phillies", "Pittsburgh Pirates": "Pittsburgh Pirates", "San Diego Padres": "San Diego Padres", "San Francisco Giants": "San Francisco Giants", "Seattle Mariners": "Seattle Mariners", "St. Louis Cardinals": "St. Louis Cardinals", "Tampa Bay Rays": "Tampa Bay Rays", "Texas Rangers": "Texas Rangers", "Toronto Blue Jays": "Toronto Blue Jays", "Washington Nationals": "Washington Nationals", "Athletics": "Oakland Athletics"}

def get_logo_url(team):
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{LOGO_MAP.get(team, 'mlb')}.png"

@st.cache_data(ttl=600)
def get_headshot_cached(name):
    try:
        results = statsapi.lookup_player(name)
        if results: return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_180,q_auto:best/v1/people/{results[0]['id']}/headshot/silo/current"
    except: pass
    return None

def sim_game_for_props(hd, ad, hp, ap, pf):
    hs, as_ = 0, 0
    ai, hi = 0, 0
    h_stats_all, a_stats_all = {}, {}
    sp_home_k, sp_away_k = 0, 0
    sp_home_runs, sp_away_runs = 0, 0
    for inn in range(1, 10):
        a_inn = {}
        if inn <= 6:
            ar, ai, a_inn = simulate_inning(ad["batters"], hp, ai, a_inn, False, True, pf)
            sp_home_k += sum(s["SO"] for s in a_inn.values())
            sp_home_runs += ar
        else:
            cur = hd["bullpen"][0] if hd["bullpen"] else hp
            ar, ai, a_inn = simulate_inning(ad["batters"], cur, ai, a_inn, False, True, pf)
        as_ += ar
        for k, v in a_inn.items():
            if k not in a_stats_all: a_stats_all[k] = {"HR": 0, "H": 0, "SO": 0}
            for s in ["HR", "H", "SO"]: a_stats_all[k][s] += v[s]
        if inn >= 9 and hs > as_: break
        h_inn = {}
        if inn <= 6:
            hr, hi, h_inn = simulate_inning(hd["batters"], ap, hi, h_inn, True, True, pf)
            sp_away_k += sum(s["SO"] for s in h_inn.values())
            sp_away_runs += hr
        else:
            cur = ad["bullpen"][0] if ad["bullpen"] else ap
            hr, hi, h_inn = simulate_inning(hd["batters"], cur, hi, h_inn, True, True, pf)
        hs += hr
        for k, v in h_inn.items():
            if k not in h_stats_all: h_stats_all[k] = {"HR": 0, "H": 0, "SO": 0}
            for s in ["HR", "H", "SO"]: h_stats_all[k][s] += v[s]
        if inn >= 9 and hs != as_: break
    return hs, as_, h_stats_all, a_stats_all, sp_home_k, sp_away_k, sp_home_runs, sp_away_runs

def run_full_sim(teams, home, away, n, home_sp=None, away_sp=None):
    hd, ad = teams[home], teams[away]
    hp = home_sp or hd["starter"]
    ap = away_sp or ad["starter"]
    pf = PARK_FACTORS.get(home, 1.0)
    hw, aw, thr, tar = 0, 0, 0, 0
    trl, margins = [], []
    hrl, arl = 0, 0
    player_hrs, player_hits = {}, {}
    home_sp_ks, away_sp_ks = [], []
    home_sp_runs, away_sp_runs = [], []
    home_sp_wins, away_sp_wins = 0, 0

    for _ in range(n):
        hs, as_, h_stats, a_stats, hk, ak, hr_allowed, ar_allowed = sim_game_for_props(hd, ad, hp, ap, pf)
        trl.append(hs + as_)
        margins.append(hs - as_)
        thr += hs; tar += as_
        home_sp_ks.append(hk); away_sp_ks.append(ak)
        home_sp_runs.append(hr_allowed); away_sp_runs.append(ar_allowed)
        if hs > as_:
            hw += 1; home_sp_wins += 1
            if hs - as_ >= 2: hrl += 1
        else:
            aw += 1; away_sp_wins += 1
            if as_ - hs >= 2: arl += 1
        for pname, ps in {**h_stats, **a_stats}.items():
            if pname not in player_hrs: player_hrs[pname] = 0
            if pname not in player_hits: player_hits[pname] = 0
            if ps["HR"] > 0: player_hrs[pname] += 1
            if ps["H"] >= 2: player_hits[pname] += 1

    ou = {line: sum(1 for t in trl if t > line) / n for line in [5.5, 6.5, 7.5, 8.5, 9.5, 10.5]}
    props = {pn: {"hr_pct": player_hrs[pn]/n, "multi_hit_pct": player_hits.get(pn, 0)/n} for pn in player_hrs}

    return {
        "home_pct": hw/n, "away_pct": aw/n, "avg_home": thr/n, "avg_away": tar/n,
        "avg_total": sum(trl)/n, "ou": ou, "home_rl": hrl/n, "away_rl": arl/n,
        "home_sp": hp.name, "away_sp": ap.name, "pf": pf,
        "home_throws": hp.throws, "away_throws": ap.throws,
        "total_runs_list": trl, "margins": margins, "props": props,
        "pitcher_props": {
            hp.name: {"team": home, "era": hp.era, "throws": hp.throws, "opp": away,
                "avg_k": sum(home_sp_ks)/n, "k5": sum(1 for k in home_sp_ks if k>=5)/n,
                "k6": sum(1 for k in home_sp_ks if k>=6)/n, "k7": sum(1 for k in home_sp_ks if k>=7)/n,
                "avg_runs": sum(home_sp_runs)/n, "qs": sum(1 for r in home_sp_runs if r<=3)/n,
                "under3": sum(1 for r in home_sp_runs if r<=2)/n, "win_pct": home_sp_wins/n},
            ap.name: {"team": away, "era": ap.era, "throws": ap.throws, "opp": home,
                "avg_k": sum(away_sp_ks)/n, "k5": sum(1 for k in away_sp_ks if k>=5)/n,
                "k6": sum(1 for k in away_sp_ks if k>=6)/n, "k7": sum(1 for k in away_sp_ks if k>=7)/n,
                "avg_runs": sum(away_sp_runs)/n, "qs": sum(1 for r in away_sp_runs if r<=3)/n,
                "under3": sum(1 for r in away_sp_runs if r<=2)/n, "win_pct": away_sp_wins/n},
        },
    }

def prob_to_ml(prob):
    if prob <= 0 or prob >= 1: return "+100"
    if prob >= 0.5: return f"{-round((prob / (1 - prob)) * 100)}"
    return f"+{round(((1 - prob) / prob) * 100)}"

def ml_to_prob(ml):
    if ml < 0: return abs(ml) / (abs(ml) + 100)
    return 100 / (ml + 100)

@st.cache_data(ttl=3600, show_spinner="🟢 Loading 2026 MLB data...")
def load_teams(): return build_auto_rosters()

@st.cache_data(ttl=120)
def get_schedule(date):
    sched = statsapi.schedule(date=date)
    return [{"away": g["away_name"], "home": g["home_name"],
        "away_pitcher": g.get("away_probable_pitcher", "TBD"), "home_pitcher": g.get("home_probable_pitcher", "TBD"),
        "away_score": g.get("away_score", 0) or 0, "home_score": g.get("home_score", 0) or 0,
        "status": g.get("status", ""), "inning": g.get("current_inning", ""), "inning_state": g.get("inning_state", "")} for g in sched]

if "bankroll" not in st.session_state: st.session_state.bankroll = 1000.0
if "bet_history" not in st.session_state: st.session_state.bet_history = []
if "prediction_history" not in st.session_state: st.session_state.prediction_history = []

teams = load_teams()

st.markdown("<div style='text-align:center;padding:1.5rem 0 0.5rem'><h1 style='color:#2ecc71;margin-bottom:0;font-size:2.5rem'>🟢 GreenEye Scout</h1><p style='color:#aaa;font-size:1.1rem;margin-top:5px'>MLB Prediction Engine — Powered by Monte Carlo Simulation</p><p style='color:#666;font-size:0.8rem'>2026 Stats • Park Factors • L/R Splits • Injury Detection • Player Props</p></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab7, tab5, tab6 = st.tabs(["📅 Predictions", "📺 Live Scores", "🔥 Best Bets", "🎯 Hitter Props", "⚾ Pitcher Props", "🎰 Parlay", "💰 Bankroll"])

with tab1:
    col1, col2 = st.columns(2)
    with col1: date_option = st.radio("Date", ["Today", "Tomorrow"], horizontal=True)
    with col2: num_sims = st.select_slider("Simulations", options=[1000, 2500, 5000, 10000, 25000], value=10000)
    if st.button("🟢 Run GreenEye Scout", type="primary"):
        date = datetime.now().strftime('%m/%d/%Y') if date_option == "Today" else (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')
        games = get_schedule(date)
        if not games: st.error("No games found")
        else:
            progress = st.progress(0); all_results = []
            for i, game in enumerate(games):
                away, home = TEAM_NAME_MAP.get(game["away"], game["away"]), TEAM_NAME_MAP.get(game["home"], game["home"])
                if home not in teams or away not in teams: continue
                hsp = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
                asp = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None
                result = run_full_sim(teams, home, away, num_sims, hsp, asp)
                all_results.append((away, home, game, result))
                st.session_state.prediction_history.append({"date": date, "away": away, "home": home, "away_pct": result["away_pct"], "home_pct": result["home_pct"]})
                progress.progress((i + 1) / len(games))
            for away, home, game, result in all_results:
                bp = BALLPARK_NAMES.get(home, "")
                st.markdown(f"<div class='game-card'><div style='display:flex;justify-content:space-between;align-items:center'><div class='team-header'><img src='{get_logo_url(away)}' class='team-logo'><span style='font-size:1.2rem;font-weight:bold'>{away}</span></div><span style='color:#666;font-size:1.5rem'>@</span><div class='team-header'><span style='font-size:1.2rem;font-weight:bold'>{home}</span><img src='{get_logo_url(home)}' class='team-logo'></div></div><p style='color:#888;font-size:0.85rem;margin-top:8px'>📍 {bp} (PF: {result['pf']:.2f}) | SP: {result['away_sp']} ({result['away_throws']}) vs {result['home_sp']} ({result['home_throws']})</p></div>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(away, f"{result['away_pct']*100:.1f}%", f"ML: {prob_to_ml(result['away_pct'])}")
                c2.metric(home, f"{result['home_pct']*100:.1f}%", f"ML: {prob_to_ml(result['home_pct'])}")
                c3.metric("Predicted Score", f"{result['avg_away']:.1f} - {result['avg_home']:.1f}")
                c4.metric("Total Runs", f"{result['avg_total']:.1f}")
                with st.expander("📊 Charts & Details"):
                    ch1, ch2 = st.columns(2)
                    with ch1: st.markdown("**Total Runs**"); st.bar_chart(pd.DataFrame({"R": result["total_runs_list"]})["R"].value_counts().sort_index(), height=200)
                    with ch2: st.markdown("**Win Margin**"); st.bar_chart(pd.DataFrame({"M": result["margins"]})["M"].value_counts().sort_index(), height=200)
                    d1, d2, d3 = st.columns(3)
                    with d1: st.markdown("**Moneyline**"); st.write(f"{away}: {result['away_pct']*100:.1f}%"); st.write(f"{home}: {result['home_pct']*100:.1f}%")
                    with d2: st.markdown("**Run Line (-1.5)**"); st.write(f"{away}: {result['away_rl']*100:.1f}%"); st.write(f"{home}: {result['home_rl']*100:.1f}%")
                    with d3:
                        st.markdown("**Over/Under**")
                        for line in [6.5, 7.5, 8.5, 9.5]: st.write(f"O/U {line}: Over {result['ou'][line]*100:.1f}%")
                st.markdown("---")

with tab2:
    st.markdown("### 📺 Live Scoreboard")
    if st.button("🔄 Refresh Scores", key="refresh"): st.cache_data.clear()
    for game in get_schedule(datetime.now().strftime('%m/%d/%Y')):
        away, home = TEAM_NAME_MAP.get(game["away"], game["away"]), TEAM_NAME_MAP.get(game["home"], game["home"])
        status = game.get("status", "")
        sd = "🏁 Final" if "Final" in status else f"🔴 LIVE — {game.get('inning_state','')} {game.get('inning','')}" if "Progress" in status else "⏰ Scheduled"
        st.markdown(f"<div class='score-live'><div style='display:flex;justify-content:space-between;align-items:center'><div class='team-header'><img src='{get_logo_url(away)}' class='team-logo'><span style='font-size:1.1rem'>{away}</span><span style='font-size:1.5rem;font-weight:bold;margin-left:10px'>{game.get('away_score',0)}</span></div><span style='color:#888;font-size:0.9rem'>{sd}</span><div class='team-header'><span style='font-size:1.5rem;font-weight:bold;margin-right:10px'>{game.get('home_score',0)}</span><span style='font-size:1.1rem'>{home}</span><img src='{get_logo_url(home)}' class='team-logo'></div></div></div>", unsafe_allow_html=True)

with tab3:
    st.markdown("### 🔥 Best Bets")
    if st.session_state.prediction_history:
        edges = []
        for p in st.session_state.prediction_history[-30:]:
            if p['home_pct'] > 0.55: edges.append({"team": p['home'], "matchup": f"{p['away']} @ {p['home']}", "win_pct": p['home_pct']*100, "ml": prob_to_ml(p['home_pct'])})
            if p['away_pct'] > 0.55: edges.append({"team": p['away'], "matchup": f"{p['away']} @ {p['home']}", "win_pct": p['away_pct']*100, "ml": prob_to_ml(p['away_pct'])})
        edges.sort(key=lambda x: x['win_pct'], reverse=True)
        for e in edges[:8]:
            fire = "🔥🔥🔥" if e['win_pct'] > 65 else "🔥🔥" if e['win_pct'] > 58 else "🔥"
            st.markdown(f"<div class='best-bet'><div class='team-header'><img src='{get_logo_url(e['team'])}' class='team-logo'><span style='font-size:1.2rem;font-weight:bold'>{fire} {e['team']}</span><span style='color:#2ecc71;font-size:1.1rem;margin-left:auto'>{e['win_pct']:.1f}% ({e['ml']})</span></div><p style='color:#888;margin-top:5px'>{e['matchup']}</p></div>", unsafe_allow_html=True)
    else: st.info("Run predictions on Tab 1 first.")

with tab4:
    st.markdown("### 🎯 Hitter Props — Auto Edge Finder")
    col1, col2 = st.columns(2)
    with col1: hp_date = st.radio("Date", ["Today", "Tomorrow"], horizontal=True, key="hp_date")
    with col2: hp_sims = st.select_slider("Sims", options=[1000, 2500, 5000, 10000], value=5000, key="hp_sims")
    if st.button("🎯 Find Best Hitter Props", type="primary", key="auto_hp"):
        date = datetime.now().strftime('%m/%d/%Y') if hp_date == "Today" else (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')
        games = get_schedule(date)
        if not games: st.error("No games found")
        else:
            progress = st.progress(0); all_props = {}; all_matchups = {}
            for i, game in enumerate(games):
                away, home = TEAM_NAME_MAP.get(game["away"], game["away"]), TEAM_NAME_MAP.get(game["home"], game["home"])
                if home not in teams or away not in teams: continue
                hsp = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
                asp = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None
                result = run_full_sim(teams, home, away, hp_sims, hsp, asp)
                for pn, pd in result["props"].items(): all_props[pn] = pd; all_matchups[pn] = f"{away} @ {home}"
                progress.progress((i + 1) / len(games))
            st.markdown("---"); st.markdown("### 💥 Top Home Run Candidates")
            for rank, (name, props) in enumerate(sorted(all_props.items(), key=lambda x: x[1]['hr_pct'], reverse=True)[:15], 1):
                hr_pct = props['hr_pct'] * 100
                if hr_pct < 1: continue
                implied = f"+{round((1-props['hr_pct'])/props['hr_pct']*100)}" if 0 < props['hr_pct'] < 1 else "N/A"
                hs = get_headshot_cached(name); fire = "🔥🔥🔥" if hr_pct > 12 else "🔥🔥" if hr_pct > 8 else "🔥" if hr_pct > 5 else ""
                c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
                with c1: st.image(hs, width=55) if hs else st.write(f"#{rank}")
                with c2: st.markdown(f"**{name}** {fire}"); st.caption(all_matchups.get(name, ""))
                with c3: st.metric("HR %", f"{hr_pct:.1f}%")
                with c4: st.metric("Implied", implied)
            st.markdown("---"); st.markdown("### 🔥 Top Multi-Hit Candidates")
            for rank, (name, props) in enumerate(sorted(all_props.items(), key=lambda x: x[1]['multi_hit_pct'], reverse=True)[:15], 1):
                mh = props['multi_hit_pct'] * 100
                if mh < 5: continue
                implied = f"+{round((1-props['multi_hit_pct'])/props['multi_hit_pct']*100)}" if 0 < props['multi_hit_pct'] < 0.5 else f"-{round(props['multi_hit_pct']/(1-props['multi_hit_pct'])*100)}" if props['multi_hit_pct'] < 1 else "N/A"
                hs = get_headshot_cached(name); fire = "🔥🔥🔥" if mh > 35 else "🔥🔥" if mh > 25 else "🔥" if mh > 15 else ""
                c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
                with c1: st.image(hs, width=55) if hs else st.write(f"#{rank}")
                with c2: st.markdown(f"**{name}** {fire}"); st.caption(all_matchups.get(name, ""))
                with c3: st.metric("2+ Hits", f"{mh:.1f}%")
                with c4: st.metric("Implied", implied)

with tab7:
    st.markdown("### ⚾ Pitcher Props — K's & Performance")
    col1, col2 = st.columns(2)
    with col1: pk_date = st.radio("Date", ["Today", "Tomorrow"], horizontal=True, key="pk_date")
    with col2: pk_sims = st.select_slider("Sims", options=[1000, 2500, 5000, 10000], value=5000, key="pk_sims")
    if st.button("⚾ Find Best Pitcher Props", type="primary", key="auto_pk"):
        date = datetime.now().strftime('%m/%d/%Y') if pk_date == "Today" else (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')
        games = get_schedule(date)
        if not games: st.error("No games found")
        else:
            progress = st.progress(0); all_pitcher_props = []
            for i, game in enumerate(games):
                away, home = TEAM_NAME_MAP.get(game["away"], game["away"]), TEAM_NAME_MAP.get(game["home"], game["home"])
                if home not in teams or away not in teams: continue
                hsp = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
                asp = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None
                result = run_full_sim(teams, home, away, pk_sims, hsp, asp)
                for pname, pp in result["pitcher_props"].items():
                    pp["name"] = pname; pp["matchup"] = f"{away} @ {home}"
                    all_pitcher_props.append(pp)
                progress.progress((i + 1) / len(games))

            st.markdown("---"); st.markdown("### 🥴 Best Strikeout Props")
            st.markdown("*Through 6 innings pitched*")
            k_sorted = sorted(all_pitcher_props, key=lambda x: x['avg_k'], reverse=True)
            for rank, p in enumerate(k_sorted[:12], 1):
                hs = get_headshot_cached(p['name']); fire = "🔥🔥🔥" if p['avg_k'] > 6 else "🔥🔥" if p['avg_k'] > 5 else "🔥" if p['avg_k'] > 4 else ""
                c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1, 1])
                with c1: st.image(hs, width=55) if hs else st.write(f"#{rank}")
                with c2: st.markdown(f"**{p['name']}** ({p['throws']}) {fire}"); st.caption(f"{p['matchup']} | ERA: {p['era']:.2f} | Avg K: {p['avg_k']:.1f}")
                with c3: st.metric("5+ K", f"{p['k5']*100:.0f}%")
                with c4: st.metric("6+ K", f"{p['k6']*100:.0f}%")
                with c5: st.metric("7+ K", f"{p['k7']*100:.0f}%")

            st.markdown("---"); st.markdown("### 🛡️ Best Quality Start Props")
            qs_sorted = sorted(all_pitcher_props, key=lambda x: x['qs'], reverse=True)
            for rank, p in enumerate(qs_sorted[:12], 1):
                hs = get_headshot_cached(p['name']); fire = "🔥🔥🔥" if p['qs'] > 0.75 else "🔥🔥" if p['qs'] > 0.6 else "🔥" if p['qs'] > 0.5 else ""
                c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1, 1])
                with c1: st.image(hs, width=55) if hs else st.write(f"#{rank}")
                with c2: st.markdown(f"**{p['name']}** ({p['throws']}) {fire}"); st.caption(f"vs {p['opp']} | ERA: {p['era']:.2f} | Avg Runs: {p['avg_runs']:.1f}")
                with c3: st.metric("QS %", f"{p['qs']*100:.0f}%")
                with c4: st.metric("U3 Runs", f"{p['under3']*100:.0f}%")
                with c5: st.metric("Win %", f"{p['win_pct']*100:.0f}%")

            st.markdown("---"); st.markdown("### 📊 All Pitchers")
            st.dataframe(pd.DataFrame([{"Pitcher": p['name'], "vs": p['opp'], "ERA": f"{p['era']:.2f}", "Avg K": f"{p['avg_k']:.1f}", "5+K": f"{p['k5']*100:.0f}%", "6+K": f"{p['k6']*100:.0f}%", "7+K": f"{p['k7']*100:.0f}%", "Avg Runs": f"{p['avg_runs']:.1f}", "QS%": f"{p['qs']*100:.0f}%", "Win%": f"{p['win_pct']*100:.0f}%"} for p in k_sorted]), use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### 🎰 Parlay Calculator")
    num_legs = st.number_input("Legs", min_value=2, max_value=10, value=2)
    legs = []; combined = 1.0
    for i in range(int(num_legs)):
        c1, c2 = st.columns(2)
        with c1: team = st.text_input(f"Leg {i+1}", key=f"p_t_{i}", placeholder="e.g. Yankees ML")
        with c2: odds = st.number_input(f"Odds {i+1}", key=f"p_o_{i}", value=-110, step=5)
        if odds != 0: prob = ml_to_prob(odds); combined *= prob; legs.append({"team": team, "odds": odds, "prob": prob})
    if st.button("🎰 Calculate", type="primary", key="parlay_go") and len(legs) >= 2:
        for i, l in enumerate(legs): st.write(f"**Leg {i+1}:** {l['team']} ({l['odds']:+d}) — {l['prob']*100:.1f}%")
        st.markdown("---")
        r1, r2 = st.columns(2); r1.metric("Combined Prob", f"{combined*100:.1f}%"); r2.metric("Parlay Odds", prob_to_ml(combined))
        wager = st.number_input("Wager ($)", min_value=1.0, value=100.0, step=10.0, key="p_w")
        if combined > 0: st.metric("Potential Payout", f"${wager/combined:.2f}", f"+${wager/combined - wager:.2f}")

with tab6:
    st.markdown("### 💰 Bankroll Tracker")
    b1, b2 = st.columns(2)
    with b1: st.metric("Bankroll", f"${st.session_state.bankroll:.2f}")
    with b2:
        w = sum(1 for b in st.session_state.bet_history if b["result"] == "Win"); l = len(st.session_state.bet_history) - w
        st.metric("Record", f"{w}W-{l}L ({w/(w+l)*100:.0f}%)" if w+l > 0 else "0W-0L")
    new_br = st.number_input("Set Bankroll", value=st.session_state.bankroll, step=50.0, key="sbr")
    if st.button("Set", key="sbr_go"): st.session_state.bankroll = new_br; st.rerun()
    st.markdown("---"); st.markdown("**Log a Bet**")
    c1, c2, c3 = st.columns(3)
    with c1: bd = st.text_input("Description", key="bd", placeholder="Yankees ML")
    with c2: ba = st.number_input("Amount ($)", min_value=1.0, value=50.0, step=10.0, key="ba")
    with c3: bo = st.number_input("Odds", value=-110, step=5, key="bo")
    w1, w2 = st.columns(2)
    with w1:
        if st.button("✅ WIN", type="primary", key="lw") and bd:
            profit = ba * (100/abs(bo)) if bo < 0 else ba * (bo/100)
            st.session_state.bankroll += profit; st.session_state.bet_history.append({"team": bd, "amount": ba, "odds": bo, "result": "Win", "profit": profit, "date": datetime.now().strftime("%m/%d %I:%M%p")}); st.rerun()
    with w2:
        if st.button("❌ LOSS", key="ll") and bd:
            st.session_state.bankroll -= ba; st.session_state.bet_history.append({"team": bd, "amount": ba, "odds": bo, "result": "Loss", "profit": -ba, "date": datetime.now().strftime("%m/%d %I:%M%p")}); st.rerun()
    if st.session_state.bet_history:
        st.markdown("---")
        st.dataframe(pd.DataFrame(st.session_state.bet_history)[["date","team","amount","odds","result","profit"]].rename(columns={"date":"Date","team":"Bet","amount":"Amt","odds":"Odds","result":"Result","profit":"Profit"}), use_container_width=True, hide_index=True)
        running = []; cur = st.session_state.bankroll - sum(b["profit"] for b in st.session_state.bet_history)
        for b in st.session_state.bet_history: cur += b["profit"]; running.append(cur)
        st.line_chart(pd.DataFrame({"Bankroll": running}), height=200)
        tp = sum(b["profit"] for b in st.session_state.bet_history)
        st.success(f"📈 +${tp:.2f}") if tp > 0 else st.error(f"📉 -${abs(tp):.2f}")
        if st.button("🗑️ Clear", key="cl"): st.session_state.bet_history = []; st.rerun()

st.markdown("---")
st.markdown("<center><small style='color:#444'>🟢 GreenEye Scout v2.0</small></center>", unsafe_allow_html=True)