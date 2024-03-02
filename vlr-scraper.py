import json
from dataclasses import dataclass
import bs4
import logging
import requests
import requests.api
import pandas as pd
from bs4 import BeautifulSoup
import glob
import os


logging.basicConfig(level=logging.DEBUG)

BASE: str = "https://www.vlr.gg/"
MATCHES: str = "matches/"
RANKINGS: str = "rankings/"
TEAM: str = "team/"
NEWS: str = "news/"
FORUMS: str = "forum/"
PLAYER: str = "player/"


@dataclass(order=True)
class Player:
    match_id: int
    match_date: str
    match_score: str
    game_index: int
    map: int
    game_score: str
    player_agent: str
    rounds_played: int
    rounds_played_t: int
    rounds_played_ct: int
    rounds_won_t: int
    rounds_won_ct: int
    round_difference: int
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    team_name_short: str
    team_vlr_rating: int
    
    player_rating: float
    player_rating_t: float
    player_rating_ct: float
    player_acs: int
    player_acs_t: int
    player_acs_ct: int
    player_kills: int
    player_kills_t: int
    player_kills_ct: int
    player_deaths: int
    player_deaths_t: int
    player_deaths_ct: int
    player_assists: int
    player_assists_t: int
    player_assists_ct: int
    player_kdiff: int
    player_kdiff_t: int
    player_kdiff_ct: int
    player_kast: float
    player_kast_t: float
    player_kast_ct: float
    player_adr: int
    player_adr_t: int
    player_adr_ct: int
    player_hs: float
    player_hs_t: float
    player_hs_ct: float
    player_fk: int
    player_fk_t: int
    player_fk_ct: int
    player_fd: int
    player_fd_t: int
    player_fd_ct: int
    player_fdiff: int
    player_fdiff_t: int
    player_fdiff_ct: int
    
    player_kpr: float
    player_kpr_t: float
    player_kpr_ct: float
    
    player_2k: int
    player_3k: int
    player_4k: int
    player_5k: int
    player_1v1: int
    player_1v2: int
    player_1v3: int
    player_1v4: int
    player_1v5: int
    player_econ: int
    player_pl: int
    player_de: int
    
    opponent_id: int
    opponent_name_long: str
    opponent_name_short: str
    opponent_vlr_rating: int

class RequestString(str):
    def __init__(self, string: str) -> None:
        self.string = string

    def __repr__(self) -> str:
        return self.string


def get_soup(address: str) -> BeautifulSoup:
    """Allows bs4 to parse the required address"""
    request_link: str = BASE + address
    requested = requests.get(request_link, timeout=1000)
    logging.debug(f"requesting url: {request_link} : {str(requested)}")
    soup = bs4.BeautifulSoup(requested.content, 'lxml')
    if requested.status_code == 404:
        return None
    else:
        return soup


def get_game_soups(match_id: int = None, match_soup: BeautifulSoup = None) -> list:
    """Retrieves a list of bs4 strings for each map, removes 'all' game and any non played maps"""
    if match_soup is None:
        match_soup = get_soup(str(match_id))
    map_list = match_soup.find_all(attrs={'class':'vm-stats-gamesnav-item js-map-switch'})
    map_names = []
    for map in map_list:
        split_text = map.text.strip().replace('\t', '').replace(' ', '').split('\n')
        map_names.append(split_text[2])
    stat_tab = match_soup.find(class_="vm-stats-container")
    game_soups = stat_tab.find_all(class_="vm-stats-game")
    game_soups = [game for game in game_soups if game.get(
        'data-game-id') != 'all' and get_game_map(game_soup=game) != 'TBD']
    
    # Order game_soups based on map_list only if there is more than 1 map played
    try:
        if len(game_soups) > 1:
            game_soups.sort(key=lambda game: map_names.index(get_game_map(game_soup=game)))
    except ValueError:
        logging.debug(f"Match {match_id} - Map not found in map list")
    
    return game_soups


def add_player_to_dataFrame(dataframe, player):
    dataframe.append(player)


def get_match_id_from_soup(match_soup: BeautifulSoup) -> int:
    """Returns the match id from a given match soup

    Args:
        match_soup (BeautifulSoup): a soup from the match

    Returns:
        int: match id in integer form
    """
    return int(match_soup.find(class_='vm-stats').get('data-url').split('/', maxsplit=2)[1])


