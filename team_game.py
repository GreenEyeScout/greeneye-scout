from auto_rosters import build_auto_rosters
from inning import simulate_inning
from pitcher import Pitcher
import random


def print_box_score(team_name, stats, score):
    print(f"\n{'─' * 55}")
    print(f"  {team_name} — {score} runs")
    print(f"{'─' * 55}")
    print(f"  {'PLAYER':<24} AB   H  2B  3B  HR RBI  SO  BB")
    print(f"  {'─' * 51}")

    for name, s in stats.items():
        print(f"  {name:<24}{s['AB']:3d} {s['H']:3d} {s['2B']:3d} {s['3B']:3d} {s['HR']:3d} {s['RBI']:3d} {s['SO']:3d} {s['BB']:3d}")

    totals = {k: sum(s[k] for s in stats.values()) for k in ["AB", "H", "2B", "3B", "HR", "RBI", "SO", "BB"]}
    print(f"  {'─' * 51}")
    print(f"  {'TOTALS':<24}{totals['AB']:3d} {totals['H']:3d} {totals['2B']:3d} {totals['3B']:3d} {totals['HR']:3d} {totals['RBI']:3d} {totals['SO']:3d} {totals['BB']:3d}")
    team_avg = f"{totals['H']/totals['AB']:.3f}" if totals['AB'] > 0 else ".000"
    print(f"  Team AVG: {team_avg}")


def simulate_game(home_batters, home_pitcher, home_bullpen, away_batters, away_pitcher, away_bullpen, home_name, away_name, quiet=False):
    home_score = 0
    away_score = 0
    away_stats = {}
    home_stats = {}
    away_lineup_idx = 0
    home_lineup_idx = 0

    current_home_pitcher = home_pitcher
    current_away_pitcher = away_pitcher
    home_pitcher_changed = False
    away_pitcher_changed = False

    if not quiet:
        print("\n" + "=" * 40)
        print(f"⚾ FIRST PITCH: {away_name} vs {home_name}")
        print(f"🏟️  {away_pitcher.name} vs {home_pitcher.name}")
        print("=" * 40)

    inning = 1
    max_innings = 9
    away_runs_by_inning = []
    home_runs_by_inning = []

    while True:
        if inning >= 7 and not home_pitcher_changed and home_bullpen:
            reliever = home_bullpen[0]
            if not quiet:
                print(f"\n🔄 PITCHING CHANGE: {current_home_pitcher.name} out, {reliever.name} in for {home_name}")
            current_home_pitcher = reliever
            home_pitcher_changed = True

        if inning >= 7 and not away_pitcher_changed and away_bullpen:
            reliever = away_bullpen[0]
            if not quiet:
                print(f"\n🔄 PITCHING CHANGE: {current_away_pitcher.name} out, {reliever.name} in for {away_name}")
            current_away_pitcher = reliever
            away_pitcher_changed = True

        if not quiet:
            print(f"\n🔵 TOP OF INNING {inning} — {away_name} batting")
        away_runs, away_lineup_idx, away_stats = simulate_inning(away_batters, current_home_pitcher, away_lineup_idx, away_stats, home_team=False)
        away_score += away_runs
        away_runs_by_inning.append(away_runs)

        if not quiet:
            print(f"\n🔴 BOTTOM OF INNING {inning} — {home_name} batting")
        home_runs, home_lineup_idx, home_stats = simulate_inning(home_batters, current_away_pitcher, home_lineup_idx, home_stats, home_team=True)
        home_score += home_runs
        home_runs_by_inning.append(home_runs)

        if not quiet:
            print(f"\n📊 SCORE AFTER {inning}: {away_name} {away_score} — {home_name} {home_score}")
            print("=" * 40)

        if inning >= max_innings and home_score != away_score:
            break
        elif inning >= max_innings and home_score == away_score:
            if not quiet:
                print("⚡ EXTRA INNINGS!")

        inning += 1

        if inning > 18:
            if not quiet:
                print("🛑 Game suspended after 18 innings!")
            break

    if not quiet:
        # Line score
        print("\n" + "=" * 55)
        print("📊 LINE SCORE")
        print("=" * 55)
        header = "  " + f"{'TEAM':<22}"
        for i in range(len(away_runs_by_inning)):
            header += f"{i+1:>3}"
        header += "   R   H"
        print(header)
        print("  " + "─" * (22 + len(away_runs_by_inning) * 3 + 8))

        away_line = "  " + f"{away_name:<22}"
        for r in away_runs_by_inning:
            away_line += f"{r:>3}"
        away_total_hits = sum(s['H'] for s in away_stats.values())
        away_line += f"  {away_score:>2}  {away_total_hits:>2}"
        print(away_line)

        home_line = "  " + f"{home_name:<22}"
        for r in home_runs_by_inning:
            home_line += f"{r:>3}"
        home_total_hits = sum(s['H'] for s in home_stats.values())
        home_line += f"  {home_score:>2}  {home_total_hits:>2}"
        print(home_line)

        # Pitching summary
        print(f"\n⚾ PITCHING:")
        print(f"  {away_name}: {away_pitcher.name} (1-6)", end="")
        if away_pitcher_changed and away_bullpen:
            print(f", {away_bullpen[0].name} (7-{inning})")
        else:
            print(f" — Complete game!")
        print(f"  {home_name}: {home_pitcher.name} (1-6)", end="")
        if home_pitcher_changed and home_bullpen:
            print(f", {home_bullpen[0].name} (7-{inning})")
        else:
            print(f" — Complete game!")

        # Final score
        print("\n🏆 FINAL SCORE:")
        print(f"  {away_name}: {away_score}")
        print(f"  {home_name}: {home_score}")

        if home_score > away_score:
            print(f"\n🎉 {home_name} WINS!")
        elif away_score > home_score:
            print(f"\n🎉 {away_name} WINS!")
        else:
            print("\n🤝 Game ended in a tie after 18 innings!")

        # Box scores
        print_box_score(away_name, away_stats, away_score)
        print_box_score(home_name, home_stats, home_score)

    return home_score, away_score


