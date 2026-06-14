import streamlit as st
from auto_rosters import build_auto_rosters, find_pitcher
from inning import simulate_inning
from pitcher import Pitcher
import random
import requests
import statsapi
from datetime import datetime, timedelta
import json

st.set_page_config(page_title="GreenEye Scout", page_icon="🟢", layout="wide")

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
    trl = []
    hrl, arl = 0, 0
    home_scores = []
    away_scores = []
    margins = []

    for _ in range(n):
        hs, as_ = sim_game(hd["batters"], hp, hd["bullpen"], ad["batters"], ap, ad["bullpen"], pf)
        t = hs + as_
        trl.append(t)
        thr += hs
        tar += as_
        home_scores.append(hs)
        away_scores.append(as_)
        margins.append(hs - as_)
        if hs > as_:
            hw += 1
            if hs - as_ >= 2: hrl += 1
        else:
            aw += 1
            if as_ - hs >= 2: arl += 1

    ou = {}
    for line in [5.5, 6.5, 7.5, 8.5, 9.5, 10.5]:
        ou[line] = sum(1 for t in trl if t > line) / n

    return {
        "home_pct": hw/n, "away_pct": aw/n,
        "avg_home": thr/n, "avg_away": tar/n,
        "avg_total": sum(trl)/n, "ou": ou,
        "home_rl": hrl/n, "away_rl": arl/n,
        "home_sp": hp.name, "away_sp": ap.name,
        "pf": pf, "home_throws": hp.throws, "away_throws": ap.throws,
        "total_runs_list": trl,
        "home_scores": home_scores,
        "away_scores": away_scores,
        "margins": margins,
    }


def prob_to_ml(prob):
    if prob <= 0 or prob >= 1: return "+100"
    if prob >= 0.5: return f"{-round((prob / (1 - prob)) * 100)}"
    else: return f"+{round(((1 - prob) / prob) * 100)}"


def ml_to_prob(ml):
    if ml < 0: return abs(ml) / (abs(ml) + 100)
    else: return 100 / (ml + 100)


@st.cache_data(ttl=3600, show_spinner="Loading 2026 MLB data...")
def load_teams():
    return build_auto_rosters()


@st.cache_data(ttl=300)
def get_schedule(date):
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


# Initialize session state for bankroll
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "bet_history" not in st.session_state:
    st.session_state.bet_history = []

teams = load_teams()

# Header
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: #2ecc71; margin-bottom: 0;'>🟢 GreenEye Scout</h1>
    <p style='color: #888; font-size: 1.1rem;'>MLB Prediction Engine — Monte Carlo Simulation</p>
    <p style='color: #666; font-size: 0.85rem;'>Real 2026 stats • Park factors • L/R splits • Injury detection • 10,000 simulations</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📅 Today/Tomorrow", "🎯 Custom Matchup", "🎰 Parlay Calculator", "💰 Bankroll Tracker"])