def get_match_data(match_soup: BeautifulSoup = False, match_id: int = None, soups_directory: str = False, debug: bool = False) -> list:
    """Returns a list of player objects which contain all the columns of data in key value pairs.

    Args:
        match_soup (BeautifulSoup, optional): Directly pass the pre fetched bs4 object to improve performace. Defaults to None.\n
        match_id (int, optional): The function will fetch the soup before continuing. Defaults to None.

    Returns:
        list: A list of player objects containing all data associated to them in a match
    """
    match_data = []
    if match_id:
        try:
            match_soup = load_match_soup(match_id, soups_directory)
            if debug:
                print(f"Match {match_id} - Loaded from file")
        except FileNotFoundError:
            print(f"Match {match_id} - Requesting from VLR")
            match_soup = get_soup(str(match_id))
            print("Saving match soup to file")
            save_match_soup(match_id, match_soup, soups_directory)
    if match_soup:
        match_id = get_match_id_from_soup(match_soup)
    game_soups = get_game_soups(match_soup=match_soup)
    match_date = get_match_date(match_soup=match_soup)
    match_score = get_match_score(match_soup=match_soup)
    team_name_long = get_team_names_long(match_soup=match_soup)
    team_id = get_team_ids(match_soup=match_soup)
    team_elo = get_team_elos(match_soup=match_soup)
    # Looping through each map in a series (match)
    # Sets the information that changes between maps
    # creates lists for each variable in order of players retrieved
    for i, game_soup in enumerate(game_soups):
        # not including games that are less than 10 players because they shouldnt exist
        game_stats = get_game_stats(game_soup=game_soup)
        player_names = game_stats.player_name
        if len(player_names) < 10:
            continue
        game_index = i
        team_name_short = get_team_names_short(game_soup=game_soup)
        player_id = get_player_ids(game_soup)
        player_agent = game_stats.player_agent
        game_map = get_game_map(game_soup)
        rounds_played = get_game_rounds_played(game_soup)
        
        performance_stats = get_game_performance(match_id=match_id, game_index=game_index)
        performance_stats = performance_stats.merge(pd.DataFrame(player_names, columns=['player_name']), on='player_name', how='right')
        game_score = get_game_score(game_soup)
        round_difference = int(game_score.split(':')[0]) - int(game_score.split(':')[1])

        # Loops through all players playing a map
        for index, player_name in enumerate(player_names):
            if index == 5:
                round_difference = -round_difference
            # Team 1
            if index <= 4:
                player_team_long = team_name_long[0]
                player_team_short = team_name_short[0]
                player_team_id = team_id[0]
                player_team_elo = team_elo[0]
                player_opponent_long = team_name_long[1]
                player_opponent_short = team_name_short[5]
                player_opponent_id = team_id[1]
                player_opponent_elo = team_elo[1]
            # Team 2
            else:
                player_team_long = team_name_long[1]
                player_team_short = team_name_short[5]
                player_team_id = team_id[1]
                player_team_elo = team_elo[1]
                player_opponent_long = team_name_long[0]
                player_opponent_short = team_name_short[0]
                player_opponent_id = team_id[0]
                player_opponent_elo = team_elo[0]
                
            # Building a row for each player
            if game_stats.player_kills[index] is None or isinstance(rounds_played, str):
                player_kpr = None
            else:
                player_kpr = round(game_stats.player_kills[index] / int(rounds_played), 2)

            match_data.append(Player(
                match_id,
                match_date,
                match_score,
                game_index,
                game_map,
                game_score,
                player_agent[index],
                rounds_played,
                game_stats.rounds_played_t[index],
                game_stats.rounds_played_ct[index],
                game_stats.rounds_won_t[index],
                game_stats.rounds_won_ct[index],
                round_difference,
                player_id[index],
                player_name,
                player_team_id,
                player_team_long,
                player_team_short,
                player_team_elo,
                game_stats.player_rating[index],
                game_stats.player_rating_t[index],
                game_stats.player_rating_ct[index],
                game_stats.player_acs[index],
                game_stats.player_acs_t[index],
                game_stats.player_acs_ct[index],
                game_stats.player_kills[index],
                game_stats.player_kills_t[index],
                game_stats.player_kills_ct[index],
                game_stats.player_deaths[index],
                game_stats.player_deaths_t[index],
                game_stats.player_deaths_ct[index],
                game_stats.player_assists[index],
                game_stats.player_assists_t[index],
                game_stats.player_assists_ct[index],
                game_stats.player_kdiff[index],
                game_stats.player_kdiff_t[index],
                game_stats.player_kdiff_ct[index],
                game_stats.player_kast[index],
                game_stats.player_kast_t[index],
                game_stats.player_kast_ct[index],
                game_stats.player_adr[index],
                game_stats.player_adr_t[index],
                game_stats.player_adr_ct[index],
                game_stats.player_hs[index],
                game_stats.player_hs_t[index],
                game_stats.player_hs_ct[index],
                game_stats.player_fk[index],
                game_stats.player_fk_t[index],
                game_stats.player_fk_ct[index],
                game_stats.player_fd[index],
                game_stats.player_fd_t[index],
                game_stats.player_fd_ct[index],
                game_stats.player_fdiff[index],
                game_stats.player_fdiff_t[index],
                game_stats.player_fdiff_ct[index],
                player_kpr,
                game_stats.player_kpr_t[index],
                game_stats.player_kpr_ct[index],
                performance_stats.player_2k[index],
                performance_stats.player_3k[index],
                performance_stats.player_4k[index],
                performance_stats.player_5k[index],
                performance_stats.player_1v1[index],
                performance_stats.player_1v2[index],
                performance_stats.player_1v3[index],
                performance_stats.player_1v4[index],
                performance_stats.player_1v5[index],
                performance_stats.player_econ[index],
                performance_stats.player_pl[index],
                performance_stats.player_de[index],
                player_opponent_id,
                player_opponent_long,
                player_opponent_short,
                player_opponent_elo
            ))

    return match_data


