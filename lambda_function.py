from twilio.twiml.messaging_response import Message, MessagingResponse
import json
import team_defs as teams
import requests
from time_util import format_clock, to_pacific_date_time, get_today_date

class NBATeam:
    def __init__(self, team_def):
        self.city = team_def["city"]
        self.altCityName = team_def["altCityName"]
        self.fullName = team_def["fullName"]
        self.triCode = team_def["tricode"]
        self.teamId = team_def["teamId"]
        self.nickname = team_def["nickname"]
        self.urlName = team_def["urlName"]
        self.teamShortName = team_def["teamShortName"]
        self.confName = team_def["confName"]
        self.divName = team_def["divName"]

def process_message(body):
    body = body.lower()
    if (body.startswith("score")):
        return get_score(body[6:])
    elif (body.startswith("scores")):
        return get_score(body[7:])
    else:
        return get_score(body)

def get_score(team_str):
    nba_team = get_team(team_str.strip())
    today_date = get_today_date()
   
    response = requests.get(f"https://data.nba.net/10s/prod/v1/{today_date}/scoreboard.json")
    if response.status_code == 200:
        if (nba_team == None):
            return get_scores_for_all_games(response.json())
        else:
            return get_box_score_for_game(response.json(), nba_team, today_date)
    else:
        return "There was an error retrieving the games for today, please try again later."

def get_scores_for_all_games(all_games):
    if (all_games["numGames"] == 0):
        return "There are no games today."
    else:
        display_strings = map(lambda game: get_simplified_game_summary(game), all_games["games"])
        return "\n".join(map(str, display_strings))

def get_box_score_for_game(all_games, nba_team, today_date):
    game_today_for_team = get_game_for_team(all_games, nba_team)
    if (game_today_for_team == None):
        return get_next_game_for_team(nba_team)
    else:
        return get_extended_game_summary(game_today_for_team, today_date)

def get_next_game_for_team(nba_team):
    schedule_response = requests.get(f"https://data.nba.net/10s/prod/v1/2019/teams/{nba_team.teamId}/schedule.json")
    default_response =  f"{nba_team.triCode} is not playing today"
    if schedule_response.status_code == 200:
        try:
            schedules = schedule_response.json()
            next_game_start_time = find_next_game_start_time(schedules)
            next_game_opponent = find_next_game_opponent(schedules, nba_team)
            return f"{nba_team.triCode} is not playing today, their next game time is {next_game_start_time} against {next_game_opponent.triCode}"
        except:
            return default_response
    else:
        return default_response

def find_next_game_start_time(schedules): 
    last_game_played = schedules["league"]["lastStandardGamePlayedIndex"]
    next_game = schedules["league"]["standard"][last_game_played + 1]
    return to_pacific_date_time(next_game["startTimeUTC"])

def find_next_game_opponent(schedules, nba_team):
    last_game_played = schedules["league"]["lastStandardGamePlayedIndex"]
    next_game = schedules["league"]["standard"][last_game_played + 1]
    if (nba_team.teamId != next_game["vTeam"]["teamId"]):
        opponent_team_id = next_game["vTeam"]["teamId"]
    else:
        opponent_team_id = next_game["hTeam"]["teamId"]
    return lookup_by_team_id(opponent_team_id)

def lookup_by_team_id(team_id):
    team = next(team for team in teams.team_defs if team["teamId"] == team_id)
    return NBATeam(team)

def get_extended_game_summary(game, today_date):
    gameId = game["gameId"]
    boxscore_response = requests.get(f"https://data.nba.net/10s/prod/v1/{today_date}/{gameId}_boxscore.json")

    if boxscore_response.status_code == 200:
        boxscore = get_simplified_boxscore(boxscore_response.json())
        return get_simplified_game_summary(game) + boxscore
    else:
        return get_simplified_game_summary(game)

