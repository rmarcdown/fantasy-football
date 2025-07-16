import streamlit as st
import sqlite3
import pandas as pd
import altair as alt
import streamlit as st
import pdb

# Set page config
st.set_page_config(page_title="Fantasy Win/Loss Dashboard", layout="centered")


@st.cache_data
def load_data():
    """Load SQLite data once and cache it."""
    connection = sqlite3.connect("fantasy.db")
    teams = pd.read_sql_query("SELECT * FROM teams", connection)
    matchups = pd.read_sql_query("SELECT * FROM matchups", connection)
    drafts = pd.read_sql_query("SELECT * FROM drafts", connection)
    connection.close()
    return teams, matchups, drafts


def league_history_stats(teams, matchups):
    """Compute Historical League Stats."""
    results = {}
    # 1. Past Champions: find playoff finals winners by season
    champions = [{"season": 2020, "champion": "BRANITZKY"}]
    for season in matchups["season"].unique():
        playoffs = matchups[(matchups["season"] == season) & (matchups["game_type"] == "playoff")]
        if playoffs.empty:
            continue
        max_week = playoffs["matchup_week"].max()
        final_game = playoffs[(playoffs["season"] == season) & (playoffs["matchup_week"] == max_week)]

        # Take only the first final game (should be just one)
        game = final_game.iloc[0]

        if game["home_score"] > game["away_score"]:
            winner = game["home_last_name"]
        else:
            winner = game["away_last_name"]

        champions.append({"season": season, "champion": winner})

    results["champions"] = pd.DataFrame(champions)

    # 2. Regular season #1 seed (best record)
    regular_season = matchups[matchups["game_type"] == "regular"]
    # Compute win/loss per team per season
    team_records = []
    for season in regular_season["season"].unique():
        season_games = regular_season[regular_season["season"] == season]
        teams_pd = pd.concat([
            season_games[["home_last_name", "home_score", "away_score"]].rename(columns={"home_last_name": "team", "home_score": "team_score", "away_score": "opp_score"}),
            season_games[["away_last_name", "away_score", "home_score"]].rename(columns={"away_last_name": "team", "away_score": "team_score", "home_score": "opp_score"})
        ])
        # Calculate wins/losses
        teams_pd["win"] = teams_pd["team_score"] > teams_pd["opp_score"]
        wins = teams_pd.groupby("team")["win"].sum()
        total_games = teams_pd.groupby("team")["win"].count()
        win_pct = wins / total_games
        record = [f"{w} - {l}" for w, l in zip(wins.values, (total_games.values - wins.values))]
        df = pd.DataFrame({"season": season, "team": wins.index, "wins": wins.values, "games": total_games.values, "record": record, "win_pct": win_pct.values})
        team_records.append(df)
    team_records_df = pd.concat(team_records)

    max_win_pct_per_season = team_records_df.groupby("season")["win_pct"].max().reset_index()
    one_seeds = pd.merge(team_records_df, max_win_pct_per_season, on=["season", "win_pct"], how="inner")
    one_seeds = one_seeds.sort_values(by=["season", "team"]).drop_duplicates(subset=["season"])
    results["one_seeds"] = one_seeds[["season", "team", "record", "win_pct"]].reset_index(drop=True)

    # 3. Sacko (last place)
    min_win_pct_per_season = team_records_df.groupby("season")["win_pct"].min().reset_index()
    sackos = pd.merge(team_records_df, min_win_pct_per_season, on=["season", "win_pct"], how="inner")
    sackos = sackos.sort_values(by=["season", "team"]).drop_duplicates(subset=["season"])
    results["sackos"] = sackos[["season", "team", "record", "win_pct"]].reset_index(drop=True)

    #4. All Time Win %
    owners = teams["lastName"].unique()
    records = []

    for team in owners:
        home_games = matchups[(matchups["home_last_name"] == team) & (matchups["game_type"].isin(["playoff", "regular"]))]
        home_wins = (home_games["home_score"] > home_games["away_score"]).sum()
        home_losses = (home_games["home_score"] < home_games["away_score"]).sum()

        away_games = matchups[(matchups["away_last_name"] == team) & (matchups["game_type"].isin(["playoff", "regular"]))]
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
            "win_pct": round(win_pct, 3),
        })

    results["overall_win_loss"] = (
        pd.DataFrame(records)
        .sort_values(by="win_pct", ascending=False)
        .reset_index(drop=True)
    )

    #5. Yearly Scoring Title
    season_points = []
    for season in matchups["season"].unique():
        season_games = matchups[(matchups["season"] == season) & (matchups["game_type"].isin(["playoff", "regular"]))]

        points = pd.concat([
            season_games[["home_last_name", "home_score"]].rename(columns={
                "home_last_name": "team", "home_score": "points"
            }),
            season_games[["away_last_name", "away_score"]].rename(columns={
                "away_last_name": "team", "away_score": "points"
            })
        ])
        total_points = points.groupby("team")["points"].sum().reset_index()
        total_points["season"] = season
        season_points.append(total_points)

    season_points_df = pd.concat(season_points, ignore_index=True)
    top_scorers_per_season = (
        season_points_df.loc[
            season_points_df.groupby("season")["points"].idxmax()
        ]
        .sort_values("season")
        .reset_index(drop=True)
    )
    results["season_points_all"] = season_points_df
    results["max_points_season_per_year"] = top_scorers_per_season

    #6. Most Points Ever in a Season
    top_scorer_overall = season_points_df.loc[
        season_points_df["points"].idxmax()
    ]
    results["max_points_season_overall"] = top_scorer_overall

    #7. Most points ever scored in a single week by a team
    weekly_points = pd.concat([
    matchups[["season", "matchup_week", "home_last_name", "home_score"]].rename(
        columns={"home_last_name": "team", "home_score": "points"}
    ),
    matchups[["season", "matchup_week", "away_last_name", "away_score"]].rename(
        columns={"away_last_name": "team", "away_score": "points"}
    )
    ], ignore_index=True)

    max_points_idx = weekly_points["points"].idxmax()
    max_points_week = weekly_points.loc[max_points_idx]

    results["max_points_week"] = max_points_week
    
    return results