def get_match_datas(match_ids: list = [], data_file: str = '', soups_directory: str = '', match_id_file: str = ''):
    """
    Returns a list of match data objects for each match in the match_id list
    """

    # Finding matches that have already been scraped into a dataset, only includes new matches to scrape
    used_match_ids = []
    data = []
    filename = 'default'
    makeNewFile = True
    if match_id_file:
        match_ids = pd.read_csv(match_id_file)['0'].to_list()
    else:
        pd.DataFrame(match_ids).to_csv('match_ids.csv', index=False)
    try:
        data = pd.read_csv(data_file)
        if data_file is not None or data.columns != len(Player.__annotations__):
            used_match_ids = data.match_id.drop_duplicates().to_list()
            used_match_ids = [str(elem) for elem in used_match_ids]
            match_ids = [
                match for match in match_ids if match not in used_match_ids]
            print(f'DATASET DETECTED - APPPENDING {len(match_ids)} MATCHES')
            makeNewFile = False
        else:
            print(
                f"Incorrect number of columns. Creating a new file with name '{filename}.csv'")

    except FileNotFoundError:
        print(f"No saved match file found. Creating new file with name '{filename}.csv'")

    # Looping through each match in the match_id list
        # Sets the information that doesnt through map/players
    for i, match_id in enumerate(match_ids):
        
        # If the match has already been scraped, load it from file   
        try:
            match_soup = load_match_soup(match_id, soups_directory)
            print(f"Match ({match_id}) | {i + 1} / {len(match_ids)} - Loaded from file")
            
        # If the match has not been scraped, request it from VLR
            # Save the match soup to file
        except FileNotFoundError:
            print(f"Match {i + 1} / {len(match_ids)} - Requesting from VLR")
            match_soup = get_soup(str(match_id))
            print("Saving match soup to file")
            save_match_soup(match_id, match_soup, soups_directory)
           
        if makeNewFile:
            try:
                data += get_match_data(match_soup=match_soup, match_id=match_id, soups_directory=soups_directory)
            except IndexError:
                print(f"({match_id}) IndexError caught, moving on to next iteration.")
                continue
            # data = data.append(get_match_data(match_soup=match_soup))   #########################################################################################################################################################################
        else:
            new_match = pd.DataFrame(get_match_data(match_soup=match_soup, match_id=match_id, soups_directory=soups_directory))
            data = pd.concat([data, new_match], ignore_index=True)

    return data


def get_match_date(match_id: int = None, match_soup: BeautifulSoup = None) -> str:
    """Returns the date of the match"""
    if not match_soup:
        match_soup = get_soup(str(match_id))
    date = RequestString(match_soup.find(
        class_="moment-tz-convert").get('data-utc-ts').split(' ')[0])
    return date.strip('\n').strip('\t')


def get_match_style(match_id: int = None, match_soup: BeautifulSoup = None) -> str:
    """Returns the match style (i.e. Bo3)"""
    if not match_soup:
        match_soup = get_soup(str(match_id))
    match_style = RequestString(match_soup.find_all(
        class_="match-header-vs-note")[1].text)
    return match_style.strip('\n').strip('\t')


def get_match_event(match_id: int = None, match_soup: BeautifulSoup = None) -> str:
    """Returns the event that the match took place in"""
    if not match_soup:
        match_soup = get_soup(str(match_id))
    return match_soup.find(class_="match-header-event").text


def get_match_score(match_id: int = None, match_soup: BeautifulSoup = None) -> str:
    """Returns the match score in a string (2:1)"""
    if not match_soup:
        match_soup = get_soup(str(match_id))
    total_score = RequestString(match_soup.find(class_="js-spoiler").text)
    return total_score.strip('\n').strip('\t').replace('\t', '').replace('\n', '')


