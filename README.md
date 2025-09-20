# Valorant Player Data 

### Structure of the data
A "match" in valorant can also be called a "series" and will usually be a best of 3 games or best of 5 games.
Each match can have many "games" or "maps within it. 

* As of now only teams in regions of **VCT** (i.e. Americas, EMEA, Pacific, China) are included

### Example
`match_id`: 303095
- `game_index`: 0
  - `map`: "Sunset"
  - `team_name`: Karmine Corp
  - `opponent_name`: Team Heretics
  - ...
- `game_index`: 1
  - `map`: "Lotus"
  - `team_name`: Karmine Corp
  - `opponent_name`: Team Heretics
  - ...

`match_id`: ...

**Columns:**

* **`match_id` (int):** The match ID for the match as on vlr.gg/`match_id`.
* **`match_event` (str):** The event in which the match took place.
* **`event_id` (str):** The ID of the event in which the match took place ans on vlr.gg/`event_id`.
* **`match_link` (str):** The link to the vlr match page.
* **`match_date` (str):** The date the match took place.
* **`match_score` (str):** The final score of the series "[TEAM 1]:[TEAM 2]".
* **`game_index` (int):** The index of the game in the series (0 = Game 1, 1 = Game 2, etc...).
* **`map` (str):** The name of the map being played.
* **`game_score` (str):** Ending round score for the game "[TEAM 1 ROUNDS]:[TEAM 2 ROUNDS]".
* **`player_agent` (str):** The agent played by the player in the game.
* **`rounds_played` (int):** The total rounds played in the game.
* **`rounds_played_attacker` (int):** Number of rounds played as Attacker.
* **`rounds_played_defender` (int):** Number of rounds played as Defender.
* **`rounds_won_attacker` (int):** Number of rounds won as Attacker.
* **`rounds_won_defender` (int):** Number of rounds won as Defender.
* **`round_difference` (int):** Difference between rounds won by Team 1 and Team 2.
* **`player_id` (int):** Unique identifier for the player (vlr.gg/player/`player_id`).
* **`player_name` (str):** Name of the player.
* **`team_id` (int):** Unique identifier for the team (vlr.gg/team/`team_id`).
* **`team_name` (str):** Full name of the team.
* **`team_name_short` (str):** Abbreviated name of the team.
* **`team_vlr_rating` (int):** VLR rating of the team (if available, -1 if N/A).
* **`player_rating` (float):** Overall rating of the player in the game.
* **`player_rating_attacker` (float):** Rating of the player as Attacker.
* **`player_rating_defender` (float):** Rating of the player as Defender.
* **`player_acs` (float):** Average Combat Score of the player.
* **`player_acs_attacker` (float):** Average Combat Score of the player as Attacker.
* **`player_acs_defender` (float):** Average Combat Score of the player as Defender.
* **`player_kills` (int):** Total number of kills by the player.
* **`player_kills_attacker` (int):** Number of kills by the player as Attacker.
* **`player_kills_defender` (int):** Number of kills by the player as Defender.
* **`player_deaths` (int):** Total number of deaths by the player.
* **`player_deaths_attacker` (int):** Number of deaths by the player as Attacker.
* **`player_deaths_defender` (int):** Number of deaths by the player as Defender.
* **`player_assists` (int):** Total number of assists by the player.
* **`player_assists_attacker` (int):** Number of assists by the player as Attacker.
* **`player_assists_defender` (int):** Number of assists by the player as Defender.
* **`player_kdiff` (int):** Kill-Death difference of the player.
* **`player_kdiff_attacker` (int):** Kill-Death difference of the player as Attacker.
* **`player_kdiff_defender` (int):** Kill-Death difference of the player as Defender.
* **`player_kast` (float):** Kill-Assist-Survive-Traded percentage of the player.
* **`player_kast_attacker` (float):** Kill-Assist-Survive-Traded percentage of the player as Attacker.
* **`player_kast_defender` (float):** Kill-Assist-Survive-Traded percentage of the player as Defender.
* **`player_adr` (float):** Average Damage per Round of the player.
* **`player_adr_attacker` (float):** Average Damage per Round of the player as Attacker.
* **`player_adr_defender` (float):** Average Damage per Round of the player as Defender.
* **`player_hs` (float):** Headshot % by the player.
* **`player_hs_attacker` (float):** Headshot % by the player as Attacker.
* **`player_hs_defender` (float):** Headshot % by the player as Defender.
* **`player_fk` (int):** Total number of first kills (First Bloods) by the player.
* **`player_fk_attacker` (int):** Number of first kills (First Bloods) by the player as Attacker.
* **`player_fk_defender` (int):** Number of first kills (First Bloods) by the player as Defender.
* **`player_fd` (int):** Total number of first deaths by the player.
* **`player_fd_attacker` (int):** Number of first deaths by the player as Attacker.
* **`player_fd_defender` (int):** Number of first deaths by the player as Defender.
* **`player_fdiff` (int):** First Kill-First Death difference of the player.
* **`player_fdiff_attacker` (int):** First Kill-First Death difference of the player as Attacker.
* **`player_fdiff_defender` (int):** First Kill-First Death difference of the player as Defender.
* **`player_2k` (int):** Number of rounds with 2 kills.
* **`player_3k` (int):** Number of rounds with 3 kills.
* **`player_4k` (int):** Number of rounds with 4 kills.
* **`player_5k` (int):** Number of rounds with 5 kills.
* **`player_1v1` (int):** Number of 1v1 clutch rounds won.
* **`player_1v2` (int):** Number of 1v2 clutch rounds won.
* **`player_1v3` (int):** Number of 1v3 clutch rounds won.
* **`player_1v4` (int):** Number of 1v4 clutch rounds won.
* **`player_1v5` (int):** Number of 1v5 clutch rounds won.
* **`player_econ` (int):** Economy rating of the player.
* **`player_pl` (int):** Number of plants by the player.
* **`player_de` (int):** Number of spike defuses by the player.
* **`opponent_id` (int):** Unique identifier for the opponent.
* **`opponent_name_long` (str):** Full name of the opponent team.
* **`opponent_name_short` (str):** Abbreviated name of the opponent team.
* **`opponent_vlr_rating` (int):** VLR rating of the opponent team (if available, -1 if N/A).
