import streamlit as st
import sqlite3
import pandas as pd
import streamlit as st

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
    """Compute win/loss records for each team."""
    owners = teams["lastName"].unique()
    results = {}
    # 1. Past Champions: find playoff finals winners by season
    champions = [{"season": 2020, "champion": "BRANITZKY"}]
    matchups["is_playoffs"] = matchups["is_playoffs"].astype(bool)
    for season in matchups["season"].unique():
        playoffs = matchups[(matchups["season"] == season) & (matchups["is_playoffs"])]
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
    regular_season = matchups[~matchups["is_playoffs"]]
    # Compute win/loss per team per season
    team_records = []
    for season in regular_season["season"].unique():
        season_games = regular_season[regular_season["season"] == season]
        teams = pd.concat([
            season_games[["home_last_name", "home_score", "away_score"]].rename(columns={"home_last_name": "team", "home_score": "team_score", "away_score": "opp_score"}),
            season_games[["away_last_name", "away_score", "home_score"]].rename(columns={"away_last_name": "team", "away_score": "team_score", "home_score": "opp_score"})
        ])
        # Calculate wins/losses
        teams["win"] = teams["team_score"] > teams["opp_score"]
        wins = teams.groupby("team")["win"].sum()
        total_games = teams.groupby("team")["win"].count()
        win_pct = wins / total_games
        df = pd.DataFrame({"season": season, "team": wins.index, "wins": wins.values, "games": total_games.values, "win_pct": win_pct.values})
        team_records.append(df)
    team_records_df = pd.concat(team_records)

    max_win_pct_per_season = team_records_df.groupby("season")["win_pct"].max().reset_index()
    one_seeds = pd.merge(team_records_df, max_win_pct_per_season, on=["season", "win_pct"], how="inner")
    one_seeds = one_seeds.sort_values(by=["season", "team"]).drop_duplicates(subset=["season"])
    results["one_seeds"] = one_seeds[["season", "team", "win_pct"]].reset_index(drop=True)

    # 3. Sacko (last place)
    min_win_pct_per_season = team_records_df.groupby("season")["win_pct"].min().reset_index()
    sackos = pd.merge(team_records_df, min_win_pct_per_season, on=["season", "win_pct"], how="inner")
    sackos = sackos.sort_values(by=["season", "team"]).drop_duplicates(subset=["season"])
    results["sackos"] = sackos[["season", "team", "win_pct"]].reset_index(drop=True)

    """
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
            "win_pct": round(win_pct, 3)
        })
    """
    return results


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
        st.header("Past Champions")
        st.table(stats["champions"])

        st.header("Regular Season #1 Seeds")
        st.table(stats["one_seeds"][["season", "team", "win_pct"]])

        st.header("Sackos")
        st.table(stats["sackos"][["season", "team", "win_pct"]])

        """""
        st.header("Career Stats")
        st.dataframe(stats["career_stats"])

        st.header("Most Points Scored in a Season")
        mp = stats["max_points_season"]
        st.write(f"{mp['team']} scored {mp['points']} points in {mp['season']}")

        st.header("Most Points Scored in a Single Week")
        mpw = stats["max_points_week"]
        st.write(f"{mpw['team']} scored {mpw['points']} points in Week {mpw['matchup_week']}, {mpw['season']}")
        """


    with tab2:
        st.subheader("All Matchups")
        #st.dataframe(matchups, use_container_width=True)


if __name__ == "__main__":
    main()