def get_team_names_long(match_id: int = None, match_soup: BeautifulSoup = None) -> list:
    """Returns the full team names listed on VLR"""
    if not match_soup:
        match_soup = get_soup(str(match_id))
    # team_tab = soup.find(class_="match-header-vs")
    team_names = [RequestString(result.text).strip('\n').strip(
        '\t') for result in match_soup.find_all(class_="wf-title-med")]
    return team_names


def get_team_names_short(match_id: int = None, game_soup: BeautifulSoup = None) -> list:
    """Returns shortened versions of the team names"""
    if game_soup is None:
        # Teams stay the same between maps so using map 1 to determine order is ok
        game_soup = get_game_soups(match_id)[0]
    player_teams = []
    player_teams_html = game_soup.find_all("a", href=True)
    for htelements in player_teams_html:
        player_teams.append(htelements.text.split('\n')[-2].replace('\t', ''))
    return player_teams


def get_team_ids(match_id: int = None, match_soup: BeautifulSoup = None) -> list:
    """Returns team ids for a match - [Team1, Team2]"""
    if not match_soup:
        match_soup = get_soup(str(match_id))
    team_ids = []
    team_tab = match_soup.find(class_="match-header-vs")
    for i in range(2):
        team_ids.append(int(team_tab.find(
            "a", class_=f"match-header-link wf-link-hover mod-{i+1}").get('href').split('/')[2]))
    return team_ids


def get_team_elos(match_id: int = None, match_soup: BeautifulSoup = None) -> list:
    """Returns vlr ratings for both teams [Team1, Team2]"""
    team_elos = []
    if not match_soup:
        match_soup = get_soup(str(match_id))
    team_tab = match_soup.find(class_="match-header-vs")
    for result in team_tab.find_all(class_="match-header-link-name-elo"):
        if RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']') == '':
            team_elos.append(-1)
            continue
        team_elos.append(int(RequestString(result.text).strip(
            '\n').strip('\t').strip('\n').strip('[').strip(']')))
    return team_elos


def get_opponent_elos(match_id: int = None, match_soup: BeautifulSoup = None) -> list:
    """Returns reversed vlr ratings for both teams [Team2, Team1]"""
    opponent_elos = []
    if not match_soup:
        match_soup = get_soup(str(match_id))
    team_tab = match_soup.find(class_="match-header-vs")
    for result in team_tab.find_all(class_="match-header-link-name-elo"):
        if RequestString(result.text).strip('\n').strip('\t').strip('\n').strip('[').strip(']') == '':
            opponent_elos.append(-1)
            continue
        opponent_elos.append(int(RequestString(result.text).strip(
            '\n').strip('\t').strip('\n').strip('[').strip(']')))
    return opponent_elos[::-1]


def get_opponent_ids(match_id: int = None, match_soup: BeautifulSoup = None) -> list:
    """Returns reversed team ids for both teams [Team2, Team1]"""
    if not match_soup:
        match_soup = get_soup(str(match_id))
    opponent_ids = []
    team_tab = match_soup.find(class_="match-header-vs")
    for i in range(2):
        opponent_ids.append(int(team_tab.find(
            "a", class_=f"match-header-link wf-link-hover mod-{i+1}").get('href').split('/')[2]))
    return opponent_ids[::-1]


def get_player_names(game_soup: BeautifulSoup = None) -> list:
    """Returns a list of names in a map, in retrieved order from vlr"""
    player_names_html = game_soup.find_all(class_="text-of")
    player_names = []
    for htelement in player_names_html:
        player_names.append(RequestString(htelement.text).split(' ')[
                            0].replace('\t', '').replace('\n', ''))
    return player_names


