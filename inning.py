import random
from player import Player


def get_platoon_modifier(batter_bats, pitcher_throws):
    if batter_bats == "S":
        return 1.04

    if batter_bats != pitcher_throws:
        return 1.08
    else:
        return 0.92


def simulate_inning(lineup, pitcher, lineup_index=0, stats=None, home_team=False, quiet=False, park_factor=1.0):
    outs = 0
    runs = 0
    bases = [False, False, False]

    if stats is None:
        stats = {}

    if not quiet:
        print(f"⚾ Inning starting... ({pitcher.name} pitching, Throws: {pitcher.throws})")
        print("---")

    while outs < 3:
        batter = lineup[lineup_index % len(lineup)]
        lineup_index += 1

        if batter.name not in stats:
            stats[batter.name] = {"AB": 0, "H": 0, "HR": 0, "RBI": 0, "SO": 0, "BB": 0, "2B": 0, "3B": 0}

        raw_difficulty = pitcher.era / 4.50
        pitcher_difficulty = 1.0 + (raw_difficulty - 1.0) * 0.3
        pitcher_difficulty = max(0.75, min(1.25, pitcher_difficulty))

        home_boost = 1.04 if home_team else 0.96
        platoon = get_platoon_modifier(batter.bats, pitcher.throws)

        adjusted_avg = batter.batting_average * pitcher_difficulty * home_boost * park_factor * platoon
        adjusted_hr = batter.home_run_rate * pitcher_difficulty * home_boost * (park_factor ** 1.5) * platoon
        adjusted_so = min(batter.strikeout_rate + pitcher.strikeout_rate / 10, 0.45)
        if batter.bats == pitcher.throws:
            adjusted_so *= 1.05
        walk_chance = pitcher.walk_rate / 10

        roll = random.random()

        if roll < walk_chance:
            stats[batter.name]["BB"] += 1
            if bases[0] and bases[1] and bases[2]:
                runs += 1
                stats[batter.name]["RBI"] += 1
                if not quiet:
                    print(f"🚶 {batter.name} walks! A run is forced in!")
            elif bases[0] and bases[1]:
                bases[2] = True
                if not quiet:
                    print(f"🚶 {batter.name} draws a walk! Bases loaded!")
            elif bases[0]:
                bases[1] = True
                if not quiet:
                    print(f"🚶 {batter.name} draws a walk!")
            else:
                bases[0] = True
                if not quiet:
                    print(f"🚶 {batter.name} draws a walk!")

        elif roll < walk_chance + adjusted_hr:
            stats[batter.name]["AB"] += 1
            stats[batter.name]["H"] += 1
            stats[batter.name]["HR"] += 1
            runners_scoring = sum(bases) + 1
            stats[batter.name]["RBI"] += runners_scoring
            runs += runners_scoring
            bases = [False, False, False]
            if not quiet:
                if runners_scoring == 4:
                    print(f"💥 {batter.name} hits a GRAND SLAM! {runners_scoring} runs score!")
                elif runners_scoring > 1:
                    print(f"💥 {batter.name} hits a HOME RUN! {runners_scoring} run(s) score!")
                else:
                    print(f"💥 {batter.name} hits a SOLO HOME RUN!")

        elif roll < walk_chance + adjusted_avg:
            stats[batter.name]["AB"] += 1
            stats[batter.name]["H"] += 1
            hit_roll = random.random()

            if hit_roll < 0.05:
                new_runs = sum(bases)
                stats[batter.name]["RBI"] += new_runs
                stats[batter.name]["3B"] += 1
                runs += new_runs
                bases = [False, False, True]
                if not quiet:
                    if new_runs > 0:
                        print(f"🔥 {batter.name} triples! {new_runs} run(s) score!")
                    else:
                        print(f"🔥 {batter.name} hits a triple!")

            elif hit_roll < 0.25:
                new_runs = 0
                if bases[2]:
                    new_runs += 1
                if bases[1]:
                    new_runs += 1
                if bases[0]:
                    bases[2] = True
                else:
                    bases[2] = False
                bases[1] = True
                bases[0] = False
                stats[batter.name]["RBI"] += new_runs
                stats[batter.name]["2B"] += 1
                runs += new_runs
                if not quiet:
                    if new_runs > 0:
                        print(f"✌️  {batter.name} doubles! {new_runs} run(s) score!")
                    else:
                        print(f"✌️  {batter.name} hits a double!")

            else:
                new_runs = 0
                if bases[2]:
                    new_runs += 1
                bases[2] = bases[1]
                bases[1] = bases[0]
                bases[0] = True
                stats[batter.name]["RBI"] += new_runs
                runs += new_runs
                if not quiet:
                    if new_runs > 0:
                        print(f"⚾ {batter.name} singles! {new_runs} run(s) score!")
                    else:
                        print(f"⚾ {batter.name} singles! Runners advance.")

        elif roll < walk_chance + adjusted_avg + adjusted_so:
            stats[batter.name]["AB"] += 1
            stats[batter.name]["SO"] += 1
            outs += 1
            if not quiet:
                print(f"🥴 {batter.name} strikes out. {outs} out(s).")

        else:
            stats[batter.name]["AB"] += 1
            outs += 1
            if not quiet:
                print(f"🎯 {batter.name} is out. {outs} out(s).")

    if not quiet:
        print("---")
        print(f"✅ Inning over! Runs scored: {runs}")
    return runs, lineup_index, stats