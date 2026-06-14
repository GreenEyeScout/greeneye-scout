import json
import os
import statsapi
from datetime import datetime, timedelta

PREDICTIONS_FILE = "predictions_log.json"

def load_predictions():
    if os.path.exists(PREDICTIONS_FILE):
        try:
            with open(PREDICTIONS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_prediction(pred):
    preds = load_predictions()
    preds.append(pred)
    with open(PREDICTIONS_FILE, "w") as f:
        json.dump(preds, f)

def save_all_predictions(new_preds):
    existing = load_predictions()
    existing.extend(new_preds)
    with open(PREDICTIONS_FILE, "w") as f:
        json.dump(existing, f)

def get_results_for_date(date_str):
    try:
        sched = statsapi.schedule(date=date_str)
        results = {}
        for g in sched:
            if "Final" in g.get("status", ""):
                key = f"{g['away_name']}@{g['home_name']}"
                results[key] = {
                    "away": g["away_name"],
                    "home": g["home_name"],
                    "away_score": g.get("away_score", 0),
                    "home_score": g.get("home_score", 0),
                    "winner": g["home_name"] if g.get("home_score", 0) > g.get("away_score", 0) else g["away_name"],
                }
        return results
    except:
        return {}

def grade_predictions():
    preds = load_predictions()
    if not preds:
        return {"total": 0, "wins": 0, "losses": 0, "pending": 0, "graded": [], "roi": 0}
    graded = []
    wins = 0
    losses = 0
    pending = 0
    total_wagered = 0
    total_returned = 0
    dates_checked = {}
    for pred in preds:
        date = pred.get("date", "")
        if not date:
            continue
        if date not in dates_checked:
            dates_checked[date] = get_results_for_date(date)
        results = dates_checked[date]
        key = f"{pred.get('away', '')}@{pred.get('home', '')}"
        if key in results:
            actual_winner = results[key]["winner"]
            pick = pred.get("pick", "")
            won = pick == actual_winner
            actual_score = f"{results[key]['away_score']}-{results[key]['home_score']}"
            if won:
                wins += 1
                ml = pred.get("ml", -110)
                if ml and ml < 0:
                    profit = 100 * (100 / abs(ml))
                elif ml and ml > 0:
                    profit = 100 * (ml / 100)
                else:
                    profit = 100
                total_wagered += 100
                total_returned += 100 + profit
            else:
                losses += 1
                total_wagered += 100
            graded.append({
                "date": date,
                "matchup": f"{pred.get('away', '')} @ {pred.get('home', '')}",
                "pick": pick,
                "edge": pred.get("edge", 0),
                "ml": pred.get("ml", None),
                "result": "✅ WIN" if won else "❌ LOSS",
                "actual_score": actual_score,
                "actual_winner": actual_winner,
            })
        else:
            pending += 1
    roi = ((total_returned - total_wagered) / total_wagered * 100) if total_wagered > 0 else 0
    return {"total": wins + losses, "wins": wins, "losses": losses, "pending": pending, "graded": graded, "roi": roi}

def get_record_by_tier():
    preds = load_predictions()
    results_cache = {}
    tiers = {
        "top": {"label": "🔥 Top Plays (5%+ edge)", "wins": 0, "losses": 0},
        "mid": {"label": "⚡ Lean Plays (2-5% edge)", "wins": 0, "losses": 0},
        "small": {"label": "📊 Small Edge (0-2%)", "wins": 0, "losses": 0},
    }
    for pred in preds:
        date = pred.get("date", "")
        if date not in results_cache:
            results_cache[date] = get_results_for_date(date)
        results = results_cache[date]
        key = f"{pred.get('away', '')}@{pred.get('home', '')}"
        if key in results:
            won = pred.get("pick", "") == results[key]["winner"]
            edge = pred.get("edge", 0)
            tier = "top" if edge >= 5 else "mid" if edge >= 2 else "small"
            if won:
                tiers[tier]["wins"] += 1
            else:
                tiers[tier]["losses"] += 1
    return tiers

def clear_predictions():
    with open(PREDICTIONS_FILE, "w") as f:
        json.dump([], f)