def get_game_stats(game_soup: BeautifulSoup, player_index: int = False, stat_column: str = False) -> list:
    """Pulls info from the stats table and gives a table of the values

    Args:
        game_soup (BeautifulSoup): Submit a soup to improve speed. Defaults to None.\n
        player_index (int, optional): Option to return a specific row of player stats. Defaults to False.\n
        stat_column (str, optional): Option to return a specific row of player data. Defaults to False.

    Returns:
        list: Returns a pandas DataFrame with applicable column titles
    """
    player_stat_list = []
    player_stat = []
    columns = ['player_name', 
               'player_agent', 
               'player_rating', 
               'player_rating_t', 
               'player_rating_ct', 
               'player_acs',
               'player_acs_t',
               'player_acs_ct', 
               'player_kills', 
               'player_kills_t', 
               'player_kills_ct', 
               'player_deaths', 
               'player_deaths_t', 
               'player_deaths_ct', 
               'player_assists',
               'player_assists_t',
               'player_assists_ct',
               'player_kdiff', 
               'player_kdiff_t', 
               'player_kdiff_ct', 
               'player_kast', 
               'player_kast_t', 
               'player_kast_ct', 
               'player_adr',
               'player_adr_t',
               'player_adr_ct', 
               'player_hs',
               'player_hs_t',
               'player_hs_ct', 
               'player_fk',
               'player_fk_t',
               'player_fk_ct', 
               'player_fd',
               'player_fd_t',
               'player_fd_ct', 
               'player_fdiff',
               'player_fdiff_t',
               'player_fdiff_ct',
               'rounds_won_t',
               'rounds_won_ct',
               'rounds_played_t',
               'rounds_played_ct',
               'player_kpr_t',
               'player_kpr_ct',]
    
    round_cols = game_soup.find_all(class_="vlr-rounds-row-col")
    #print(round_cols[1].text)
    team_1_on_ct = False
    team_1_ct_round_wins = 0
    team_2_ct_round_wins = 0
    team_1_t_round_wins = 0
    team_2_t_round_wins = 0
    total_team_1_t_rounds = 0
    total_team_1_ct_rounds = 0
    
    for round_col in round_cols:
        try:
            round_num = int(round_col.text)
        except ValueError:
            continue
        
        if len(round_col.find_all(class_="rnd-sq mod-win mod-ct")) == 0 and len(round_col.find_all(class_="rnd-sq mod-win mod-t")) == 0:
            break
        
        if round_num == 13: # Switch sides after 12 rounds
            team_1_on_ct = not team_1_on_ct
        if round_num > 24: # Overtime handling flips the side every round
            team_1_on_ct = not team_1_on_ct
        
        if round_num == 1:
            if round_col.get('title') == "1-0" and len(round_col.find_all(class_="rnd-sq mod-win mod-ct")) == 1:
                team_1_on_ct = True
    
        if team_1_on_ct:
            total_team_1_ct_rounds += 1
        else:
            total_team_1_t_rounds += 1
        
        if round_col.find_all(class_="rnd-sq mod-win mod-ct"):
            if team_1_on_ct:
                team_1_ct_round_wins += 1
                
            else:
                team_2_ct_round_wins += 1
                
        elif round_col.find_all(class_="rnd-sq mod-win mod-t"):
            if team_1_on_ct:
                team_2_t_round_wins += 1
            else:
                team_1_t_round_wins += 1
        else:
            continue
    
    tables = game_soup.find_all('table', attrs={'class':'wf-table-inset mod-overview'})
    table_output = []
    
    for team, table in enumerate(tables): # Loop through each table in the game team 1 and team 2
        
        for i, row in enumerate(table.find_all('tr')): # Loop through each row in the table
            if i == 0: # Skip the first row as it contains the column headers
                continue
            row_data = []
            for j, cell in enumerate(row.find_all('td')): # Loop through each cell in the row
                cell_data = cell.text.replace('/', '').strip().replace('\t', "")
                
                if j == 0: # Cell 1 is the player name and its formatted weirdly, so we need to split it
                    cell_data = cell_data.split(' ')[0]
                if j == 1: # Cell 2 is the agent image, so we need to get the agent name from the title
                    try:
                        cell_data = cell.find('img').get('title')
                    except AttributeError:
                        cell_data = None
                
                if 1 < j < 14:
                    cell_data = cell_data.split("\n")
                    for k in range(3): # Loop through "All", "Attack", "Defends for each cell
                        try:
                            if cell_data[k] == "\xa0":
                                row_data.append(None)
                                continue
                            if cell_data[k] == "":
                                row_data.append(None)
                                continue
                            if cell_data[k].endswith("%"): # If the cell is a percentage, convert it to a float
                                row_data.append(float(cell_data[k].strip('%')) / 100)
                                continue
                            row_data.append(float(cell_data[k].replace(',', ""))) # If the cell is a number, convert it to a float
                        except IndexError:
                            row_data.append(None) # If the cell is empty, set it to None
                    continue
                    
                if cell_data == '': # If the cell is empty, set it to None
                    cell_data = None
                
                row_data.append(cell_data) # Append the cell data
            
            if team == 0:
                row_data.append(team_1_t_round_wins)
                row_data.append(team_1_ct_round_wins)
                row_data.append(total_team_1_t_rounds)
                row_data.append(total_team_1_ct_rounds)
                try:
                    row_data.append(row_data[8] / total_team_1_t_rounds) # KPR on T Side
                except ZeroDivisionError:
                    row_data.append(0)
                except TypeError:
                    row_data.append(None)
                try:
                    row_data.append(row_data[9] / total_team_1_ct_rounds) # KPR on CT Side
                except ZeroDivisionError:
                    row_data.append(0)
                except TypeError:
                    row_data.append(None)
            else:
                row_data.append(team_2_t_round_wins)
                row_data.append(team_2_ct_round_wins)
                row_data.append(total_team_1_ct_rounds)
                row_data.append(total_team_1_t_rounds)
                try:
                    row_data.append(round(row_data[8] / total_team_1_ct_rounds, 3)) # KPR on T Side
                except ZeroDivisionError:
                    row_data.append(0)
                except TypeError:
                    row_data.append(None)
                try:    
                    row_data.append(round(row_data[9] / total_team_1_t_rounds, 3)) # KPR on CT Side
                except ZeroDivisionError:
                    row_data.append(0)
                except TypeError:
                    row_data.append(None)
                    
            table_output.append(row_data)
    player_stat_list = pd.DataFrame(table_output, columns=columns)
    player_stat_list.to_csv('test_stats.csv')
    return player_stat_list


