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

# ⬇️ YOUR ODDS API KEY
ODDS_API_KEY = "439bc802948590bfe717abda18d2421c"

st.markdown("""
<style>
    .pick-card { background: linear-gradient(135deg, #1a3a1a 0%, #0e1117 100%); border: 2px solid #2ecc71; border-radius: 16px; padding: 24px; margin: 16px 0; }
    .pick-card-medium { background: linear-gradient(135deg, #2a2a1a 0%, #0e1117 100%); border: 2px solid #f39c12; border-radius: 16px; padding: 24px; margin: 16px 0; }
    .pick-card-avoid { background: linear-gradient(135deg, #1a1a2a 0%, #0e1117 100%); border: 1px solid #333; border-radius: 16px; padding: 24px; margin: 16px 0; }
    .team-header { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
    .team-logo { width: 45px; height: 45px; }
    .reasoning { background: #111; border-radius: 8px; padding: 16px; margin-top: 12px; color: #ccc; font-size: 0.95rem; line-height: 1.6; }
    .score-live { background: #1a1f2e; border: 1px solid #333; border-radius: 8px; padding: 12px; margin: 5px 0; }
    .edge-badge { background: #2ecc71; color: black; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; }
    .edge-badge-med { background: #f39c12; color: black; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

LOGO_MAP = {"Arizona Diamondbacks": "ari", "Atlanta Braves": "atl", "Baltimore Orioles": "bal", "Boston Red Sox": "bos", "Chicago Cubs": "chc", "Chicago White Sox": "chw", "Cincinnati Reds": "cin", "Cleveland Guardians": "cle", "Colorado Rockies": "col", "Detroit Tigers": "det", "Houston Astros": "hou", "Kansas City Royals": "kc", "Los Angeles Angels": "laa", "Los Angeles Dodgers": "lad", "Miami Marlins": "mia", "Milwaukee Brewers": "mil", "Minnesota Twins": "min", "New York Mets": "nym", "New York Yankees": "nyy", "Oakland Athletics": "oak", "Philadelphia Phillies": "phi", "Pittsburgh Pirates": "pit", "San Diego Padres": "sd", "San Francisco Giants": "sf", "Seattle Mariners": "sea", "St. Louis Cardinals": "stl", "Tampa Bay Rays": "tb", "Texas Rangers": "tex", "Toronto Blue Jays": "tor", "Washington Nationals": "wsh"}
PARK_FACTORS = {"Arizona Diamondbacks": 1.04, "Atlanta Braves": 1.01, "Baltimore Orioles": 1.03, "Boston Red Sox": 1.08, "Chicago Cubs": 1.05, "Chicago White Sox": 1.02, "Cincinnati Reds": 1.06, "Cleveland Guardians": 0.98, "Colorado Rockies": 1.30, "Detroit Tigers": 0.96, "Houston Astros": 1.03, "Kansas City Royals": 1.00, "Los Angeles Angels": 0.97, "Los Angeles Dodgers": 0.97, "Miami Marlins": 0.90, "Milwaukee Brewers": 1.02, "Minnesota Twins": 1.00, "New York Mets": 0.94, "New York Yankees": 1.07, "Oakland Athletics": 1.00, "Philadelphia Phillies": 1.05, "Pittsburgh Pirates": 0.93, "San Diego Padres": 0.92, "San Francisco Giants": 0.93, "Seattle Mariners": 0.93, "St. Louis Cardinals": 0.97, "Tampa Bay Rays": 0.95, "Texas Rangers": 0.99, "Toronto Blue Jays": 1.01, "Washington Nationals": 1.00}
BALLPARK_NAMES = {"Arizona Diamondbacks": "Chase Field", "Atlanta Braves": "Truist Park", "Baltimore Orioles": "Camden Yards", "Boston Red Sox": "Fenway Park", "Chicago Cubs": "Wrigley Field", "Chicago White Sox": "Guaranteed Rate Field", "Cincinnati Reds": "Great American Ball Park", "Cleveland Guardians": "Progressive Field", "Colorado Rockies": "Coors Field", "Detroit Tigers": "Comerica Park", "Houston Astros": "Minute Maid Park", "Kansas City Royals": "Kauffman Stadium", "Los Angeles Angels": "Angel Stadium", "Los Angeles Dodgers": "Dodger Stadium", "Miami Marlins": "loanDepot Park", "Milwaukee Brewers": "American Family Field", "Minnesota Twins": "Target Field", "New York Mets": "Citi Field", "New York Yankees": "Yankee Stadium", "Oakland Athletics": "Sutter Health Park", "Philadelphia Phillies": "Citizens Bank Park", "Pittsburgh Pirates": "PNC Park", "San Diego Padres": "Petco Park", "San Francisco Giants": "Oracle Park", "Seattle Mariners": "T-Mobile Park", "St. Louis Cardinals": "Busch Stadium", "Tampa Bay Rays": "Tropicana Field", "Texas Rangers": "Globe Life Field", "Toronto Blue Jays": "Rogers Centre", "Washington Nationals": "Nationals Park"}
TEAM_NAME_MAP = {"Arizona Diamondbacks": "Arizona Diamondbacks", "Atlanta Braves": "Atlanta Braves", "Baltimore Orioles": "Baltimore Orioles", "Boston Red Sox": "Boston Red Sox", "Chicago Cubs": "Chicago Cubs", "Chicago White Sox": "Chicago White Sox", "Cincinnati Reds": "Cincinnati Reds", "Cleveland Guardians": "Cleveland Guardians", "Colorado Rockies": "Colorado Rockies", "Detroit Tigers": "Detroit Tigers", "Houston Astros": "Houston Astros", "Kansas City Royals": "Kansas City Royals", "Los Angeles Angels": "Los Angeles Angels", "Los Angeles Dodgers": "Los Angeles Dodgers", "Miami Marlins": "Miami Marlins", "Milwaukee Brewers": "Milwaukee Brewers", "Minnesota Twins": "Minnesota Twins", "New York Mets": "New York Mets", "New York Yankees": "New York Yankees", "Oakland Athletics": "Oakland Athletics", "Philadelphia Phillies": "Philadelphia Phillies", "Pittsburgh Pirates": "Pittsburgh Pirates", "San Diego Padres": "San Diego Padres", "San Francisco Giants": "San Francisco Giants", "Seattle Mariners": "Seattle Mariners", "St. Louis Cardinals": "St. Louis Cardinals", "Tampa Bay Rays": "Tampa Bay Rays", "Texas Rangers": "Texas Rangers", "Toronto Blue Jays": "Toronto Blue Jays", "Washington Nationals": "Washington Nationals", "Athletics": "Oakland Athletics"}

def get_logo(team): return f"https://a.espncdn.com/i/teamlogos/mlb/500/{LOGO_MAP.get(team, 'mlb')}.png"

@st.cache_data(ttl=600)
def get_headshot(name):
    try:
        r = statsapi.lookup_player(name)
        if r: return f"https://img.mlbstatic.com/mlb-photos/image/upload/w_180,q_auto:best/v1/people/{r[0]['id']}/headshot/silo/current"
    except: pass
    return None

def sim_game(hd, ad, hp, ap, pf):
    hs, as_ = 0, 0
    ai, hi = 0, 0
    chp, cap = hp, ap
    h_stats, a_stats = {}, {}
    sp_hk, sp_ak, sp_hr, sp_ar = 0, 0, 0, 0
    for inn in range(1, 10):
        a_inn = {}
        if inn <= 6:
            ar, ai, a_inn = simulate_inning(ad["batters"], chp, ai, a_inn, False, True, pf)
            sp_hk += sum(s["SO"] for s in a_inn.values()); sp_hr += ar
        else:
            cur = hd["bullpen"][0] if hd["bullpen"] else chp
            ar, ai, a_inn = simulate_inning(ad["batters"], cur, ai, a_inn, False, True, pf)
        as_ += ar
        for k, v in a_inn.items():
            if k not in a_stats: a_stats[k] = {"HR": 0, "H": 0}
            a_stats[k]["HR"] += v.get("HR", 0); a_stats[k]["H"] += v.get("H", 0)
        if inn >= 9 and hs > as_: break
        h_inn = {}
        if inn <= 6:
            hr, hi, h_inn = simulate_inning(hd["batters"], cap, hi, h_inn, True, True, pf)
            sp_ak += sum(s["SO"] for s in h_inn.values()); sp_ar += hr
        else:
            cur = ad["bullpen"][0] if ad["bullpen"] else cap
            hr, hi, h_inn = simulate_inning(hd["batters"], cur, hi, h_inn, True, True, pf)
        hs += hr
        for k, v in h_inn.items():
            if k not in h_stats: h_stats[k] = {"HR": 0, "H": 0}
            h_stats[k]["HR"] += v.get("HR", 0); h_stats[k]["H"] += v.get("H", 0)
        if inn >= 9 and hs != as_: break
    return hs, as_, h_stats, a_stats, sp_hk, sp_ak, sp_hr, sp_ar

def run_full_sim(teams, home, away, n, home_sp=None, away_sp=None):
    hd, ad = teams[home], teams[away]
    hp = home_sp or hd["starter"]; ap = away_sp or ad["starter"]
    pf = PARK_FACTORS.get(home, 1.0)
    hw, aw, thr, tar, hrl, arl = 0, 0, 0, 0, 0, 0
    trl, margins = [], []
    player_hrs, player_hits = {}, {}
    hsp_ks, asp_ks, hsp_runs, asp_runs = [], [], [], []

    for _ in range(n):
        hs, as_, h_st, a_st, hk, ak, hr_a, ar_a = sim_game(hd, ad, hp, ap, pf)
        trl.append(hs + as_); margins.append(hs - as_); thr += hs; tar += as_
        hsp_ks.append(hk); asp_ks.append(ak); hsp_runs.append(hr_a); asp_runs.append(ar_a)
        if hs > as_: hw += 1; hrl += (1 if hs - as_ >= 2 else 0)
        else: aw += 1; arl += (1 if as_ - hs >= 2 else 0)
        for pn, ps in {**h_st, **a_st}.items():
            if pn not in player_hrs: player_hrs[pn] = 0
            if pn not in player_hits: player_hits[pn] = 0
            if ps["HR"] > 0: player_hrs[pn] += 1
            if ps["H"] >= 2: player_hits[pn] += 1

    ou = {l: sum(1 for t in trl if t > l)/n for l in [5.5, 6.5, 7.5, 8.5, 9.5, 10.5]}
    return {
        "home_pct": hw/n, "away_pct": aw/n, "avg_home": thr/n, "avg_away": tar/n,
        "avg_total": sum(trl)/n, "ou": ou, "home_rl": hrl/n, "away_rl": arl/n,
        "home_sp": hp.name, "away_sp": ap.name, "home_era": hp.era, "away_era": ap.era,
        "home_throws": hp.throws, "away_throws": ap.throws, "pf": pf,
        "total_runs_list": trl, "margins": margins,
        "props": {pn: {"hr_pct": player_hrs[pn]/n, "mh_pct": player_hits.get(pn,0)/n} for pn in player_hrs},
        "pitcher_props": {
            hp.name: {"avg_k": sum(hsp_ks)/n, "k5": sum(1 for k in hsp_ks if k>=5)/n, "k6": sum(1 for k in hsp_ks if k>=6)/n, "k7": sum(1 for k in hsp_ks if k>=7)/n, "avg_runs": sum(hsp_runs)/n, "qs": sum(1 for r in hsp_runs if r<=3)/n},
            ap.name: {"avg_k": sum(asp_ks)/n, "k5": sum(1 for k in asp_ks if k>=5)/n, "k6": sum(1 for k in asp_ks if k>=6)/n, "k7": sum(1 for k in asp_ks if k>=7)/n, "avg_runs": sum(asp_runs)/n, "qs": sum(1 for r in asp_runs if r<=3)/n},
        },
    }

def prob_to_ml(p):
    if p <= 0 or p >= 1: return "+100"
    return f"{-round(p/(1-p)*100)}" if p >= 0.5 else f"+{round((1-p)/p*100)}"

def ml_to_prob(ml):
    return abs(ml)/(abs(ml)+100) if ml < 0 else 100/(ml+100)

def build_reasoning(pick_team, opp_team, result, market_prob, pick_side, home_name):
    is_home = pick_team == home_name
    pick_sp = result["home_sp"] if is_home else result["away_sp"]
    opp_sp = result["away_sp"] if is_home else result["home_sp"]
    pick_era = result["home_era"] if is_home else result["away_era"]
    opp_era = result["away_era"] if is_home else result["home_era"]
    pick_throws = result["home_throws"] if is_home else result["away_throws"]
    sim_pct = result["home_pct"] if is_home else result["away_pct"]
    edge = (sim_pct - market_prob) * 100
    pf = result["pf"]
    bp_name = BALLPARK_NAMES.get(home_name, "")

    reasons = []

    # Pitching matchup
    if pick_era < opp_era - 1.0:
        reasons.append(f"**Pitching dominance.** {pick_sp} ({pick_era:.2f} ERA) has a massive advantage over {opp_sp} ({opp_era:.2f} ERA). That {opp_era - pick_era:.2f} ERA gap is significant — the sim sees {pick_sp} limiting damage while {opp_sp} is expected to give up runs.")
    elif pick_era < opp_era:
        reasons.append(f"**Pitching edge.** {pick_sp} ({pick_era:.2f} ERA) gets the nod over {opp_sp} ({opp_era:.2f} ERA). Not a huge gap, but in a tight game this pitching advantage tips the scale.")
    else:
        reasons.append(f"**Despite facing a solid arm** in {opp_sp} ({opp_era:.2f} ERA), the sim still favors {pick_team} here based on lineup strength against {pick_sp} ({pick_era:.2f} ERA).")

    # Park factor
    if pf >= 1.10:
        reasons.append(f"**Park factor boost.** {bp_name} (PF: {pf:.2f}) is one of the most hitter-friendly parks in baseball. Expect elevated run totals — this benefits the team with more offensive firepower.")
    elif pf <= 0.93:
        reasons.append(f"**Pitcher's park.** {bp_name} (PF: {pf:.2f}) suppresses offense significantly. Good pitching plays up here, giving {pick_sp} an additional edge in this environment.")

    # Home/away
    if is_home:
        reasons.append(f"**Home field advantage.** {pick_team} gets the crowd, the last at-bat, and the comfort of playing at {bp_name}. The sim gives home teams a built-in 4% boost which compounds across 9 innings.")
    else:
        reasons.append(f"**Road warrior pick.** Even without home field advantage, the sim sees enough value in {pick_team}'s lineup and pitching matchup to overcome the away disadvantage.")

    # Market edge
    if edge > 10:
        reasons.append(f"**Significant market mispricing.** The sim has {pick_team} at {sim_pct*100:.1f}% while the market implies {market_prob*100:.1f}% — that's a +{edge:.1f}% edge. The market may be undervaluing {pick_sp}'s impact or overrating {opp_sp}.")
    elif edge > 5:
        reasons.append(f"**Solid edge found.** The sim sees {pick_team} at {sim_pct*100:.1f}% vs the market's {market_prob*100:.1f}% — a +{edge:.1f}% gap. This is the kind of edge that compounds profitably over time.")
    else:
        reasons.append(f"**Moderate edge.** At +{edge:.1f}% over market price, this isn't a slam dunk but it's a spot where the sim consistently sees value.")

    return " ".join(reasons)

def get_live_odds():
    if ODDS_API_KEY == "YOUR_KEY_HERE": return None
    try:
        r = requests.get("https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/", params={"apiKey": ODDS_API_KEY, "regions": "us", "markets": "h2h,totals", "oddsFormat": "american"}, timeout=10)
        data = r.json(); odds = {}
        for g in data:
            h = TEAM_NAME_MAP.get(g.get("home_team",""), g.get("home_team","")); a = TEAM_NAME_MAP.get(g.get("away_team",""), g.get("away_team",""))
            best = {"home_ml": None, "away_ml": None, "total": None}
            for b in g.get("bookmakers", [])[:1]:
                for m in b.get("markets", []):
                    if m["key"] == "h2h":
                        for o in m["outcomes"]:
                            mapped = TEAM_NAME_MAP.get(o["name"], o["name"])
                            if mapped == h: best["home_ml"] = o["price"]
                            elif mapped == a: best["away_ml"] = o["price"]
                    elif m["key"] == "totals":
                        for o in m["outcomes"]:
                            if o["name"] == "Over": best["total"] = o.get("point"); break
            odds[f"{a}@{h}"] = best
        return odds
    except: return None

@st.cache_data(ttl=3600, show_spinner="🟢 Loading 2026 MLB data...")
def load_teams(): return build_auto_rosters()

@st.cache_data(ttl=120)
def get_schedule(date):
    return [{"away": g["away_name"], "home": g["home_name"], "away_pitcher": g.get("away_probable_pitcher","TBD"), "home_pitcher": g.get("home_probable_pitcher","TBD"), "away_score": g.get("away_score",0) or 0, "home_score": g.get("home_score",0) or 0, "status": g.get("status",""), "inning": g.get("current_inning",""), "inning_state": g.get("inning_state","")} for g in statsapi.schedule(date=date)]

if "bankroll" not in st.session_state: st.session_state.bankroll = 1000.0
if "bet_history" not in st.session_state: st.session_state.bet_history = []

teams = load_teams()

st.markdown("<div style='text-align:center;padding:1.5rem 0'><h1 style='color:#2ecc71;font-size:2.8rem;margin-bottom:0'>🟢 GreenEye Scout</h1><p style='color:#aaa;font-size:1.2rem;margin-top:5px'>Find the Edge. Make the Play.</p></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Tonight's Plays", "📺 Scoreboard", "⚾ Props", "🎰 Parlay", "💰 Bankroll"])

# ============ TONIGHT'S PLAYS ============
with tab1:
    col1, col2 = st.columns(2)
    with col1: date_opt = st.radio("", ["Today", "Tomorrow"], horizontal=True)
    with col2: n_sims = st.select_slider("Simulations", options=[5000, 10000, 25000], value=10000)

    if st.button("🟢 Scout Tonight's Games", type="primary", use_container_width=True):
        date = datetime.now().strftime('%m/%d/%Y') if date_opt == "Today" else (datetime.now()+timedelta(days=1)).strftime('%m/%d/%Y')
        games = get_schedule(date)
        if not games: st.error("No games found"); st.stop()

        st.info(f"📊 Fetching odds & running {n_sims} simulations across {len(games)} games...")
        all_odds = get_live_odds()
        progress = st.progress(0)
        picks = []

        for i, game in enumerate(games):
            away = TEAM_NAME_MAP.get(game["away"], game["away"]); home = TEAM_NAME_MAP.get(game["home"], game["home"])
            if home not in teams or away not in teams: continue
            hsp = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
            asp = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None
            result = run_full_sim(teams, home, away, n_sims, hsp, asp)

            game_odds = all_odds.get(f"{away}@{home}") if all_odds else None
            if game_odds and game_odds.get("home_ml"):
                hm_prob = ml_to_prob(game_odds["home_ml"]); am_prob = ml_to_prob(game_odds["away_ml"])
                h_edge = (result["home_pct"] - hm_prob) * 100; a_edge = (result["away_pct"] - am_prob) * 100
                if h_edge > a_edge:
                    picks.append({"pick": home, "opp": away, "side": "HOME", "edge": h_edge, "ml": game_odds["home_ml"], "market_prob": hm_prob, "result": result, "game": game, "home": home, "away": away, "total_line": game_odds.get("total")})
                else:
                    picks.append({"pick": away, "opp": home, "side": "AWAY", "edge": a_edge, "ml": game_odds["away_ml"], "market_prob": am_prob, "result": result, "game": game, "home": home, "away": away, "total_line": game_odds.get("total")})
            else:
                fav = home if result["home_pct"] > result["away_pct"] else away
                opp = away if fav == home else home
                picks.append({"pick": fav, "opp": opp, "side": "HOME" if fav == home else "AWAY", "edge": 0, "ml": None, "market_prob": 0.5, "result": result, "game": game, "home": home, "away": away, "total_line": None})
            progress.progress((i+1)/len(games))

        picks.sort(key=lambda x: x["edge"], reverse=True)

        # TOP PLAYS
        top = [p for p in picks if p["edge"] > 3]
        mid = [p for p in picks if 0 < p["edge"] <= 3]
        avoid = [p for p in picks if p["edge"] <= 0]

        if top:
            st.markdown(f"## 🔥 Top Plays ({len(top)} games with edge)")
            for rank, p in enumerate(top, 1):
                r = p["result"]; sim_pct = r["home_pct"] if p["pick"] == p["home"] else r["away_pct"]
                card_class = "pick-card"
                fire = "🔥🔥🔥" if p["edge"] > 10 else "🔥🔥" if p["edge"] > 5 else "🔥"

                reasoning = build_reasoning(p["pick"], p["opp"], r, p["market_prob"], p["side"], p["home"])

                st.markdown(f"""<div class='{card_class}'>
                    <div style='display:flex;justify-content:space-between;align-items:center'>
                        <div class='team-header'>
                            <img src='{get_logo(p["pick"])}' class='team-logo' style='width:50px;height:50px'>
                            <div>
                                <span style='font-size:1.4rem;font-weight:bold'>{fire} {p["pick"]}</span><br>
                                <span style='color:#888'>vs {p["opp"]} • {p["side"]}</span>
                            </div>
                        </div>
                        <div style='text-align:right'>
                            <span class='edge-badge'>+{p["edge"]:.1f}% EDGE</span><br>
                            <span style='color:#aaa;font-size:1.1rem;margin-top:4px;display:block'>ML: {p["ml"]:+d if p["ml"] else "N/A"}</span>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Sim Win %", f"{sim_pct*100:.1f}%")
                c2.metric("Market", f"{p['market_prob']*100:.1f}%")
                c3.metric("Predicted", f"{r['avg_away']:.1f} - {r['avg_home']:.1f}")
                c4.metric("Total Runs", f"{r['avg_total']:.1f}")

                st.markdown(f"<div class='reasoning'>{reasoning}</div>", unsafe_allow_html=True)

                with st.expander("📊 Deep Dive"):
                    ch1, ch2 = st.columns(2)
                    with ch1: st.markdown("**Run Distribution**"); st.bar_chart(pd.DataFrame({"R": r["total_runs_list"]})["R"].value_counts().sort_index(), height=180)
                    with ch2: st.markdown("**Margin Distribution**"); st.bar_chart(pd.DataFrame({"M": r["margins"]})["M"].value_counts().sort_index(), height=180)
                    d1, d2 = st.columns(2)
                    with d1:
                        st.markdown("**Run Line (-1.5)**"); st.write(f"{p['away']}: {r['away_rl']*100:.1f}%"); st.write(f"{p['home']}: {r['home_rl']*100:.1f}%")
                    with d2:
                        st.markdown("**Over/Under**")
                        for line in [6.5, 7.5, 8.5, 9.5]: st.write(f"O/U {line}: Over {r['ou'][line]*100:.1f}%")
                st.markdown("---")

        if mid:
            st.markdown(f"## ⚡ Lean Plays ({len(mid)} games)")
            for p in mid:
                r = p["result"]; sim_pct = r["home_pct"] if p["pick"] == p["home"] else r["away_pct"]
                st.markdown(f"""<div class='pick-card-medium'>
                    <div style='display:flex;justify-content:space-between;align-items:center'>
                        <div class='team-header'><img src='{get_logo(p["pick"])}' class='team-logo'><span style='font-size:1.2rem;font-weight:bold'>⚡ {p["pick"]}</span></div>
                        <div style='text-align:right'><span class='edge-badge-med'>+{p["edge"]:.1f}%</span><br><span style='color:#aaa'>ML: {p["ml"]:+d if p["ml"] else "N/A"} | Sim: {sim_pct*100:.1f}%</span></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        if avoid:
            with st.expander(f"⛔ No Edge ({len(avoid)} games) — Avoid"):
                for p in avoid:
                    st.write(f"❌ {p['away']} @ {p['home']} — No value found")

# ============ SCOREBOARD ============
with tab2:
    st.markdown("### 📺 Live Scoreboard")
    if st.button("🔄 Refresh", key="ref"): st.cache_data.clear()
    for g in get_schedule(datetime.now().strftime('%m/%d/%Y')):
        a, h = TEAM_NAME_MAP.get(g["away"], g["away"]), TEAM_NAME_MAP.get(g["home"], g["home"])
        s = g.get("status",""); sd = "🏁 Final" if "Final" in s else f"🔴 LIVE — {g.get('inning_state','')} {g.get('inning','')}" if "Progress" in s else "⏰ Scheduled"
        st.markdown(f"<div class='score-live'><div style='display:flex;justify-content:space-between;align-items:center'><div class='team-header'><img src='{get_logo(a)}' class='team-logo'><span>{a}</span><span style='font-size:1.5rem;font-weight:bold;margin-left:10px'>{g.get('away_score',0)}</span></div><span style='color:#888'>{sd}</span><div class='team-header'><span style='font-size:1.5rem;font-weight:bold;margin-right:10px'>{g.get('home_score',0)}</span><span>{h}</span><img src='{get_logo(h)}' class='team-logo'></div></div></div>", unsafe_allow_html=True)

# ============ PROPS ============
with tab3:
    st.markdown("### ⚾ Player & Pitcher Props")
    col1, col2 = st.columns(2)
    with col1: pr_date = st.radio("", ["Today", "Tomorrow"], horizontal=True, key="pr_d")
    with col2: pr_sims = st.select_slider("Sims", options=[2500, 5000, 10000], value=5000, key="pr_s")
    if st.button("🎯 Find Best Props", type="primary", key="pr_go", use_container_width=True):
        date = datetime.now().strftime('%m/%d/%Y') if pr_date == "Today" else (datetime.now()+timedelta(days=1)).strftime('%m/%d/%Y')
        games = get_schedule(date)
        if not games: st.error("No games"); st.stop()
        progress = st.progress(0); all_props = {}; all_matchups = {}; all_pp = []
        for i, g in enumerate(games):
            a, h = TEAM_NAME_MAP.get(g["away"], g["away"]), TEAM_NAME_MAP.get(g["home"], g["home"])
            if h not in teams or a not in teams: continue
            hsp = find_pitcher(g["home_pitcher"]) if g["home_pitcher"]!="TBD" else None
            asp = find_pitcher(g["away_pitcher"]) if g["away_pitcher"]!="TBD" else None
            r = run_full_sim(teams, h, a, pr_sims, hsp, asp)
            for pn, pd in r["props"].items(): all_props[pn] = pd; all_matchups[pn] = f"{a} @ {h}"
            for pn, pp in r["pitcher_props"].items(): pp["name"]=pn; pp["matchup"]=f"{a} @ {h}"; all_pp.append(pp)
            progress.progress((i+1)/len(games))

        st.markdown("---"); st.markdown("### 💥 Top HR Candidates")
        for rank, (n, p) in enumerate(sorted(all_props.items(), key=lambda x: x[1]['hr_pct'], reverse=True)[:10], 1):
            if p['hr_pct'] < 0.01: continue
            hs = get_headshot(n); implied = f"+{round((1-p['hr_pct'])/p['hr_pct']*100)}" if 0 < p['hr_pct'] < 1 else "N/A"
            c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
            with c1:
                if hs: st.image(hs, width=55)
                else: st.write(f"#{rank}")
            with c2: st.markdown(f"**{n}**"); st.caption(all_matchups.get(n,""))
            with c3: st.metric("HR %", f"{p['hr_pct']*100:.1f}%")
            with c4: st.metric("Implied", implied)

        st.markdown("---"); st.markdown("### 🥴 Top K Props (Pitchers through 6 IP)")
        for rank, p in enumerate(sorted(all_pp, key=lambda x: x['avg_k'], reverse=True)[:10], 1):
            hs = get_headshot(p['name']); fire = "🔥🔥🔥" if p['avg_k'] > 6 else "🔥🔥" if p['avg_k'] > 5 else "🔥" if p['avg_k'] > 4 else ""
            c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1, 1])
            with c1:
                if hs: st.image(hs, width=55)
                else: st.write(f"#{rank}")
            with c2: st.markdown(f"**{p['name']}** {fire}"); st.caption(f"{p['matchup']} | Avg K: {p['avg_k']:.1f}")
            with c3: st.metric("5+ K", f"{p['k5']*100:.0f}%")
            with c4: st.metric("6+ K", f"{p['k6']*100:.0f}%")
            with c5: st.metric("7+ K", f"{p['k7']*100:.0f}%")

# ============ PARLAY ============
with tab4:
    st.markdown("### 🎰 Parlay Calculator")
    nl = st.number_input("Legs", min_value=2, max_value=10, value=2)
    legs = []; cp = 1.0
    for i in range(int(nl)):
        c1, c2 = st.columns(2)
        with c1: t = st.text_input(f"Leg {i+1}", key=f"pt{i}", placeholder="Yankees ML")
        with c2: o = st.number_input(f"Odds", key=f"po{i}", value=-110, step=5)
        if o != 0: p = ml_to_prob(o); cp *= p; legs.append({"t": t, "o": o, "p": p})
    if st.button("🎰 Calculate", type="primary", key="pcalc") and len(legs) >= 2:
        for i, l in enumerate(legs): st.write(f"**{i+1}.** {l['t']} ({l['o']:+d}) — {l['p']*100:.1f}%")
        st.markdown("---"); r1, r2 = st.columns(2); r1.metric("Combined", f"{cp*100:.1f}%"); r2.metric("Odds", prob_to_ml(cp))
        w = st.number_input("Wager ($)", value=100.0, step=10.0, key="pw")
        if cp > 0: st.metric("Payout", f"${w/cp:.2f}", f"+${w/cp-w:.2f}")

# ============ BANKROLL ============
with tab5:
    st.markdown("### 💰 Bankroll")
    b1, b2 = st.columns(2)
    with b1: st.metric("Balance", f"${st.session_state.bankroll:.2f}")
    with b2:
        w = sum(1 for b in st.session_state.bet_history if b["r"] == "W"); l = len(st.session_state.bet_history) - w
        st.metric("Record", f"{w}W-{l}L ({w/(w+l)*100:.0f}%)" if w+l > 0 else "0-0")
    nb = st.number_input("Set Bankroll", value=st.session_state.bankroll, step=50.0, key="nb")
    if st.button("Set", key="nbs"): st.session_state.bankroll = nb; st.rerun()
    st.markdown("---"); st.markdown("**Log Bet**")
    c1, c2, c3 = st.columns(3)
    with c1: bd = st.text_input("Pick", key="bd2", placeholder="Yankees ML")
    with c2: ba = st.number_input("$", min_value=1.0, value=50.0, step=10.0, key="ba2")
    with c3: bo = st.number_input("Odds", value=-110, step=5, key="bo2")
    w1, w2 = st.columns(2)
    with w1:
        if st.button("✅ WIN", type="primary", key="lw2") and bd:
            pr = ba*(100/abs(bo)) if bo < 0 else ba*(bo/100)
            st.session_state.bankroll += pr; st.session_state.bet_history.append({"d": datetime.now().strftime("%m/%d"), "t": bd, "a": ba, "o": bo, "r": "W", "p": pr}); st.rerun()
    with w2:
        if st.button("❌ LOSS", key="ll2") and bd:
            st.session_state.bankroll -= ba; st.session_state.bet_history.append({"d": datetime.now().strftime("%m/%d"), "t": bd, "a": ba, "o": bo, "r": "L", "p": -ba}); st.rerun()
    if st.session_state.bet_history:
        st.markdown("---")
        st.dataframe(pd.DataFrame(st.session_state.bet_history).rename(columns={"d":"Date","t":"Bet","a":"Amt","o":"Odds","r":"Result","p":"P/L"}), use_container_width=True, hide_index=True)
        running = []; cur = st.session_state.bankroll - sum(b["p"] for b in st.session_state.bet_history)
        for b in st.session_state.bet_history: cur += b["p"]; running.append(cur)
        st.line_chart(pd.DataFrame({"Bankroll": running}), height=200)
        tp = sum(b["p"] for b in st.session_state.bet_history)
        st.success(f"📈 +${tp:.2f}") if tp > 0 else st.error(f"📉 -${abs(tp):.2f}")
        if st.button("🗑️ Clear", key="cl2"): st.session_state.bet_history = []; st.rerun()

st.markdown("---")
st.markdown("<center><small style='color:#444'>🟢 GreenEye Scout v3.0 — Find the Edge. Make the Play.</small></center>", unsafe_allow_html=True)