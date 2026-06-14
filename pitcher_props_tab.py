import streamlit as st
from datetime import datetime, timedelta
import pandas as pd


def render_pitcher_props(teams, get_schedule, TEAM_NAME_MAP, PARK_FACTORS, find_pitcher, simulate_inning, get_headshot_cached, prob_to_ml, get_logo_url):

    st.markdown("### ⚾ Pitcher Props — Strikeout & Performance Projections")

    col1, col2 = st.columns(2)
    with col1:
        pk_date = st.radio("Date", ["Today", "Tomorrow"], horizontal=True, key="pk_date")
    with col2:
        pk_sims = st.select_slider("Simulations", options=[1000, 2500, 5000, 10000], value=5000, key="pk_sims")

    if st.button("⚾ Find Best Pitcher Props", type="primary", key="auto_pk"):
        if pk_date == "Today":
            pkdate = datetime.now().strftime('%m/%d/%Y')
        else:
            pkdate = (datetime.now() + timedelta(days=1)).strftime('%m/%d/%Y')

        games = get_schedule(pkdate)
        if not games:
            st.error("No games found")
            return

        progress = st.progress(0)
        pitcher_results = []

        for i, game in enumerate(games):
            away = TEAM_NAME_MAP.get(game["away"], game["away"])
            home = TEAM_NAME_MAP.get(game["home"], game["home"])
            if home not in teams or away not in teams:
                continue

            home_sp_obj = find_pitcher(game["home_pitcher"]) if game["home_pitcher"] != "TBD" else None
            away_sp_obj = find_pitcher(game["away_pitcher"]) if game["away_pitcher"] != "TBD" else None

            hd, ad = teams[home], teams[away]
            hp = home_sp_obj or hd["starter"]
            ap = away_sp_obj or ad["starter"]
            pf = PARK_FACTORS.get(home, 1.0)

            home_sp_ks = []
            away_sp_ks = []
            home_sp_runs = []
            away_sp_runs = []
            home_sp_wins = 0
            away_sp_wins = 0

            for sim in range(pk_sims):
                ai, hi = 0, 0
                hs_total, as_total = 0, 0
                sp_home_k, sp_away_k = 0, 0
                sp_home_runs, sp_away_runs = 0, 0

                for inn in range(1, 10):
                    a_stats_inn = {}
                    h_stats_inn = {}

                    if inn <= 6:
                        ar, ai, a_stats_inn = simulate_inning(ad["batters"], hp, ai, a_stats_inn, False, True, pf)
                        sp_home_k += sum(s["SO"] for s in a_stats_inn.values())
                        sp_home_runs += ar
                    else:
                        cur_hp = hd["bullpen"][0] if hd["bullpen"] else hp
                        ar, ai, a_stats_inn = simulate_inning(ad["batters"], cur_hp, ai, a_stats_inn, False, True, pf)

                    as_total += ar
                    if inn >= 9 and hs_total > as_total:
                        break

                    if inn <= 6:
                        hr_runs, hi, h_stats_inn = simulate_inning(hd["batters"], ap, hi, h_stats_inn, True, True, pf)
                        sp_away_k += sum(s["SO"] for s in h_stats_inn.values())
                        sp_away_runs += hr_runs
                    else:
                        cur_ap = ad["bullpen"][0] if ad["bullpen"] else ap
                        hr_runs, hi, h_stats_inn = simulate_inning(hd["batters"], cur_ap, hi, h_stats_inn, True, True, pf)

                    hs_total += hr_runs
                    if inn >= 9 and hs_total != as_total:
                        break

                home_sp_ks.append(sp_home_k)
                away_sp_ks.append(sp_away_k)
                home_sp_runs.append(sp_home_runs)
                away_sp_runs.append(sp_away_runs)
                if hs_total > as_total:
                    home_sp_wins += 1
                else:
                    away_sp_wins += 1

            for pitcher_data in [
                {"name": hp.name, "team": home, "era": hp.era, "throws": hp.throws,
                 "matchup": f"{away} @ {home}", "opp": away,
                 "ks": home_sp_ks, "runs": home_sp_runs, "wins": home_sp_wins},
                {"name": ap.name, "team": away, "era": ap.era, "throws": ap.throws,
                 "matchup": f"{away} @ {home}", "opp": home,
                 "ks": away_sp_ks, "runs": away_sp_runs, "wins": away_sp_wins},
            ]:
                ks = pitcher_data["ks"]
                runs = pitcher_data["runs"]
                pitcher_results.append({
                    "name": pitcher_data["name"],
                    "team": pitcher_data["team"],
                    "era": pitcher_data["era"],
                    "throws": pitcher_data["throws"],
                    "matchup": pitcher_data["matchup"],
                    "opp": pitcher_data["opp"],
                    "avg_k": sum(ks) / pk_sims,
                    "k4": sum(1 for k in ks if k >= 4) / pk_sims,
                    "k5": sum(1 for k in ks if k >= 5) / pk_sims,
                    "k6": sum(1 for k in ks if k >= 6) / pk_sims,
                    "k7": sum(1 for k in ks if k >= 7) / pk_sims,
                    "avg_runs": sum(runs) / pk_sims,
                    "under3": sum(1 for r in runs if r <= 2) / pk_sims,
                    "under4": sum(1 for r in runs if r <= 3) / pk_sims,
                    "qs": sum(1 for r in runs if r <= 3) / pk_sims,
                    "win_pct": pitcher_data["wins"] / pk_sims,
                })

            progress.progress((i + 1) / len(games))

        # STRIKEOUT PROPS
        st.markdown("---")
        st.markdown("### 🥴 Best Strikeout Props")
        st.markdown("*Pitchers most likely to rack up K's tonight (through 6 IP)*")

        k_sorted = sorted(pitcher_results, key=lambda x: x['avg_k'], reverse=True)

        for rank, p in enumerate(k_sorted[:12], 1):
            headshot = get_headshot_cached(p['name'])
            logo = get_logo_url(p['team'])
            fire = "🔥🔥🔥" if p['avg_k'] > 6 else "🔥🔥" if p['avg_k'] > 5 else "🔥" if p['avg_k'] > 4 else ""

            pc1, pc2, pc3, pc4, pc5 = st.columns([1, 3, 1, 1, 1])
            with pc1:
                if headshot:
                    st.image(headshot, width=55)
                else:
                    st.write(f"**#{rank}**")
            with pc2:
                st.markdown(f"**{p['name']}** ({p['throws']}) {fire}")
                st.caption(f"{p['matchup']} | ERA: {p['era']:.2f} | Avg K: {p['avg_k']:.1f}")
            with pc3:
                st.metric("5+ K's", f"{p['k5']*100:.0f}%")
            with pc4:
                st.metric("6+ K's", f"{p['k6']*100:.0f}%")
            with pc5:
                st.metric("7+ K's", f"{p['k7']*100:.0f}%")

        # QUALITY START / RUNS ALLOWED
        st.markdown("---")
        st.markdown("### 🛡️ Best Quality Start Props")
        st.markdown("*Pitchers most likely to allow 3 or fewer runs (through 6 IP)*")

        qs_sorted = sorted(pitcher_results, key=lambda x: x['qs'], reverse=True)

        for rank, p in enumerate(qs_sorted[:12], 1):
            headshot = get_headshot_cached(p['name'])
            fire = "🔥🔥🔥" if p['qs'] > 0.75 else "🔥🔥" if p['qs'] > 0.60 else "🔥" if p['qs'] > 0.50 else ""

            pc1, pc2, pc3, pc4, pc5 = st.columns([1, 3, 1, 1, 1])
            with pc1:
                if headshot:
                    st.image(headshot, width=55)
                else:
                    st.write(f"**#{rank}**")
            with pc2:
                st.markdown(f"**{p['name']}** ({p['throws']}) {fire}")
                st.caption(f"vs {p['opp']} | ERA: {p['era']:.2f} | Avg Runs: {p['avg_runs']:.1f}")
            with pc3:
                st.metric("QS %", f"{p['qs']*100:.0f}%")
            with pc4:
                st.metric("Under 3 ER", f"{p['under3']*100:.0f}%")
            with pc5:
                st.metric("Win %", f"{p['win_pct']*100:.0f}%")

        # ALL PITCHERS TABLE
        st.markdown("---")
        st.markdown("### 📊 All Pitchers Tonight")

        table_data = []
        for p in k_sorted:
            table_data.append({
                "Pitcher": p['name'],
                "Team": p['team'],
                "vs": p['opp'],
                "ERA": f"{p['era']:.2f}",
                "Avg K": f"{p['avg_k']:.1f}",
                "5+ K": f"{p['k5']*100:.0f}%",
                "6+ K": f"{p['k6']*100:.0f}%",
                "7+ K": f"{p['k7']*100:.0f}%",
                "Avg Runs": f"{p['avg_runs']:.1f}",
                "QS %": f"{p['qs']*100:.0f}%",
                "Win %": f"{p['win_pct']*100:.0f}%",
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.info("💡 Compare K props to your sportsbook. If sim says 65% chance of 5+ K's but the book has it at +110 (47.6%), that's a value bet.")