def get_player_kills(game_soup: BeautifulSoup = None) -> list:
    """Returns a list of kill # in a map, in retrieved order from vlr"""
    player_kills_html = game_soup.find_all(class_="mod-stat mod-vlr-kills")
    player_kills = []
    for htelement in player_kills_html:
        if RequestString(htelement.text).strip().split('\n', maxsplit=1)[0] == '':
            player_kills.append('***')
        else:
            player_kills.append(
                int(RequestString(htelement.text).strip().split('\n', maxsplit=1)[0]))
    return player_kills


def get_player_deaths(game_soup: BeautifulSoup = None) -> list:
    """Returns a list of death # in a map, in retrieved order from vlr"""
    player_deaths_html = game_soup.find_all(class_="mod-stat mod-vlr-deaths")
    player_deaths = []
    for htelement in player_deaths_html:
        if RequestString(htelement.find(class_='stats-sq').text).replace('/', '').strip().split('\n', maxsplit=1)[0] == '':
            player_deaths.append('***')
        else:
            player_deaths.append(int(RequestString(htelement.find(class_='stats-sq').text).replace('/', '').strip().split('\n', maxsplit=1)[0]))
    return player_deaths


def get_player_assists(game_soup: BeautifulSoup = None) -> list:
    """Returns a list of assist # in a map, in retrieved order from vlr"""
    player_assists_html = game_soup.find_all(class_="mod-stat mod-vlr-assists")
    player_assists = []
    for htelement in player_assists_html:
        if RequestString(htelement.text).strip().split('\n', maxsplit=1)[0] == '':
            player_assists.append('***')
        else:
            player_assists.append(
                int(RequestString(htelement.text).strip().split('\n', maxsplit=1)[0]))
    return player_assists


def get_game_score(game_soup: BeautifulSoup = None) -> list:
    """Returns the score of an individual map (13:7) (Team1 Score, Team2 Score)"""
    game_score = f"{game_soup.find_all(class_='score')[0].text}: {game_soup.find_all(class_='score')[1].text}"
    return game_score


def get_game_rounds_played(game_soup: BeautifulSoup = None) -> int:
    """Returns the total amount of rounds played in a map"""
    return int(game_soup.find_all(class_='score')[0].text) + int(game_soup.find_all(class_='score')[1].text)


def get_game_map(game_soup: BeautifulSoup = None) -> str:
    """Returns the map played"""
    map_div = game_soup.find(class_='map')
    map = map_div.find('span', style='position: relative;').text.replace(
        "PICK", '').replace('\n', '').replace('\t', '')
    return map


## Unused
def get_player_adrs(game_soup: BeautifulSoup = None) -> list:
    """Returns a list of adr # in a map, in retrieved order from vlr"""
    player_adr_html = game_soup.find_all(class_="stats-sq mod-combat")
    player_adrs = []
    for htelement in player_adr_html:
        if RequestString(htelement.text).strip().split('\n', maxsplit=1)[0] == '':
            player_adrs.append('***')
        else:
            player_adrs.append(
                int(RequestString(htelement.text).strip().split('\n', maxsplit=1)[0]))
    return player_adrs


def get_player_agents(game_soup: BeautifulSoup = None) -> list:
    """Returns a list of agents in a map, in retreived order from vlr"""
    players_agents_images = game_soup.find_all('img')
    players_agents = []
    if len(players_agents_images) < 10:
        for i in range(0, 10):
            players_agents.append('***')
    for image in players_agents_images:
        if (image.get("title")):
            players_agents.append(image.get("title"))
    return players_agents


def get_player_ids(game_soup: BeautifulSoup = None) -> list:
    """Returns a list of player ids in a map, in retrieved order from vlr"""
    player_ids = []
    player_ids_html = game_soup.find_all("a", href=True)
    for htelements in player_ids_html:
        player_ids.append((htelements)['href'].split('/')[2])
    return player_ids


