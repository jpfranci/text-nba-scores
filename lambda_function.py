from twilio.twiml.messaging_response import Message, MessagingResponse
import datetime
import json
import team_defs as teams
import pytz
import requests

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
        return get_score(body[4:])
    elif (body.startswith("scores")):
        return get_score(body[5:])
    else:
        return get_score(body)

def get_today_date():
    today = datetime.datetime.now(pytz.timezone('US/Pacific'))
    return str(today.strftime("%Y%m%d"))

def get_score(team_str):
    nba_team = get_team(team_str)
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
    print("not implemented yet")

def get_simplified_game_summary(game): 
    home_team = game["hTeam"]["triCode"]
    home_score = 0 if game["hTeam"]["score"] == "" else game["hTeam"]["score"]
    visitor_team = game["vTeam"]["triCode"]
    visitor_score = 0 if game["vTeam"]["score"] == "" else game["vTeam"]["score"]

    current_period = game["period"]["current"]
    clock = str(game["clock"])
    start_time = game["startTimeEastern"]

    if (current_period == 0):
        period_display_str = f"Start time: {start_time}"
    else:
        if (clock == ""):
            period_display_str = "Final"
        else:
            if (current_period <= 4):
                period_display_str =  f"Quarter {str(current_period)} {clock}"
            else:
                period_display_str = f"OT{str(current_period - 4)} {clock}"
    
    return f"{visitor_team} ({visitor_score}) vs {home_team} ({home_score}) {period_display_str}"
        
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
    body = event["Body"]
    resp = MessagingResponse()
    resp.message("\n" + process_message(body))

    return str(resp)