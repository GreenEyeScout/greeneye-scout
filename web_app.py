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
    .game-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #0e1117 100%);
        border: 1px solid #2ecc71;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }
    .team-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 8px 0;
    }
    .team-logo { width: 40px; height: 40px; }
    .best-bet {
        background: linear-gradient(135deg, #1a3a1a 0%, #0e1117 100%);
        border: 2px solid #2ecc71;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }
    .score-live {
        background: #1a1f2e;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 12px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

LOGO_MAP = {
    "Arizona Diamondbacks": "ari", "Atlanta Braves": "atl", "Baltimore Orioles": "bal",
    "Boston Red Sox": "bos", "Chicago Cubs": "chc", "Chicago White Sox": "chw",
    "Cincinnati Reds": "cin", "Cleveland Guardians": "cle", "Colorado Rockies": "col",
    "Detroit Tigers": "det", "Houston Astros": "hou", "Kansas City Royals": "kc",
    "Los Angeles Angels": "laa", "Los Angeles Dodgers": "lad", "Miami Marlins": "mia",
    "Milwaukee Brewers": "mil", "Minnesota Twins": "min", "New York Mets": "nym",
    "New York Yankees": "nyy", "Oakland Athletics": "oak", "Philadelphia Phillies": "phi",
    "Pittsburgh Pirates": "pit", "San Diego Padres": "sd", "San Francisco Giants": "sf",
    "Seattle Mariners": "sea", "St. Louis Cardinals": "stl", "Tampa Bay Rays": "tb",
    "Texas Rangers": "tex", "Toronto Blue Jays": "tor", "Washington Nationals": "wsh",
}

PARK_FACTORS = {
    "Arizona Diamondbacks": 1.04, "Atlanta Braves": 1.01, "Baltimore Orioles": 1.03,
    "Boston Red Sox": 1.08, "Chicago Cubs": 1.05, "Chicago White Sox": 1.02,
    "Cincinnati Reds": 1.06, "Cleveland Guardians": 0.98, "Colorado Rockies": 1.30,
    "Detroit Tigers": 0.96, "Houston Astros": 1.03, "Kansas City Royals": 1.00,
    "Los Angeles Angels": 0.97, "Los Angeles Dodgers": 0.97, "Miami Marlins": 0.90,
    "Milwaukee Brewers": 1.02, "Minnesota Twins": 1.00, "New York Mets": 0.94,
    "New York Yankees": 1.07, "Oakland Athletics": 1.00, "Philadelphia Phillies": 1.05,
    "Pittsburgh Pirates": 0.93, "San Diego Padres": 0.92, "San Francisco Giants": 0.93,
    "Seattle Mariners": 0.93, "St. Louis Cardinals": 0.97, "Tampa Bay Rays": 0.95,
    "Texas Rangers": 0.99, "Toronto Blue Jays": 1.01, "Washington Nationals": 1.00,
}

BALLPARK_NAMES = {
    "Arizona Diamondbacks": "Chase Field", "Atlanta Braves": "Truist Park",
    "Baltimore Orioles": "Camden Yards", "Boston Red Sox": "Fenway Park",
    "Chicago Cubs": "Wrigley Field", "Chicago White Sox": "Guaranteed Rate Field",
    "Cincinnati Reds": "Great American Ball Park", "Cleveland Guardians": "Progressive Field",
    "Colorado Rockies": "Coors Field", "Detroit Tigers": "Comerica Park",
    "Houston Astros": "Minute Maid Park", "Kansas City Royals": "Kauffman Stadium",
    "Los Angeles Angels": "Angel Stadium", "Los Angeles Dodgers": "Dodger Stadium",
    "Miami Marlins": "loanDepot Park", "Milwaukee Brewers": "American Family Field",
    "Minnesota Twins": "Target Field", "New York Mets": "Citi Field",
    "New York Yankees": "Yankee Stadium", "Oakland Athletics": "Sutter Health Park",
    "Philadelphia Phillies": "Citizens Bank Park", "Pittsburgh Pirates": "PNC Park",
    "San Diego Padres": "Petco Park", "San Francisco Giants": "Oracle Park",
    "Seattle Mariners": "T-Mobile Park", "St. Louis Cardinals": "Busch Stadium",
    "Tampa Bay Rays": "Tropicana Field", "Texas Rangers": "Globe Life Field",
    "Toronto Blue Jays": "Rogers Centre", "Washington Nationals": "Nationals Park",
}

TEAM_NAME_MAP = {
    "Arizona Diamondbacks": "Arizona Diamondbacks", "Atlanta Braves": "Atlanta Braves",
    "Baltimore Orioles": "Baltimore Orioles", "Boston Red Sox": "Boston Red Sox",
    "Chicago Cubs": "Chicago Cubs", "Chicago White Sox": "Chicago White Sox",
    "Cincinnati Reds": "Cincinnati Reds", "Cleveland Guardians": "Cleveland Guardians",
    "Colorado Rockies": "Colorado Rockies", "Detroit Tigers": "Detroit Tigers",
    "Houston Astros": "Houston Astros", "Kansas City Royals": "Kansas City Royals",
    "Los Angeles Angels": "Los Angeles Angels", "Los Angeles Dodgers": "Los Angeles Dodgers",
    "Miami Marlins": "Miami Marlins", "Milwaukee Brewers": "Milwaukee Brewers",
    "Minnesota Twins": "Minnesota Twins", "New York Mets": "New York Mets",
    "New York Yankees": "New York Yankees", "Oakland Athletics": "Oakland Athletics",
    "Philadelphia Phillies": "Philadelphia Phillies", "Pittsburgh Pirates": "Pittsburgh Pirates",
    "San Diego Padres": "San Diego Padres", "San Francisco Giants": "San Francisco Giants",
    "Seattle Mariners": "Seattle Mariners", "St. Louis Cardinals": "St. Louis Cardinals",
    "Tampa Bay Rays": "Tampa Bay Rays", "Texas Rangers": "Texas Rangers",
    "Toronto Blue Jays": "Toronto Blue Jays", "Washington Nationals": "Washington Nationals",
    "Athletics": "Oakland Athletics",
}


def get_logo_url(team):
    abbrev = LOGO_MAP.get(team, "mlb")
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{abbrev}.png"


@st.cache_data(ttl=600)
def get_headshot_cached(name):
    try:
        results = statsapi.lookup_player(name)
        if results:
            pid = results[0]['id']
            return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_180,q_auto:best/v1/people/{pid}/headshot/silo/current"
    except:
        pass
    return None


def sim_game(home_b, home_p, home_bp, away_b, away_p, away_bp, pf=1.0):
    hs, as_ = 0, 0
    ai, hi = 0, 0
    chp, cap = home_p, away_p
    for inn in range(1, 19):
        if inn == 7:
            if home_bp: chp = home_bp[0]
            if away_bp: cap = away_bp[0]
        ar, ai, _ = simulate_inning(away_b, chp, ai, None, False, True, pf)
        as_ += ar
        if inn >= 9 and hs > as_: break
        hr, hi, _ = simulate_inning(home_b, cap, hi, None, True, True, pf)
        hs += hr
        if inn >= 9 and hs != as_: break
    return hs, as_


def run_sim_detailed(teams, home, away, n, home_sp=None, away_sp=None):
    hd, ad = teams[home], teams[away]
    hp = home_sp or hd["starter"]
    ap = away_sp or ad["starter"]
    pf = PARK_FACTORS.get(home, 1.0)
    hw, aw, thr, tar = 0, 0, 0, 0
    trl, margins = [], []
    hrl, arl = 0, 0
    player_hrs = {}
    player_hits = {}

    for sim in range(n):
        hs_total, as_total = 0, 0
        ai, hi = 0, 0
        chp, cap = hp, ap
        h_stats, a_stats = {}, {}

        for inn in range(1, 19):
            if inn == 7:
                if hd["bullpen"]: chp = hd["bullpen"][0]
                if ad["bullpen"]: cap = ad["bullpen"][0]
            ar, ai, a_stats = simulate_inning(ad["batters"], chp, ai, a_stats, False, True, pf)
            as_total += ar
            if inn >= 9 and hs_total > as_total: break
            hr_runs, hi, h_stats = simulate_inning(hd["batters"], cap, hi, h_stats, True, True, pf)
            hs_total += hr_runs
            if inn >= 9 and hs_total != as_total: break

        all_stats = {**h_stats, **a_stats}
        for pname, pstats in all_stats.items():
            if pname not in player_hrs: player_hrs[pname] = 0
            if pname not in player_hits: player_hits[pname] = 0
            if pstats["HR"] > 0: player_hrs[pname] += 1
            if pstats["H"] >= 2: player_hits[pname] += 1

        trl.append(hs_total + as_total)
        margins.append(hs_total - as_total)
        thr += hs_total
        tar += as_total
        if hs_total > as_total:
            hw += 1
            if hs_total - as_total >= 2: hrl += 1
        else:
            aw += 1
            if as_total - hs_total >= 2: arl += 1

    ou = {}
    for line in [5.5, 6.5, 7.5, 8.5, 9.5, 10.5]:
        ou[line] = sum(1 for t in trl if t > line) / n

    props = {}
    for pname in player_hrs:
        props[pname] = {
            "hr_pct": player_hrs[pname] / n,
            "multi_hit_pct": player_hits.get(pname, 0) / n,
        }

    return {
        "home_pct": hw/n, "away_pct": aw/n,
        "avg_home": thr/n, "avg_away": tar/n,
        "avg_total": sum(trl)/n, "ou": ou,
        "home_rl": hrl/n, "away_rl": arl/n,
        "home_sp": hp.name, "away_sp": ap.name,
        "pf": pf, "home_throws": hp.throws, "away_throws": ap.throws,
        "total_runs_list": trl, "margins": margins,
        "props": props,
    }


def prob_to_ml(prob):
    if prob <= 0 or prob >= 1: return "+100"
    if prob >= 0.5: return f"{-round((prob / (1 - prob)) * 100)}"
    else: return f"+{round(((1 - prob) / prob) * 100)}"


def ml_to_prob(ml):
    if ml < 0: return abs(ml) / (abs(ml) + 100)
    else: return 100 / (ml + 100)


@st.cache_data(ttl=3600, show_spinner="🟢 Loading 2026 MLB data...")
def load_teams():
    return build_auto_rosters()


@st.cache_data(ttl=120)
def get_schedule(date):
    sched = statsapi.schedule(date=date)
    games = []
    for game in sched:
        games.append({
            "away": game["away_name"], "home": game["home_name"],
            "away_pitcher": game.get("away_probable_pitcher", "TBD"),
            "home_pitcher": game.get("home_probable_pitcher", "TBD"),
            "away_score": game.get("away_score", 0) or 0,
            "home_score": game.get("home_score", 0) or 0,
            "status": game.get("status", ""),
            "inning": game.get("current_inning", ""),
            "inning_state": game.get("inning_state", ""),
        })
    return games


if "bankroll" not in st.session_state: st.session_state.bankroll = 1000.0
if "bet_history" not in st.session_state: st.session_state.bet_history = []
if "prediction_history" not in st.session_state: st.session_state.prediction_history = []

teams = load_teams()

st.markdown("""
<div style='text-align: center; padding: 1.5rem 0 0.5rem 0;'>
    <h1 style='color: #2ecc71; margin-bottom: 0; font-size: 2.5rem;'>🟢 GreenEye Scout</h1>
    <p style='color: #aaa; font-size: 1.1rem; margin-top: 5px;'>MLB Prediction Engine — Powered by Monte Carlo Simulation</p>
    <p style='color: #666; font-size: 0.8rem;'>2026 Stats • Park Factors • L/R Splits • Injury Detection • Player Props</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📅 Predictions", "📺 Live Scores", "🔥 Best Bets",
    "🎯 Player Props", "🎰 Parlay", "💰 Bankroll"
])

# ============ TAB 1: PREDICTIONS ============
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        date_option = st.radio("Date", ["Today", "Tomorrow"], horizontal=True)
    with col2:
        num_sims = st.select_slider("Simulations", options=[1000, 2500, 5000, 10000, 25000], value=10000)

    if st.button("🟢 Run GreenEye Scout", type="primary"):
        if date_option == "Today":
            date = datetime.now().strftime('%m/%d/%Y')
        else:
            date = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')

        games = get_schedule(date)
        if not games:
            st.error("No games found")
        else:
            progress = st.progress(0)
            all_results = []

            for i, game in enumerate(games):
                away = TEAM_NAME_MAP.get(game["away"], game["away"])
                home = TEAM_NAME_MAP.get(game["home"], game["home"])
                if home not in teams or away not in teams: continue
                home_sp = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
                away_sp = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None
                result = run_sim_detailed(teams, home, away, num_sims, home_sp, away_sp)
                all_results.append((away, home, game, result))
                st.session_state.prediction_history.append({
                    "date": date, "away": away, "home": home,
                    "away_pct": result["away_pct"], "home_pct": result["home_pct"],
                    "pred_score": f"{result['avg_away']:.1f}-{result['avg_home']:.1f}",
                })
                progress.progress((i + 1) / len(games))

            for away, home, game, result in all_results:
                away_logo = get_logo_url(away)
                home_logo = get_logo_url(home)
                bp_name = BALLPARK_NAMES.get(home, "")

                st.markdown(f"""
                <div class='game-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div class='team-header'>
                            <img src='{away_logo}' class='team-logo'>
                            <span style='font-size: 1.2rem; font-weight: bold;'>{away}</span>
                        </div>
                        <span style='color: #666; font-size: 1.5rem;'>@</span>
                        <div class='team-header'>
                            <span style='font-size: 1.2rem; font-weight: bold;'>{home}</span>
                            <img src='{home_logo}' class='team-logo'>
                        </div>
                    </div>
                    <p style='color: #888; font-size: 0.85rem; margin-top: 8px;'>📍 {bp_name} (PF: {result["pf"]:.2f}) | SP: {result["away_sp"]} ({result["away_throws"]}) vs {result["home_sp"]} ({result["home_throws"]})</p>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns(4)
                away_ml = prob_to_ml(result['away_pct'])
                home_ml = prob_to_ml(result['home_pct'])
                c1.metric(away, f"{result['away_pct']*100:.1f}%", f"ML: {away_ml}")
                c2.metric(home, f"{result['home_pct']*100:.1f}%", f"ML: {home_ml}")
                c3.metric("Predicted Score", f"{result['avg_away']:.1f} - {result['avg_home']:.1f}")
                c4.metric("Total Runs", f"{result['avg_total']:.1f}")

                with st.expander("📊 Charts & Details"):
                    ch1, ch2 = st.columns(2)
                    with ch1:
                        st.markdown("**Total Runs Distribution**")
                        st.bar_chart(pd.DataFrame({"Runs": result["total_runs_list"]})["Runs"].value_counts().sort_index(), height=200)
                    with ch2:
                        st.markdown("**Win Margin Distribution**")
                        st.bar_chart(pd.DataFrame({"Margin": result["margins"]})["Margin"].value_counts().sort_index(), height=200)

                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.markdown("**Moneyline**")
                        st.write(f"{away}: {result['away_pct']*100:.1f}% ({away_ml})")
                        st.write(f"{home}: {result['home_pct']*100:.1f}% ({home_ml})")
                    with d2:
                        st.markdown("**Run Line (-1.5)**")
                        st.write(f"{away}: {result['away_rl']*100:.1f}%")
                        st.write(f"{home}: {result['home_rl']*100:.1f}%")
                    with d3:
                        st.markdown("**Over/Under**")
                        for line in [6.5, 7.5, 8.5, 9.5]:
                            st.write(f"O/U {line}: Over {result['ou'][line]*100:.1f}%")
                st.markdown("---")

            st.markdown("### 🟢 Summary")
            summary = []
            for away, home, game, result in all_results:
                fav = home if result['home_pct'] > result['away_pct'] else away
                summary.append({"Matchup": f"{away} @ {home}", "Favorite": fav,
                    "Win %": f"{max(result['home_pct'], result['away_pct'])*100:.1f}%",
                    "Score": f"{result['avg_away']:.1f} - {result['avg_home']:.1f}",
                    "Total": f"{result['avg_total']:.1f}"})
            st.table(summary)

# ============ TAB 2: LIVE SCOREBOARD ============
with tab2:
    st.markdown("### 📺 Live Scoreboard")
    if st.button("🔄 Refresh Scores", key="refresh"):
        st.cache_data.clear()

    live_games = get_schedule(datetime.now().strftime('%m/%d/%Y'))
    if not live_games:
        st.info("No games today")
    else:
        for game in live_games:
            away = TEAM_NAME_MAP.get(game["away"], game["away"])
            home = TEAM_NAME_MAP.get(game["home"], game["home"])
            away_logo = get_logo_url(away)
            home_logo = get_logo_url(home)
            status = game.get("status", "")
            a_score = game.get("away_score", 0) or 0
            h_score = game.get("home_score", 0) or 0
            inning = game.get("inning", "")
            state = game.get("inning_state", "")

            if "Final" in status:
                sdisplay = "🏁 Final"
            elif "Progress" in status or "Live" in status:
                sdisplay = f"🔴 LIVE — {state} {inning}"
            elif "Pre" in status or "Scheduled" in status:
                sdisplay = "⏰ Scheduled"
            else:
                sdisplay = status

            st.markdown(f"""
            <div class='score-live'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div class='team-header'>
                        <img src='{away_logo}' class='team-logo'>
                        <span style='font-size: 1.1rem;'>{away}</span>
                        <span style='font-size: 1.5rem; font-weight: bold; margin-left: 10px;'>{a_score}</span>
                    </div>
                    <span style='color: #888; font-size: 0.9rem;'>{sdisplay}</span>
                    <div class='team-header'>
                        <span style='font-size: 1.5rem; font-weight: bold; margin-right: 10px;'>{h_score}</span>
                        <span style='font-size: 1.1rem;'>{home}</span>
                        <img src='{home_logo}' class='team-logo'>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============ TAB 3: BEST BETS ============
with tab3:
    st.markdown("### 🔥 Best Bets — Auto Edge Finder")
    st.markdown("*Run predictions first (Tab 1), then best edges appear here*")

    if st.session_state.prediction_history:
        edges = []
        for pred in st.session_state.prediction_history[-30:]:
            if pred['home_pct'] > 0.55:
                edges.append({"team": pred['home'], "matchup": f"{pred['away']} @ {pred['home']}",
                    "win_pct": pred['home_pct'] * 100, "ml": prob_to_ml(pred['home_pct']), "date": pred['date']})
            if pred['away_pct'] > 0.55:
                edges.append({"team": pred['away'], "matchup": f"{pred['away']} @ {pred['home']}",
                    "win_pct": pred['away_pct'] * 100, "ml": prob_to_ml(pred['away_pct']), "date": pred['date']})

        edges.sort(key=lambda x: x['win_pct'], reverse=True)

        if edges:
            for edge in edges[:8]:
                logo = get_logo_url(edge['team'])
                fire = "🔥🔥🔥" if edge['win_pct'] > 65 else "🔥🔥" if edge['win_pct'] > 58 else "🔥"
                st.markdown(f"""
                <div class='best-bet'>
                    <div class='team-header'>
                        <img src='{logo}' class='team-logo'>
                        <span style='font-size: 1.2rem; font-weight: bold;'>{fire} {edge['team']}</span>
                        <span style='color: #2ecc71; font-size: 1.1rem; margin-left: auto;'>{edge['win_pct']:.1f}% ({edge['ml']})</span>
                    </div>
                    <p style='color: #888; margin-top: 5px;'>{edge['matchup']} — {edge['date']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No strong edges found yet.")
    else:
        st.info("Run predictions on Tab 1 first.")

# ============ TAB 4: PLAYER PROPS ============
with tab4:
    st.markdown("### 🎯 Player Props — Auto Edge Finder")

    col1, col2 = st.columns(2)
    with col1:
        props_date = st.radio("Date", ["Today", "Tomorrow"], horizontal=True, key="props_date")
    with col2:
        props_sims = st.select_slider("Simulations", options=[1000, 2500, 5000, 10000], value=5000, key="props_sims2")

    if st.button("🎯 Find Best Player Props", type="primary", key="auto_props"):
        if props_date == "Today":
            pdate = datetime.now().strftime('%m/%d/%Y')
        else:
            pdate = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')

        games = get_schedule(pdate)
        if not games:
            st.error("No games found")
        else:
            progress = st.progress(0)
            all_props = {}
            all_matchups = {}

            for i, game in enumerate(games):
                away = TEAM_NAME_MAP.get(game["away"], game["away"])
                home = TEAM_NAME_MAP.get(game["home"], game["home"])
                if home not in teams or away not in teams: continue
                home_sp = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
                away_sp = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None
                result = run_sim_detailed(teams, home, away, props_sims, home_sp, away_sp)
                for pname, pdata in result["props"].items():
                    all_props[pname] = pdata
                    all_matchups[pname] = f"{away} @ {home}"
                progress.progress((i + 1) / len(games))

            st.markdown("---")
            st.markdown("### 💥 Top Home Run Candidates")
            st.markdown("*Players most likely to go yard tonight*")

            hr_sorted = sorted(all_props.items(), key=lambda x: x[1]['hr_pct'], reverse=True)

            for rank, (name, props) in enumerate(hr_sorted[:15], 1):
                hr_pct = props['hr_pct'] * 100
                if hr_pct < 1: continue
                implied = f"+{round((1 - props['hr_pct']) / props['hr_pct'] * 100)}" if props['hr_pct'] > 0 and props['hr_pct'] < 1 else "N/A"
                headshot = get_headshot_cached(name)
                matchup = all_matchups.get(name, "")
                fire = "🔥🔥🔥" if hr_pct > 12 else "🔥🔥" if hr_pct > 8 else "🔥" if hr_pct > 5 else ""

                pc1, pc2, pc3, pc4 = st.columns([1, 3, 1, 1])
                with pc1:
                    if headshot:
                        st.image(headshot, width=55)
                    else:
                        st.write(f"**#{rank}**")
                with pc2:
                    st.markdown(f"**{name}** {fire}")
                    st.caption(matchup)
                with pc3:
                    st.metric("HR %", f"{hr_pct:.1f}%")
                with pc4:
                    st.metric("Implied", implied)

            st.markdown("---")
            st.markdown("### 🔥 Top Multi-Hit Candidates")
            st.markdown("*Players most likely to get 2+ hits tonight*")

            hit_sorted = sorted(all_props.items(), key=lambda x: x[1]['multi_hit_pct'], reverse=True)

            for rank, (name, props) in enumerate(hit_sorted[:15], 1):
                mh_pct = props['multi_hit_pct'] * 100
                if mh_pct < 5: continue
                if props['multi_hit_pct'] > 0 and props['multi_hit_pct'] < 1:
                    implied = f"+{round((1 - props['multi_hit_pct']) / props['multi_hit_pct'] * 100)}" if props['multi_hit_pct'] < 0.5 else f"-{round(props['multi_hit_pct'] / (1 - props['multi_hit_pct']) * 100)}"
                else:
                    implied = "N/A"
                headshot = get_headshot_cached(name)
                matchup = all_matchups.get(name, "")
                fire = "🔥🔥🔥" if mh_pct > 35 else "🔥🔥" if mh_pct > 25 else "🔥" if mh_pct > 15 else ""

                pc1, pc2, pc3, pc4 = st.columns([1, 3, 1, 1])
                with pc1:
                    if headshot:
                        st.image(headshot, width=55)
                    else:
                        st.write(f"**#{rank}**")
                with pc2:
                    st.markdown(f"**{name}** {fire}")
                    st.caption(matchup)
                with pc3:
                    st.metric("2+ Hits", f"{mh_pct:.1f}%")
                with pc4:
                    st.metric("Implied", implied)

            st.markdown("---")
            st.info("💡 Compare implied odds above to your sportsbook. If the book offers better odds than the sim implies, that's a value bet.")

# ============ TAB 5: PARLAY ============
with tab5:
    st.markdown("### 🎰 Parlay Calculator")
    num_legs = st.number_input("Legs in parlay", min_value=2, max_value=10, value=2)
    legs = []
    combined_prob = 1.0

    for i in range(int(num_legs)):
        c1, c2 = st.columns(2)
        with c1:
            team = st.text_input(f"Leg {i+1} Pick", key=f"p_team_{i}", placeholder="e.g. Yankees ML")
        with c2:
            odds = st.number_input(f"Leg {i+1} Odds", key=f"p_odds_{i}", value=-110, step=5)
        if odds != 0:
            prob = ml_to_prob(odds)
            combined_prob *= prob
            legs.append({"team": team, "odds": odds, "prob": prob})

    if st.button("🎰 Calculate", type="primary", key="parlay_go"):
        if len(legs) >= 2:
            for i, leg in enumerate(legs):
                st.write(f"**Leg {i+1}:** {leg['team']} ({leg['odds']:+d}) — {leg['prob']*100:.1f}%")
            st.markdown("---")
            r1, r2 = st.columns(2)
            r1.metric("Combined Probability", f"{combined_prob*100:.1f}%")
            r2.metric("Parlay Odds", prob_to_ml(combined_prob))
            wager = st.number_input("Wager ($)", min_value=1.0, value=100.0, step=10.0, key="p_wager")
            if combined_prob > 0:
                payout = wager / combined_prob
                st.metric("Potential Payout", f"${payout:.2f}", f"+${payout - wager:.2f} profit")

# ============ TAB 6: BANKROLL ============
with tab6:
    st.markdown("### 💰 Bankroll Tracker")
    b1, b2 = st.columns(2)
    with b1:
        st.metric("Bankroll", f"${st.session_state.bankroll:.2f}")
    with b2:
        wins = sum(1 for b in st.session_state.bet_history if b["result"] == "Win")
        losses = len(st.session_state.bet_history) - wins
        wr = (wins / len(st.session_state.bet_history) * 100) if st.session_state.bet_history else 0
        st.metric("Record", f"{wins}W - {losses}L ({wr:.0f}%)")

    st.markdown("---")
    new_br = st.number_input("Set Bankroll ($)", value=st.session_state.bankroll, step=50.0, key="set_br")
    if st.button("Set", key="set_br_go"):
        st.session_state.bankroll = new_br
        st.rerun()

    st.markdown("---")
    st.markdown("**Log a Bet**")
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        bet_desc = st.text_input("Description", placeholder="Yankees ML", key="b_desc")
    with lc2:
        bet_amt = st.number_input("Amount ($)", min_value=1.0, value=50.0, step=10.0, key="b_amt")
    with lc3:
        bet_odds = st.number_input("Odds", value=-110, step=5, key="b_odds")

    wc1, wc2 = st.columns(2)
    with wc1:
        if st.button("✅ WIN", type="primary", key="log_w"):
            if bet_desc:
                profit = bet_amt * (100 / abs(bet_odds)) if bet_odds < 0 else bet_amt * (bet_odds / 100)
                st.session_state.bankroll += profit
                st.session_state.bet_history.append({"team": bet_desc, "amount": bet_amt, "odds": bet_odds, "result": "Win", "profit": profit, "date": datetime.now().strftime("%m/%d %I:%M%p")})
                st.rerun()
    with wc2:
        if st.button("❌ LOSS", key="log_l"):
            if bet_desc:
                st.session_state.bankroll -= bet_amt
                st.session_state.bet_history.append({"team": bet_desc, "amount": bet_amt, "odds": bet_odds, "result": "Loss", "profit": -bet_amt, "date": datetime.now().strftime("%m/%d %I:%M%p")})
                st.rerun()

    if st.session_state.bet_history:
        st.markdown("---")
        hist_df = pd.DataFrame(st.session_state.bet_history)[["date", "team", "amount", "odds", "result", "profit"]]
        hist_df.columns = ["Date", "Bet", "Amount", "Odds", "Result", "Profit"]
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

        st.markdown("**Bankroll Over Time**")
        running = []
        cur = st.session_state.bankroll - sum(b["profit"] for b in st.session_state.bet_history)
        for b in st.session_state.bet_history:
            cur += b["profit"]
            running.append(cur)
        st.line_chart(pd.DataFrame({"Bankroll": running}), height=250)

        total_profit = sum(b["profit"] for b in st.session_state.bet_history)
        if total_profit > 0:
            st.success(f"📈 Total Profit: +${total_profit:.2f}")
        else:
            st.error(f"📉 Total Loss: -${abs(total_profit):.2f}")

        if st.button("🗑️ Clear History", key="clear"):
            st.session_state.bet_history = []
            st.rerun()

st.markdown("---")
st.markdown("<center><small style='color: #444;'>🟢 GreenEye Scout v2.0</small></center>", unsafe_allow_html=True)