def get_opponent_name_short(match_id: int = None, game_soup: BeautifulSoup = None) -> list:
    """Returns a reversed list of short team names in retrieved order"""
    if game_soup is None:
        # Teams stay the same between maps so using map 1 to determine order is ok
        game_soup = get_game_soups(match_id)[0]
    player_teams = []
    player_teams_html = game_soup.find_all("a", href=True)
    for htelements in player_teams_html:
        player_teams.append(htelements.text.split('\n')[-2].replace('\t', ''))
    return player_teams[::-1]


def get_opponent_name_long(match_id: int = None, soup: BeautifulSoup = None) -> list:
    """Returns a reversed list of long team names (Team2, Team1)"""
    if not soup:
        soup = get_soup(str(match_id))
    team_names = [RequestString(result.text).strip('\n').strip(
        '\t') for result in soup.find_all(class_="wf-title-med")]
    return team_names[::-1]


def get_player_infos(player_id: int) -> dict:
    """Gets player info from profile page"""
    player_soup = get_soup(PLAYER + str(player_id))
    header = player_soup.find(class_="wf-card mod-header mod-full")
    name = header.find(class_="wf-title").text
    real_name = header.find(class_="player-real-name").text
    twitter_link = header.find("a", href=True)
    twitch_link = header.find_next("a", href=True)
    country = header.find_all("div")
    return {"name": RequestString(name), "real_name": real_name,
            "twitter": twitter_link["href"], "twitch": twitch_link["href"],
            "country": RequestString(country[6].text)}


def get_player_match_ids(player_id: int, amount: int = 1) -> list:
    """Fetches a list of match ids from a given number of previous matches user defined length"""
    match_ids = []
    for i in range(int(amount/50) + 1):
        player_matches_soup = get_soup(
            PLAYER + MATCHES + str(player_id) + '/?page=' + str(i+1))
        matches = player_matches_soup.find_all(
            "a", class_="wf-card fc-flex m-item")
        for match in matches:
            match_ids.append(match.get("href").split('/')[1])
    return match_ids[0:amount]


def get_team_match_ids(team_id: int, amount: int = 1) -> list:
    """Fetches a list of match ids from previous games a team has played in user defined list length"""
    match_ids = []
    for i in range(int(amount/50) + 1):
        player_matches_soup = get_soup(
            TEAM + MATCHES + str(team_id) + '/?page=' + str(i+1))
        matches = player_matches_soup.find_all(
            "a", class_="wf-card fc-flex m-item")
        for match in matches:
            match_ids.append(match.get("href").split('/')[1])
    return match_ids[0:amount]

def get_game_performance(match_id: int, game_index: int, player_index: int = False, stat_column: str = False) -> list:    
    
    try:
        #print("Attempting to load performance soup from file")
        performance_soup = load_performance_soup(match_id, SOUPS_DIRECTORY)
    except FileNotFoundError:
        print(f"Perf soup not found for match ({match_id}) - Requesting from VLR")
        performance_soup = get_soup(str(match_id) + '/?tab=performance')
        print("Saving match soup to file")
        save_performance_soup(match_id, performance_soup, SOUPS_DIRECTORY)
    
    #performance_html = performance_soup.find_all(class_="wf-table-inset mod-adv-stats")[1:]
    #performance_table = performance_html[game_index].find_all('td')
    
    player_stat_list = []
    player_stat = []
    columns = ['player_name', 'player_2k', 'player_3k', 'player_4k', 'player_5k', 
               'player_1v1', 'player_1v2', 'player_1v3', 'player_1v4', 'player_1v5', 
               'player_econ', 'player_pl', 'player_de']
    
    
    try:
        table = performance_soup.find_all('table', attrs={'class':'wf-table-inset mod-adv-stats'})[game_index + 1]
    except IndexError:
        print(f"Match {match_id} - IndexError caught, returning empty dataframe")
        return pd.DataFrame(columns=columns)
    #save_soup(table, 'test', '/Users/nickt/Documents/Coding/Python Projects/Valorant Player Data')
    #table_rows = table.find_all('tr')

    data = []
    for row in table.find_all('tr'):
        row_data = []
        for index, cell in enumerate(row.find_all('td')):
            #stat = cell.text.strip().replace('\t', "").replace('\n', '')
            if index == 0:
                stat = cell.text.strip().replace('\t', "").split('\n')[0]
            elif index == 1:
                continue
            elif cell.text.strip().replace('\t', "") == '':
                stat = 0
            else:
                stat = int(cell.text.strip().replace('\t', "").split('\n')[0])
            row_data.append(stat)
        data.append(row_data)
    
    player_stat_list = pd.DataFrame(data[1:], columns=columns)

    return player_stat_list

def to_json(filename: str, data: dict, indent: int = 4, append: bool = False) -> None:
    """Converts a python dictionary to json format"""
    with open(file=f"{filename}.json", mode="a") as file:
        json.dump(data, file, indent=indent)
        # Add a newline after each JSON object for readability
        file.write('\n')