# ============ TAB 1: TODAY/TOMORROW ============
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        date_option = st.radio("Date", ["Today", "Tomorrow"])
    with col2:
        num_sims = st.select_slider("Simulations per game",
            options=[1000, 2500, 5000, 10000, 25000, 50000], value=10000)

    if st.button("🟢 Run GreenEye Scout", type="primary"):
        if date_option == "Today":
            date = datetime.now().strftime('%m/%d/%Y')
        else:
            date = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')

        games = get_schedule(date)

        if not games:
            st.error("No games found for this date")
        else:
            st.success(f"Found {len(games)} games — running {num_sims} simulations each...")
            progress = st.progress(0)
            all_results = []

            for i, game in enumerate(games):
                away = TEAM_NAME_MAP.get(game["away"], game["away"])
                home = TEAM_NAME_MAP.get(game["home"], game["home"])
                if home not in teams or away not in teams:
                    continue
                home_sp = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
                away_sp = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None
                result = run_sim_detailed(teams, home, away, num_sims, home_sp, away_sp)
                all_results.append((away, home, game, result))
                progress.progress((i + 1) / len(games))

            st.markdown("---")

            for away, home, game, result in all_results:
                pf = result['pf']
                bp_name = BALLPARK_NAMES.get(home, "")

                with st.container():
                    st.markdown(f"### ⚾ {away} @ {home}")
                    st.caption(f"📍 {bp_name} (PF: {pf:.2f}) | SP: {result['away_sp']} ({result['away_throws']}) vs {result['home_sp']} ({result['home_throws']})")

                    c1, c2, c3, c4 = st.columns(4)
                    away_pct = result['away_pct'] * 100
                    home_pct = result['home_pct'] * 100
                    away_ml = prob_to_ml(result['away_pct'])
                    home_ml = prob_to_ml(result['home_pct'])
                    c1.metric(f"{away}", f"{away_pct:.1f}%", f"ML: {away_ml}")
                    c2.metric(f"{home}", f"{home_pct:.1f}%", f"ML: {home_ml}")
                    c3.metric("Predicted Score", f"{result['avg_away']:.1f} - {result['avg_home']:.1f}")
                    c4.metric("Avg Total Runs", f"{result['avg_total']:.1f}")

                    with st.expander("📊 Charts & Detailed Breakdown"):
                        ch1, ch2 = st.columns(2)

                        with ch1:
                            st.markdown("**Total Runs Distribution**")
                            import pandas as pd
                            runs_df = pd.DataFrame({"Total Runs": result["total_runs_list"]})
                            hist_data = runs_df["Total Runs"].value_counts().sort_index()
                            st.bar_chart(hist_data, height=200)

                        with ch2:
                            st.markdown("**Win Margin Distribution**")
                            margin_df = pd.DataFrame({"Margin": result["margins"]})
                            margin_counts = margin_df["Margin"].value_counts().sort_index()
                            st.bar_chart(margin_counts, height=200)

                        det1, det2, det3 = st.columns(3)
                        with det1:
                            st.markdown("**Moneyline**")
                            st.write(f"{away}: {away_pct:.1f}% ({away_ml})")
                            st.write(f"{home}: {home_pct:.1f}% ({home_ml})")
                        with det2:
                            st.markdown("**Run Line (-1.5)**")
                            st.write(f"{away}: {result['away_rl']*100:.1f}%")
                            st.write(f"{home}: {result['home_rl']*100:.1f}%")
                        with det3:
                            st.markdown("**Over/Under**")
                            for line in [6.5, 7.5, 8.5, 9.5]:
                                ov = result['ou'][line] * 100
                                st.write(f"O/U {line}: Over {ov:.1f}%")

                    st.markdown("---")

            # Summary
            st.markdown("### 🟢 GreenEye Scout Summary")
            summary_data = []
            for away, home, game, result in all_results:
                fav = home if result['home_pct'] > result['away_pct'] else away
                fav_pct = max(result['home_pct'], result['away_pct']) * 100
                summary_data.append({
                    "Matchup": f"{away} @ {home}",
                    "Favorite": fav,
                    "Win %": f"{fav_pct:.1f}%",
                    "ML": prob_to_ml(max(result['home_pct'], result['away_pct'])),
                    "Score": f"{result['avg_away']:.1f} - {result['avg_home']:.1f}",
                    "Total": f"{result['avg_total']:.1f}",
                })
            st.table(summary_data)

