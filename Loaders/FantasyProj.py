import sqlite3
from espn_api.football import League
import os
from dotenv import load_dotenv

load_dotenv()
LEAGUEID = int(os.getenv("LEAGUE_ID"))
SWID = os.getenv("SWID")
ESPN_S2 = os.getenv("ESPN_S2")

def scrape_historical():
    all_teams = []
    all_matchups = []
    all_drafts = []

    for year in range(2021, 2025):
        league = League(league_id=LEAGUEID, year=year, espn_s2=ESPN_S2, swid=SWID)
        all_teams.extend(teams_loader(league))
        all_matchups.extend(matchup_loader(league, year))
        all_drafts.extend(drafts_loader(league, year))

    return all_teams, all_matchups, all_drafts

def teams_loader(league):
    all_teams = []
    for team in league.teams:
        first_name = team.owners[0]["firstName"].upper()
        last_name = team.owners[0]["lastName"].upper()
        if last_name == "THE GREAT":
            last_name = "JAIME"
        entry = {
            "lastName": last_name,
            "firstName": first_name,
            "teamName": team.team_name,
        }
        all_teams.append(entry)
    return all_teams

def matchup_loader(league, year):
    all_matchups = []

    final_standings = {team: team.final_standing for team in league.teams}
    teams_by_name = {team: team.team_name for team in league.teams}

    playoff_teams = set(team for team, standing in final_standings.items() if standing <= 8)
    alive_playoff_teams = playoff_teams.copy()

    for week in range(1, 18):
        try:
            matchups = league.box_scores(week)
        except Exception as e:
            print(f"Error fetching box scores for season {year}, week {week}: {e}")
            continue

        next_alive = set()

        for matchup in matchups:
            home_team = matchup.home_team
            away_team = matchup.away_team

            home_last_name = home_team.owners[0]["lastName"].upper()
            away_last_name = away_team.owners[0]["lastName"].upper()

            if home_last_name == "THE GREAT":
                home_last_name = "JAIME"
            if away_last_name == "THE GREAT":
                away_last_name = "JAIME"

            home_score = matchup.home_score
            away_score = matchup.away_score
            home_proj_score = matchup.home_projected
            away_proj_score = matchup.away_projected

            # Game type logic
            if week < 15:
                game_type = "regular"
            elif week == 15:
                if home_team in playoff_teams and away_team in playoff_teams:
                    game_type = "playoff"
                    winner = home_team if home_score > away_score else away_team
                    next_alive.add(winner)
                else:
                    game_type = "non_playoff"
            elif week >= 16:
                if home_team in alive_playoff_teams and away_team in alive_playoff_teams:
                    game_type = "playoff"
                    winner = home_team if home_score > away_score else away_team
                    next_alive.add(winner)
                else:
                    game_type = "non_playoff"

            entry = {
                "season": year,
                "week": week,
                "home_last": home_last_name,
                "away_last": away_last_name,
                "home_score": home_score,
                "away_score": away_score,
                "home_projected": home_proj_score,
                "away_projected": away_proj_score,
                "game_type": game_type
            }

            all_matchups.append(entry)

        if week in [15, 16]:
            alive_playoff_teams = next_alive

    return all_matchups


def drafts_loader(league, year):
    draft_entries = []
    for pick in league.draft:
        team_last = pick.team.owners[0]["lastName"].upper()
        if team_last == "THE GREAT":
            team_last = "JAIME"
        player_name = getattr(pick, "playerName", None) or "UNKNOWN PLAYER"
        entry = {
            "player_id": pick.playerId,
            "team_last_name": team_last,
            "season": year,
            "draft_round": pick.round_num,
            "draft_pick": pick.round_pick,
            "player_name": player_name
        }
        draft_entries.append(entry)
    return draft_entries


def load_db(db_file, teams, matchups, drafts):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    # Load Teams
    for team in teams:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO teams (lastName, firstName, teamName)
                VALUES (?, ?, ?)
            """, (
                team["lastName"],
                team.get("firstName", ""),
                team["teamName"]
            ))
        except sqlite3.Error as e:
            print(f"Team insert error: {team['lastName']} - {e}")

    # Load Matchups
    for matchup in matchups:
        try:
            cursor.execute("""
                INSERT INTO matchups (
                    season, matchup_week,
                    home_last_name, away_last_name,
                    home_score, away_score,
                    home_proj_score, away_proj_score,
                    game_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                matchup["season"],
                matchup["week"],
                matchup["home_last"],
                matchup["away_last"],
                matchup["home_score"],
                matchup["away_score"],
                matchup["home_projected"],
                matchup["away_projected"],
                matchup["game_type"]
            ))
        except sqlite3.Error as e:
            print(f"Matchup insert error (Week {matchup['week']}): {e}")

    # Load Drafts
    for draft in drafts:
        try:
            cursor.execute("""
                INSERT INTO drafts (player_id, team_last_name, season, draft_round, draft_pick, player_name) VALUES (?, ?, ?, ?, ?, ?)""", (
                draft["player_id"],
                draft["team_last_name"],
                draft["season"],
                draft["draft_round"],
                draft["draft_pick"],
                draft["player_name"]
            ))
        except sqlite3.Error as e:
            print(f"Draft insert error (Player ID {draft['player_id']}): {e}")

    connection.commit()
    connection.close()
    print("All data loaded into SQLite database.")


def main():
    """ Main Function """
    db_file = "fantasy.db"
    print("Scraping ESPN Fantasy Football data...")
    teams, matchups, drafts = scrape_historical()
    print("Loading data into SQLite...")
    load_db(db_file, teams, matchups, drafts)
    print("All done.")

if __name__ == "__main__":
    main()