def to_csv(self : pd.DataFrame, filename : str = 'default') -> None:
    """Converts a pandas dataframe to a .csv file"""
    self.to_csv(f'{filename}.csv', index=False)

def save_soup(soup: BeautifulSoup, filename: str, directory: str) -> None:
    """Saves a soup to a text file"""
    with open(f"{directory}/{filename}", 'w') as file:
        file.write(str(soup))

def save_match_soup(match_id: int, match_soup: BeautifulSoup, soup_directory: str) -> None:
    """Save the match_soup to a text file with the name of the file being the match_id"""
    filename = f"{match_id}.txt"
    save_soup(match_soup, filename, soup_directory)
   
def save_performance_soup(match_id: int, performance_soup: BeautifulSoup, soup_directory: str) -> None:
    """Save the match_soup to a text file with the name of the file being the match_id + '-perftab'"""
    filename = f"{match_id}-perftab.txt"
    save_soup(performance_soup, filename, soup_directory)  
                 
def load_match_soup(match_id: int, soup_directory: str, debug_print: bool = False) -> BeautifulSoup:
    """Load the match_soup from a text file with the name of the file being the match_id"""
    filename = f"{soup_directory}/{match_id}.txt"
    if debug_print: 
        print(f"Loading match ({match_id}) from {filename}")
    with open(filename, 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    return soup

def load_performance_soup(match_id: int, soup_directory: str, debug_print: bool = False) -> BeautifulSoup:
    """Load the match_soup from a text file with the name of the file being the match_id"""
    filename = f"{match_id}-perftab.txt"
    if debug_print: 
        print(f"Loading performance soup ({match_id}) from {filename}")
    return load_soup_file(filename, soup_directory)

def load_soup_file(filename: str, directory: str, debug: bool = False) -> BeautifulSoup:
    """Load a soup file from a directory"""
    if debug:
        print(f"Loading soup from {directory}/{filename}")
    with open(f"{directory}/{filename}", 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    return soup


americas = [
    2406,
    6961,
    2359,
    188,
    7389,
    1034,
    2,
    120,
    5248,
    2355,
    11058
]
emea = [
    2593,
    1184,
    474,
    4915,
    2059,
    2304,
    1001,
    7035,
    8877,
    397,
    12694
]
pacific =[
    8185,
    624,
    17,
    6199,
    14,
    5448,
    878,
    918,
    278,
    8304,
    6387
]
china = [
    1119,
    12010,
    1120,
    11328,
    13576,
    12064,
    12685,
    14137,
    731,
    13790,
    11981
]

# What regions to scrape
all_regions = americas + emea + pacific + china

# How many historical matches to scrape
AMOUNT = 3
SOUPS_DIRECTORY = '/Users/nickt/Documents/Coding/Python Projects/Valorant Player Data/Match Soup Files'
PLAYER_DATA_DIRECTORY = '/Users/nickt/Documents/Coding/Python Projects/Valorant Player Data/Player Data'


if True:    
    # Get a list of all CSV files in the directory
    csv_files = glob.glob(os.path.join(PLAYER_DATA_DIRECTORY, '*.csv'))

    # Sort the files by modification time in descending order
    sorted_files = sorted(csv_files, key=os.path.getmtime, reverse=True)

    # Get the path of the most recent CSV file
    most_recent_file = sorted_files[0]

    # Read the most recent player data
    most_recent_player_data = pd.DataFrame(pd.read_csv(most_recent_file))
    
    scraped_matches = most_recent_player_data.match_id.to_list()
    scraped_matches = list(set(scraped_matches))

    match_data_list = []
    unique_matches = []
    matches = []
    failed_match_ids = [283388]
    for team in all_regions:
        matches += get_team_match_ids(team, AMOUNT)
        unique_matches = list(set(matches))
        print(len(unique_matches))
    unique_matches = [int(match) for match in unique_matches]
    new_matches = [match_id for match_id in unique_matches if match_id not in scraped_matches and match_id not in failed_match_ids]
    
    if len(new_matches) == 0:
        print("No new matches to scrape")
        exit()
    
    match_datas = get_match_datas(new_matches, soups_directory='/Users/nickt/Documents/Coding/Python Projects/Valorant Player Data/Match Soup Files')
    match_datas = pd.DataFrame(match_datas)
    match_datas = match_datas._append(most_recent_player_data, ignore_index=True)
        
    current_date = pd.to_datetime('today').strftime('%m-%d-%y')

    match_datas.to_csv(f'Valorant Player Data/Player Data/All_Region({current_date}).csv', index=False)
    match_datas.to_csv(f'/Users/nickt/Documents/Local UW Files/STAT240/data/val_data.csv', index=False)

