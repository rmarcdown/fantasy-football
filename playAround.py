import sqlite3
import pandas as pd

def play_around():

    results = {}
        

    # Connect to your fantasy database
    connection = sqlite3.connect("fantasy.db")
    teams = pd.read_sql_query("SELECT * FROM teams", connection)
    matchups = pd.read_sql_query("SELECT * FROM matchups", connection)
    drafts = pd.read_sql_query("SELECT * FROM drafts", connection)


    # Example output
    print(drafts[drafts['year'] == 2021])


    connection.close()

def main():
    play_around()

if __name__ == "__main__":
    main()
