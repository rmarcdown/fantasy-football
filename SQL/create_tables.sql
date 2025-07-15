CREATE TABLE teams (    
    lastName VARCHAR(256) NOT NULL,
    firstName VARCHAR(256) NOT NULL,
    teamName VARCHAR(256) NOT NULL,
    PRIMARY KEY(lastName)
);

CREATE TABLE matchups (
    matchup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    matchup_week INTEGER NOT NULL,
    home_last_name VARCHAR(256) NOT NULL,
    away_last_name VARCHAR(256) NOT NULL,
    home_score REAL,
    away_score REAL,
    home_proj_score REAL,
    away_proj_score REAL,
    is_playoffs BOOLEAN DEFAULT 0,
    FOREIGN KEY (home_last_name) REFERENCES teams(lastName),
    FOREIGN KEY (away_last_name) REFERENCES teams(lastName)
);

CREATE TABLE drafts (
    player_id INTEGER,
    team_last_name VARCHAR(256) NOT NULL,
    season INTEGER NOT NULL,
    draft_round INTEGER,
    draft_pick INTEGER,          
    FOREIGN KEY (team_last_name) REFERENCES teams(lastName)
);

CREATE TABLE keepers (
    player_id INTEGER,
    team_last_name VARCHAR(256) NOT NULL,
    season INTEGER NOT NULL,
    draft_round INTEGER,         -- original draft round
    years_kept INTEGER,          -- how many years this player has been kept
    keeper_round INTEGER,        -- round used this season
    FOREIGN KEY (team_last_name) REFERENCES teams(lastName)
);