def get_simplified_boxscore(boxscore):
    if (is_game_not_started(boxscore["basicGameData"])):
        return ""
    home_team_id = boxscore["basicGameData"]["hTeam"]["teamId"]
    home_tri_code = boxscore["basicGameData"]["hTeam"]["triCode"]
    visitor_tri_code = boxscore["basicGameData"]["vTeam"]["triCode"]
    
    players_for_home_team = []
    players_for_visiting_team = []

    players = boxscore["stats"]["activePlayers"]
    for player in players:
        if (player["teamId"] == home_team_id):
            players_for_home_team.append(player)
        else:
            players_for_visiting_team.append(player)
    
    top_scorers_for_home_team = get_top_scorers(3, players_for_home_team)
    top_scorers_for_visiting_team = get_top_scorers(3, players_for_visiting_team)

    return f"\n{to_scorers_string(top_scorers_for_home_team, home_tri_code)}\n{to_scorers_string(top_scorers_for_visiting_team, visitor_tri_code)}"

def get_top_scorers(num_top_scorers, players):
    return sorted(players, key = lambda player: get_int(player["points"]), reverse = True)[0:num_top_scorers]

def to_scorers_string(scorers, team_tri_code):
    displayString = f"Top scorers for {team_tri_code}:\n"
    scorer_strings = map(lambda scorer: to_scorer_string(scorer), scorers)
    return displayString + "\n".join(map(str, scorer_strings))
    
def to_scorer_string(scorer):
    first_name = scorer["firstName"]
    last_name = scorer["lastName"]
    points = get_int(scorer["points"])
    fgm = get_int(scorer["fgm"])
    fga = get_int(scorer["fga"])
    return f"{first_name} {last_name}: {points} pts - {fgm}/{fga} ({0 if int(fga) == 0 else round(fgm / fga, 2)} fg%)"

def get_int(str_value):
    return 0 if str_value == "" else int(str_value)

def is_game_not_started(game):
    return game["statusNum"] == 1

def is_game_ongoing(game):
    return game["statusNum"] == 2

def is_game_ended(game):
    return game["statusNum"] == 3

def is_higher_scorer(player1, player2):
    return player1["points"] > player2["points"]

def get_game_for_team(all_games, nba_team):
    for game in all_games["games"]:
        if (game["hTeam"]["triCode"] == nba_team.triCode or game["vTeam"]["triCode"] == nba_team.triCode):
            return game
    return None

def get_simplified_game_summary(game): 
    home_team = game["hTeam"]["triCode"]
    home_score = 0 if game["hTeam"]["score"] == "" else game["hTeam"]["score"]
    visitor_team = game["vTeam"]["triCode"]
    visitor_score = 0 if game["vTeam"]["score"] == "" else game["vTeam"]["score"]

    current_period = game["period"]["current"]
    clock = format_clock(game["clock"])
    start_time = to_pacific_date_time(game["startTimeUTC"])
    
    if (is_game_not_started(game)):
        period_display_str = f"Start time: {start_time}"
    elif (is_game_ongoing(game)):
        if (current_period <= 4):
            period_display_str =  f"Quarter {str(current_period)} {clock}"
        else:
            period_display_str = f"OT{str(current_period - 4)} {clock}"
    else:
         period_display_str = "Final"

    return f"{visitor_team} ({visitor_score} pts) vs {home_team} ({home_score} pts) {period_display_str}"

def get_team(team):
    for team_def in teams.team_defs:
        if (team == team_def["city"].lower() or 
            team == team_def["altCityName"].lower() or 
            team == team_def["tricode"].lower() or 
            team == team_def["teamId"].lower() or 
            team == team_def["nickname"].lower() or 
            team == team_def["urlName"].lower() or
            team == team_def["teamShortName"].lower()):
            return NBATeam(team_def)
    return None
        
def lambda_handler(event, context):
    print("Received event: " + str(event))
    # sub + to whitespace
    body = event["Body"].replace("+", " ")
    body = body.replace("%20", " ")
    resp = MessagingResponse()
    resp.message("\n" + process_message(body))

    return str(resp)