def show_menu(teams):
    team_list = sorted(teams.keys())

    while True:
        print("\n" + "=" * 40)
        print("⚾ MLB BASEBALL SIMULATOR ⚾")
        print("=" * 40)
        print("\nPick a matchup!\n")

        for i, name in enumerate(team_list, 1):
            starter = teams[name]["starter"].name
            bp_count = len(teams[name]["bullpen"])
            batters = len(teams[name]["batters"])
            print(f"  {i:2}. {name} ({starter}, {bp_count} relievers, {batters} batters)")

        print(f"\n  0. Quit")

        print("\n--- AWAY TEAM ---")
        while True:
            try:
                away_pick = int(input("Enter number for AWAY team: "))
                if away_pick == 0:
                    print("\nThanks for playing! ⚾")
                    return
                if 1 <= away_pick <= len(team_list):
                    break
                print("Invalid number, try again.")
            except ValueError:
                print("Please enter a number.")

        away_name = team_list[away_pick - 1]
        print(f"✅ Away: {away_name}")

        print("\n--- HOME TEAM ---")
        while True:
            try:
                home_pick = int(input("Enter number for HOME team: "))
                if home_pick == 0:
                    print("\nThanks for playing! ⚾")
                    return
                if 1 <= home_pick <= len(team_list):
                    if home_pick != away_pick:
                        break
                    print("Home team can't be the same as away team!")
                else:
                    print("Invalid number, try again.")
            except ValueError:
                print("Please enter a number.")

        home_name = team_list[home_pick - 1]
        print(f"✅ Home: {home_name}")

        away_data = teams[away_name]
        home_data = teams[home_name]

        print(f"\n📋 {away_name} LINEUP:")
        for i, p in enumerate(away_data["batters"], 1):
            print(f"  {i}. {p.name} (AVG: {p.batting_average:.3f})")
        print(f"  SP: {away_data['starter'].name} (ERA: {away_data['starter'].era:.2f})")
        for bp in away_data["bullpen"][:2]:
            print(f"  RP: {bp.name} (ERA: {bp.era:.2f})")

        print(f"\n📋 {home_name} LINEUP:")
        for i, p in enumerate(home_data["batters"], 1):
            print(f"  {i}. {p.name} (AVG: {p.batting_average:.3f})")
        print(f"  SP: {home_data['starter'].name} (ERA: {home_data['starter'].era:.2f})")
        for bp in home_data["bullpen"][:2]:
            print(f"  RP: {bp.name} (ERA: {bp.era:.2f})")

        print()
        confirm = input("Play this game? (y/n): ").strip().lower()
        if confirm != 'y':
            continue

        simulate_game(
            home_data["batters"], home_data["starter"], home_data["bullpen"],
            away_data["batters"], away_data["starter"], away_data["bullpen"],
            home_name, away_name
        )

        print()
        again = input("Simulate another game? (y/n): ").strip().lower()
        if again != 'y':
            print("\nThanks for playing! ⚾")
            return


teams = build_auto_rosters()
show_menu(teams)