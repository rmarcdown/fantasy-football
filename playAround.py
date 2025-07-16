import sqlite3
import pandas as pd

def play_around():

    results = {}
        

    # Connect to your fantasy database
    connection = sqlite3.connect("fantasy.db")
    teams = pd.read_sql_query("SELECT * FROM teams", connection)
    matchups = pd.read_sql_query("SELECT * FROM matchups", connection)
    drafts = pd.read_sql_query("SELECT * FROM drafts", connection)

    player_weeks = pd.concat([
        matchups[["season", "home_last_name", "home_score", "home_proj_score"]].rename(
            columns={"home_last_name": "team", "home_score": "actual", "home_proj_score": "projected"}
        ),
        matchups[["season", "away_last_name", "away_score", "away_proj_score"]].rename(
            columns={"away_last_name": "team", "away_score": "actual", "away_proj_score": "projected"}
        )
    ])

    # Compute over/under per week
    player_weeks["over_under"] = player_weeks["actual"] - player_weeks["projected"]

    # Aggregate per team (owner) per season
    seasonal_over_under = (
        player_weeks.groupby(["season", "team"])["over_under"]
        .sum()
        .reset_index()
        .sort_values(by=["season", "over_under"], ascending=[True, False])
    )

    # Optional: Round for clean output
    seasonal_over_under["over_under"] = seasonal_over_under["over_under"].round(2)

    # Example output
    print(seasonal_over_under)


    connection.close()

def main():
    play_around()

if __name__ == "__main__":
    main()