# ============ TAB 2: CUSTOM MATCHUP ============
with tab2:
    team_list = sorted(teams.keys())
    col1, col2 = st.columns(2)
    with col1:
        away_team = st.selectbox("Away Team", team_list,
            index=team_list.index("New York Yankees") if "New York Yankees" in team_list else 0)
    with col2:
        home_team = st.selectbox("Home Team", team_list,
            index=team_list.index("Los Angeles Dodgers") if "Los Angeles Dodgers" in team_list else 1)

    custom_sims = st.select_slider("Simulations",
        options=[1000, 2500, 5000, 10000, 25000, 50000], value=10000, key="custom_sims")

    if st.button("🟢 Scout This Matchup", type="primary", key="custom_btn"):
        if away_team == home_team:
            st.error("Pick two different teams!")
        else:
            with st.spinner(f"Running {custom_sims} simulations..."):
                result = run_sim_detailed(teams, home_team, away_team, custom_sims)

            bp_name = BALLPARK_NAMES.get(home_team, "")
            st.markdown(f"### ⚾ {away_team} @ {home_team}")
            st.caption(f"📍 {bp_name} (PF: {result['pf']:.2f}) | SP: {result['away_sp']} ({result['away_throws']}) vs {result['home_sp']} ({result['home_throws']})")

            c1, c2, c3 = st.columns(3)
            away_ml = prob_to_ml(result['away_pct'])
            home_ml = prob_to_ml(result['home_pct'])
            c1.metric(away_team, f"{result['away_pct']*100:.1f}%", f"ML: {away_ml}")
            c2.metric(home_team, f"{result['home_pct']*100:.1f}%", f"ML: {home_ml}")
            c3.metric("Predicted Score", f"{result['avg_away']:.1f} - {result['avg_home']:.1f}")

            st.markdown("---")

            # Charts
            import pandas as pd
            ch1, ch2 = st.columns(2)
            with ch1:
                st.markdown("**Total Runs Distribution**")
                runs_df = pd.DataFrame({"Total Runs": result["total_runs_list"]})
                hist_data = runs_df["Total Runs"].value_counts().sort_index()
                st.bar_chart(hist_data, height=250)
            with ch2:
                st.markdown("**Win Margin Distribution**")
                margin_df = pd.DataFrame({"Margin": result["margins"]})
                margin_counts = margin_df["Margin"].value_counts().sort_index()
                st.bar_chart(margin_counts, height=250)

            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**Run Line (-1.5)**")
                st.write(f"{away_team}: {result['away_rl']*100:.1f}%")
                st.write(f"{home_team}: {result['home_rl']*100:.1f}%")
            with d2:
                st.markdown("**Over/Under**")
                for line in [6.5, 7.5, 8.5, 9.5]:
                    ov = result['ou'][line] * 100
                    st.write(f"O/U {line}: Over {ov:.1f}% | Under {100-ov:.1f}%")
            with d3:
                st.markdown("**Game Info**")
                st.write(f"Park Factor: {result['pf']:.2f}")
                st.write(f"Avg Total Runs: {result['avg_total']:.1f}")

            st.markdown("---")
            l1, l2 = st.columns(2)
            with l1:
                st.markdown(f"**{away_team} Lineup**")
                for j, p in enumerate(teams[away_team]["batters"], 1):
                    st.write(f"{j}. {p.name} (.{int(p.batting_average*1000):03d}, {p.bats})")
            with l2:
                st.markdown(f"**{home_team} Lineup**")
                for j, p in enumerate(teams[home_team]["batters"], 1):
                    st.write(f"{j}. {p.name} (.{int(p.batting_average*1000):03d}, {p.bats})")

# ============ TAB 3: PARLAY CALCULATOR ============
with tab3:
    st.markdown("### 🎰 Parlay Calculator")
    st.markdown("*Add multiple bets to see combined odds and potential payout*")

    num_legs = st.number_input("How many legs in your parlay?", min_value=2, max_value=10, value=2)

    legs = []
    combined_prob = 1.0

    for i in range(int(num_legs)):
        st.markdown(f"**Leg {i+1}**")
        c1, c2 = st.columns(2)
        with c1:
            team = st.text_input(f"Team/Pick", key=f"parlay_team_{i}", placeholder="e.g. Yankees ML")
        with c2:
            odds = st.number_input(f"American Odds", key=f"parlay_odds_{i}", value=-110, step=5)

        if odds != 0:
            prob = ml_to_prob(odds)
            combined_prob *= prob
            legs.append({"team": team, "odds": odds, "prob": prob})

    if st.button("🎰 Calculate Parlay", type="primary", key="parlay_calc"):
        if len(legs) >= 2:
            st.markdown("---")
            st.markdown("### Parlay Breakdown")

            for i, leg in enumerate(legs):
                st.write(f"**Leg {i+1}:** {leg['team']} ({leg['odds']:+d}) — {leg['prob']*100:.1f}% implied probability")

            combined_ml = prob_to_ml(combined_prob)
            st.markdown("---")

            r1, r2, r3 = st.columns(3)
            r1.metric("Combined Probability", f"{combined_prob*100:.1f}%")
            r2.metric("Parlay Odds", combined_ml)

            # Calculate payout
            wager = st.number_input("Wager Amount ($)", min_value=1.0, value=100.0, step=10.0, key="parlay_wager")
            if combined_prob > 0:
                payout = wager / combined_prob
                profit = payout - wager
                r3.metric("Potential Payout", f"${payout:.2f}", f"+${profit:.2f} profit")

            if combined_prob < 0.1:
                st.warning("⚠️ This parlay has less than 10% chance of hitting. High risk!")
            elif combined_prob < 0.25:
                st.info("🎲 Moderate risk parlay — proceed with caution")
            else:
                st.success("✅ Reasonable parlay with decent probability")

