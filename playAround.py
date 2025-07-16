import sqlite3
import pandas as pd

def play_around():

    results = {}
    
    # Example: Reading from SQLite to Pandas
    connection = sqlite3.connect("fantasy.db")
    teams = pd.read_sql_query("SELECT * FROM teams", connection)
    matchups = pd.read_sql_query("SELECT * FROM matchups", connection)
    drafts = pd.read_sql_query("SELECT * FROM drafts", connection)

    # Ensure is_playoffs is int or bool
    matchups["is_playoffs"] = matchups["is_playoffs"].astype(bool)

    """
    # 4 & 6. Career Stats including playoffs
    # Aggregate all games (including playoffs)
    all_games = []
    for season in matchups["season"].unique():
        season_games = matchups[matchups["season"] == season]
        teams_all = pd.concat([
            season_games[["home_last_name", "home_score", "away_score", "is_playoffs"]].rename(columns={"home_last_name": "team", "home_score": "team_score", "away_score": "opp_score"}),
            season_games[["away_last_name", "away_score", "home_score", "is_playoffs"]].rename(columns={"away_last_name": "team", "away_score": "team_score", "home_score": "opp_score"})
        ])
        teams_all["win"] = teams_all["team_score"] > teams_all["opp_score"]
        teams_all["season"] = season
        all_games.append(teams_all)
    all_games_df = pd.concat(all_games)

    career_stats = all_games_df.groupby("team").agg(
        total_games=pd.NamedAgg(column="win", aggfunc="count"),
        total_wins=pd.NamedAgg(column="win", aggfunc="sum"),
        playoff_games=pd.NamedAgg(column="is_playoffs", aggfunc="sum"),
        playoff_wins=pd.NamedAgg(column=lambda df: df[df["is_playoffs"]]["win"].sum(), aggfunc="sum")
    )
    career_stats["win_pct"] = career_stats["total_wins"] / career_stats["total_games"]
    career_stats["playoff_win_pct"] = career_stats["playoff_wins"] / career_stats["playoff_games"].replace(0, pd.NA)
    results["career_stats"] = career_stats.reset_index()

    # 7. Most points scored in a season by a team
    season_points = []
    for season in matchups["season"].unique():
        season_games = matchups[matchups["season"] == season]
        points = pd.concat([
            season_games[["home_last_name", "home_score"]].rename(columns={"home_last_name": "team", "home_score": "points"}),
            season_games[["away_last_name", "away_score"]].rename(columns={"away_last_name": "team", "away_score": "points"})
        ])
        total_points = points.groupby("team")["points"].sum().reset_index()
        total_points["season"] = season
        season_points.append(total_points)
    season_points_df = pd.concat(season_points)

    max_points_season = season_points_df.loc[season_points_df["points"].idxmax()]
    results["max_points_season"] = max_points_season

    # 8. Most points ever scored in a single week by a team
    weekly_points = pd.concat([
        matchups[["season", "matchup_week", "home_last_name", "home_score"]].rename(columns={"home_last_name": "team", "home_score": "points"}),
        matchups[["season", "matchup_week", "away_last_name", "away_score"]].rename(columns={"away_last_name": "team", "away_score": "points"})
    ])
    max_points_week = weekly_points.loc[weekly_points["points"].idxmax()]
    results["max_points_week"] = max_points_week

    print(results)

    """

    connection.close()

def main():
    play_around()

if __name__ == "__main__":
    main()