def team_profile_tab(teams, matchups):
    st.header("Team Profile")

    selected_team = st.selectbox("Select a Team", sorted(teams["lastName"].unique()))

    # Filter all matchups for selected team
    team_games = matchups[
        (matchups["home_last_name"] == selected_team) | (matchups["away_last_name"] == selected_team)
    ].copy()

    # Compute win/loss per game
    team_games["win"] = (
        ((team_games["home_last_name"] == selected_team) & (team_games["home_score"] > team_games["away_score"])) |
        ((team_games["away_last_name"] == selected_team) & (team_games["away_score"] > team_games["home_score"]))
    )
    team_games["loss"] = (
        ((team_games["home_last_name"] == selected_team) & (team_games["home_score"] < team_games["away_score"])) |
        ((team_games["away_last_name"] == selected_team) & (team_games["away_score"] < team_games["home_score"]))
    )

    # Separate into regular and playoff
    regular_season = team_games[team_games["game_type"] == "regular"] 
    playoffs = team_games[team_games["game_type"] == "playoff"]

    # Group by season
    regular_grouped = regular_season.groupby("season").agg(
        wins=("win", "sum"),
        losses=("loss", "sum")
    ).reset_index()

    playoff_grouped = playoffs.groupby("season").agg(
        playoff_wins=("win", "sum"),
        playoff_losses=("loss", "sum")
    ).reset_index()

    # Show results
    st.subheader("📅 Regular Season Record")
    st.dataframe(regular_grouped)
    

    st.subheader("🏆 Playoff Record")
    if not playoff_grouped.empty:
        st.dataframe(playoff_grouped)
        
    else:
        st.write("No playoff games on record.")
    
    
    # --- Over/Under Projections ---
    st.header("📊 Over/Under ESPN Projections by Season")

    player_weeks = pd.concat([
        matchups[["season", "home_last_name", "home_score", "home_proj_score"]].rename(
            columns={"home_last_name": "team", "home_score": "actual", "home_proj_score": "projected"}
        ),
        matchups[["season", "away_last_name", "away_score", "away_proj_score"]].rename(
            columns={"away_last_name": "team", "away_score": "actual", "away_proj_score": "projected"}
        )
    ])

    player_weeks["over_under"] = player_weeks["actual"] - player_weeks["projected"]

    seasonal_over_under = (
        player_weeks.groupby(["season", "team"])["over_under"]
        .sum()
        .reset_index()
    )
    seasonal_over_under["over_under"] = seasonal_over_under["over_under"].round(2)

    team_over_under = seasonal_over_under[seasonal_over_under["team"] == selected_team]

    st.dataframe(team_over_under)

    st.bar_chart(
        team_over_under.set_index("season")["over_under"],
        use_container_width=True
    )

     # --- Weekly Scores ---
    st.header("📈 Weekly Scores Over Time")
    team_games["score"] = team_games.apply(
        lambda row: row["home_score"] if row["home_last_name"] == selected_team else row["away_score"], axis=1
    )
    team_games["week_label"] = team_games["season"].astype(str) + " - Wk " + team_games["matchup_week"].astype(str)

    st.line_chart(team_games.set_index("week_label")["score"])

    st.header("🤝 Head-to-Head Record")
    team_games["opponent"] = team_games.apply(
        lambda row: row["away_last_name"] if row["home_last_name"] == selected_team else row["home_last_name"], axis=1
    )
    h2h = team_games.groupby("opponent").agg(
        wins=("win", "sum"),
        losses=("loss", "sum")
    ).reset_index().sort_values(by="wins", ascending=False)
    st.dataframe(h2h)


def main():
    st.title("Bozwell Fantasy Football Website")

    teams, matchups, drafts = load_data()

    # Define tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Rulebook", "League History", "Team Profile", "Draft History"])

    with tab1:
        with open('rulebook.md', 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        st.markdown(markdown_content, unsafe_allow_html=True)
        

    with tab2:
        st.subheader("League History")
        stats = league_history_stats(teams, matchups)

        st.header("Past League Champions")
        st.table(stats["champions"])

        st.header("Regular Season Winners")
        st.table(stats["one_seeds"][["season", "team", "record", "win_pct"]])

        st.header("Regular Season Losers")
        st.table(stats["sackos"][["season", "team", "record", "win_pct"]])

        st.header("Overall Career Win Percentage")
        chart1 = alt.Chart(stats["overall_win_loss"]).mark_bar().encode(
            x=alt.X('win_pct', title='Win Percentage'),
            y=alt.Y('team', sort='-x', title='Team'),
            tooltip=['team', 'wins', 'losses', 'win_pct']
        ).properties(height=400)
        st.altair_chart(chart1, use_container_width=True)

        st.header("Top Scorers Per Season")
        st.table(stats["max_points_season_per_year"][["season", "team", "points"]])

        st.header("Most Points Scored in a Single Season (Overall)")
        max_season = stats["max_points_season_overall"]
        st.write(f"{max_season['team']} scored {max_season['points']} points in {max_season['season']}")

        st.header("Most Points Scored in a Single Week")
        max_week = stats["max_points_week"]
        st.write(f"{max_week['team']} scored {max_week['points']} points in Week {max_week['matchup_week']}, {max_week['season']}")

    with tab3:
        team_profile_tab(teams, matchups)


if __name__ == "__main__":
    main()