# ============ TAB 4: BANKROLL TRACKER ============
with tab4:
    st.markdown("### 💰 Bankroll Tracker")

    b1, b2 = st.columns(2)
    with b1:
        st.metric("Current Bankroll", f"${st.session_state.bankroll:.2f}")
    with b2:
        total_bets = len(st.session_state.bet_history)
        wins = sum(1 for b in st.session_state.bet_history if b["result"] == "Win")
        losses = total_bets - wins
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        st.metric("Record", f"{wins}W - {losses}L ({win_rate:.0f}%)")

    st.markdown("---")

    st.markdown("**Set Starting Bankroll**")
    new_bankroll = st.number_input("Starting Bankroll ($)", min_value=0.0, value=st.session_state.bankroll, step=50.0, key="set_bankroll")
    if st.button("Set Bankroll", key="set_br_btn"):
        st.session_state.bankroll = new_bankroll
        st.success(f"Bankroll set to ${new_bankroll:.2f}")
        st.rerun()

    st.markdown("---")
    st.markdown("**Log a Bet**")

    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        bet_team = st.text_input("Bet Description", placeholder="e.g. Yankees ML", key="bet_desc")
    with lc2:
        bet_amount = st.number_input("Bet Amount ($)", min_value=1.0, value=50.0, step=10.0, key="bet_amt")
    with lc3:
        bet_odds = st.number_input("Odds", value=-110, step=5, key="bet_odds_input")

    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("✅ Log as WIN", type="primary", key="log_win"):
            if bet_team:
                if bet_odds < 0:
                    profit = bet_amount * (100 / abs(bet_odds))
                else:
                    profit = bet_amount * (bet_odds / 100)
                st.session_state.bankroll += profit
                st.session_state.bet_history.append({
                    "team": bet_team, "amount": bet_amount,
                    "odds": bet_odds, "result": "Win",
                    "profit": profit,
                    "date": datetime.now().strftime("%m/%d %I:%M%p")
                })
                st.success(f"WIN! +${profit:.2f}")
                st.rerun()
    with rc2:
        if st.button("❌ Log as LOSS", key="log_loss"):
            if bet_team:
                st.session_state.bankroll -= bet_amount
                st.session_state.bet_history.append({
                    "team": bet_team, "amount": bet_amount,
                    "odds": bet_odds, "result": "Loss",
                    "profit": -bet_amount,
                    "date": datetime.now().strftime("%m/%d %I:%M%p")
                })
                st.error(f"LOSS -${bet_amount:.2f}")
                st.rerun()

    if st.session_state.bet_history:
        st.markdown("---")
        st.markdown("**Bet History**")

        import pandas as pd
        hist_df = pd.DataFrame(st.session_state.bet_history)
        hist_df = hist_df[["date", "team", "amount", "odds", "result", "profit"]]
        hist_df.columns = ["Date", "Bet", "Amount", "Odds", "Result", "Profit"]
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

        # Profit chart
        st.markdown("**Bankroll Over Time**")
        running_total = []
        current = st.session_state.bankroll - sum(b["profit"] for b in st.session_state.bet_history)
        for bet in st.session_state.bet_history:
            current += bet["profit"]
            running_total.append(current)
        chart_df = pd.DataFrame({"Bankroll": running_total})
        st.line_chart(chart_df, height=250)

        total_profit = sum(b["profit"] for b in st.session_state.bet_history)
        if total_profit > 0:
            st.success(f"📈 Total Profit: +${total_profit:.2f}")
        else:
            st.error(f"📉 Total Loss: -${abs(total_profit):.2f}")

        if st.button("🗑️ Clear All History", key="clear_hist"):
            st.session_state.bet_history = []
            st.rerun()

st.markdown("---")
st.markdown("<center><small>🟢 GreenEye Scout — Built from scratch, powered by Monte Carlo simulation</small></center>", unsafe_allow_html=True)