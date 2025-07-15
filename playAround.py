import sqlite3
import pandas as pd

def play_around():
    
    # Example: Reading from SQLite to Pandas
    connection = sqlite3.connect("fantasy.db")
    teams = pd.read_sql_query("SELECT * FROM teams", connection)
    matchups = pd.read_sql_query("SELECT * FROM matchups", connection)
    drafts = pd.read_sql_query("SELECT * FROM drafts", connection)

    owners = teams["lastName"].unique()

    records = []

    for team in owners:
        home_games = matchups[matchups["home_last_name"] == team]
        home_wins = (home_games["home_score"] > home_games["away_score"]).sum()
        home_losses = (home_games["home_score"] < home_games["away_score"]).sum()

        away_games = matchups[matchups["away_last_name"] == team]
        away_wins = (away_games["away_score"] > away_games["home_score"]).sum()
        away_losses = (away_games["away_score"] < away_games["home_score"]).sum()

        total_wins = home_wins + away_wins
        total_losses = home_losses + away_losses
        games_played = total_wins + total_losses
        win_pct = total_wins / games_played if games_played > 0 else 0

        records.append({
            "team": team,
            "wins": total_wins,
            "losses": total_losses,
            "win_pct": win_pct
        })

    df = pd.DataFrame(records)

    # Sort by win percentage descending
    df_sorted = df.sort_values(by="win_pct", ascending=False).reset_index(drop=True)

    # Add a rank column (starting at 1)
    df_sorted["rank"] = df_sorted.index + 1

    # Show ranked table
    print(df_sorted[["rank", "team", "wins", "losses", "win_pct"]])

    connection.close()

def main():
    play_around()

if __name__ == "__main__":
    main()
