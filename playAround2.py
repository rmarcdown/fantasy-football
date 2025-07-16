import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

def load_data():
    connection = sqlite3.connect("fantasy.db")
    teams = pd.read_sql("SELECT * FROM teams", connection)
    matchups = pd.read_sql("SELECT * FROM matchups", connection)
    drafts = pd.read_sql("SELECT * FROM drafts", connection)
    keepers = pd.read_sql("SELECT * FROM keepers", connection)
    connection.close()
    return teams, matchups, drafts, keepers

def team_profile(selected_team, matchups):
    st.title(f"Team Profile: {selected_team}")

    # --- Season Breakdown ---
    st.header("📆 Season-by-Season Breakdown")

    # Filter for selected team's games
    season_summary = matchups[
        (matchups["home_last_name"] == selected_team) | (matchups["away_last_name"] == selected_team)
    ].copy()

    # Determine win/loss
    season_summary["win"] = ((season_summary["home_last_name"] == selected_team) & (season_summary["home_score"] > season_summary["away_score"])) | \
                            ((season_summary["away_last_name"] == selected_team) & (season_summary["away_score"] > season_summary["home_score"]))
    season_summary["loss"] = ((season_summary["home_last_name"] == selected_team) & (season_summary["home_score"] < season_summary["away_score"])) | \
                            ((season_summary["away_last_name"] == selected_team) & (season_summary["away_score"] < season_summary["home_score"]))

    # Split into regular season and playoffs
    regular_season = season_summary[season_summary["is_playoffs"] == 0]
    playoffs = season_summary[season_summary["is_playoffs"] == 1]

    # Aggregate regular season
    regular_grouped = regular_season.groupby("season").agg(
        wins=("win", "sum"),
        losses=("loss", "sum")
    ).reset_index()

    # Aggregate playoff games
    playoff_grouped = playoffs.groupby("season").agg(
        playoff_wins=("win", "sum"),
        playoff_losses=("loss", "sum")
    ).reset_index()

    # Display in Streamlit
    st.subheader("📅 Regular Season Record")
    st.dataframe(regular_grouped)
    st.plotly_chart(px.bar(regular_grouped, x="season", y=["wins", "losses"], barmode="group", title="Regular Season Results"))

    st.subheader("🏆 Playoff Record")
    if not playoff_grouped.empty:
        st.dataframe(playoff_grouped)
        st.plotly_chart(px.bar(playoff_grouped, x="season", y=["playoff_wins", "playoff_losses"], barmode="group", title="Playoff Results"))
    else:
        st.write("No playoff games on record.")


    # --- Weekly Scores ---
    st.header("📈 Weekly Scores Over Time")
    season_summary["score"] = season_summary.apply(
        lambda row: row["home_score"] if row["home_last_name"] == selected_team else row["away_score"], axis=1
    )
    season_summary["week_label"] = season_summary["season"].astype(str) + " - Wk " + season_summary["matchup_week"].astype(str)

    st.line_chart(season_summary.set_index("week_label")["score"])

    # --- Playoff Runs ---
    st.header("🏆 Playoff Performance")
    playoff_summary = season_summary[season_summary["game_type"] == "playoff"]
    if not playoff_summary.empty:
        playoff_grouped = playoff_summary.groupby("season").agg(
            playoff_wins=("win", "sum"),
            playoff_losses=("loss", "sum")
        ).reset_index()
        st.dataframe(playoff_grouped)
    else:
        st.write("No playoff appearances on record.")

    # --- Head-to-Head Stats ---
    st.header("🤝 Head-to-Head Record")
    season_summary["opponent"] = season_summary.apply(
        lambda row: row["away_last_name"] if row["home_last_name"] == selected_team else row["home_last_name"], axis=1
    )
    h2h = season_summary.groupby("opponent").agg(
        wins=("win", "sum"),
        losses=("loss", "sum")
    ).reset_index().sort_values(by="wins", ascending=False)
    st.dataframe(h2h)

    # --- Big Games ---
    st.header("🔥 Big Games")
    season_summary["point_diff"] = abs(season_summary["home_score"] - season_summary["away_score"])
    top_games = season_summary.sort_values(by="point_diff", ascending=False).head(5)
    st.dataframe(top_games[["season", "matchup_week", "home_last_name", "away_last_name", "home_score", "away_score", "point_diff"]])

    # --- Point Trends ---
    st.header("📊 Points For and Against by Season")
    trend_df = season_summary.groupby("season").agg(
        avg_points_for=("score", "mean"),
        avg_points_against=("away_score" if season_summary["home_last_name"].iloc[0] == selected_team else "home_score", "mean")
    ).reset_index()
    st.line_chart(trend_df.set_index("season"))


def main():
    st.set_page_config(page_title="Fantasy Football Team Profile", layout="wide")
    st.sidebar.title("🔎 Team Explorer")

    teams, matchups, drafts, keepers = load_data()
    team_names = teams["lastName"].tolist()
    selected_team = st.sidebar.selectbox("Select an Owner", team_names)

    if selected_team:
        team_profile(selected_team, matchups)

if __name__ == "__main__":
    main()
