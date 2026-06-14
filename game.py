import random
from player import Player
from inning import simulate_inning

def simulate_game(home_team, away_team, home_name, away_name):
    home_score = 0
    away_score = 0

    print("=" * 40)
    print(f"⚾ FIRST PITCH: {away_name} vs {home_name}")
    print("=" * 40)

    for inning in range(1, 10):
        print(f"\n🔵 TOP OF INNING {inning} — {away_name} batting")
        away_runs = simulate_inning(away_team)
        away_score += away_runs

        print(f"\n🔴 BOTTOM OF INNING {inning} — {home_name} batting")
        home_runs = simulate_inning(home_team)
        home_score += home_runs

        print(f"\n📊 SCORE AFTER {inning}: {away_name} {away_score} — {home_name} {home_score}")
        print("=" * 40)

    print("\n🏆 FINAL SCORE:")
    print(f"{away_name}: {away_score}")
    print(f"{home_name}: {home_score}")

    if home_score > away_score:
        print(f"\n🎉 {home_name} WINS!")
    elif away_score > home_score:
        print(f"\n🎉 {away_name} WINS!")
    else:
        print("\n🤝 It's a tie!")


# BUILD THE NEW YORK YANKEES
judge =    Player("Aaron Judge",    0.322, 0.085, 0.248)
stanton =  Player("Giancarlo Stanton", 0.241, 0.072, 0.310)
rizzo =    Player("Anthony Rizzo",  0.224, 0.038, 0.195)
torres =   Player("Gleyber Torres", 0.257, 0.041, 0.198)
volpe =    Player("Anthony Volpe",  0.243, 0.033, 0.221)

yankees = [judge, stanton, rizzo, torres, volpe]

# BUILD THE LOS ANGELES DODGERS
ohtani =   Player("Shohei Ohtani",  0.310, 0.078, 0.231)
betts =    Player("Mookie Betts",   0.289, 0.055, 0.134)
freeman =  Player("Freddie Freeman",0.301, 0.048, 0.142)
muncy =    Player("Max Muncy",      0.212, 0.058, 0.271)
hernandez= Player("Teoscar Hernandez", 0.272, 0.061, 0.248)

dodgers = [ohtani, betts, freeman, muncy, hernandez]

# PLAY BALL!
simulate_game(
    home_team=dodgers,
    away_team=yankees,
    home_name="Los Angeles Dodgers",
    away_name="New York Yankees"
)