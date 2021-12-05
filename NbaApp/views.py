from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse
from basketball_reference_scraper.seasons import get_schedule, get_standings
from basketball_reference_scraper.box_scores import get_box_scores
from nba_api.stats.endpoints import teamdashboardbyteamperformance
from pathlib import Path
from NbaApp.models import Games
from datetime import datetime;
from bs4 import BeautifulSoup
from NbaApp.serializers import GameSerializer
import pandas as pd
import os
import pickle
from datetime import datetime;
from bs4 import BeautifulSoup
import requests
import time
from pathlib import Path

import json


from NbaApp.models import Games
from NbaApp.serializers import GameSerializer



@csrf_exempt
def gameApi(request, gameId=0):
    if request.method == 'GET':
        games = Games.objects.all()
        games_serializer = GameSerializer(games, many=True)
        return JsonResponse(games_serializer.data, safe=False)
    elif request.method == 'POST':
        game_data = JSONParser().parse(request)
        game_serializer = GameSerializer(data=game_data)
        if game_serializer.is_valid():
            game_serializer.save()
            return JsonResponse("Added Game successfully.", safe=False)
        return JsonResponse("Failed to add Game.", safe=False)
    elif request.method == 'PUT':
        game_data = JSONParser().parse(request)
        game = Games.objects.get(GameId=game_data['GameId'])
        game_serializer = GameSerializer(game, data=game_data)
        if game_serializer.is_valid():
            game_serializer.save()
            return JsonResponse("Updated Game successfully.", safe=False)
        return JsonResponse("Failed to update Game.", safe=False)
    elif request.method == 'DELETE':
        game = Games.objects.get(GameId=gameId)
        game.delete()
        return JsonResponse("Deleted Game successfully", safe=False)


@csrf_exempt
def standingApi(request):
    if request.method == 'GET':
        data = get_standings()
        data["EASTERN_CONF"]['DIV'] = 'east'
        data["WESTERN_CONF"]['DIV'] = 'west'
        res = pd.concat([data["EASTERN_CONF"], data["WESTERN_CONF"]], ignore_index=True)
        res = res.rename(columns={"W/L%": "WL", "PS/G": "PSG", "PA/G": "PAG"})
        return JsonResponse(res.to_json(), safe=False)


@csrf_exempt
def scheduleApi(request):
    if request.method == 'GET':
        data = get_schedule(2022, playoffs=False)
        return JsonResponse(data.to_json(date_format='iso'), safe=False)


@csrf_exempt
def boxScoreApi(request, date, team1, team2):
    if request.method == 'GET':
        data = get_box_scores(date, team1, team2, period='GAME', stat_type='BASIC')
        data[team1]['TEAM'] = team1
        data[team2]['TEAM'] = team2
        res = pd.concat([data[team1], data[team2]], ignore_index=True)
        res = res.rename(columns={"FG%": "FGP", "3P": "threeP", "3PA": "threePA", "3P%": "threePP", "+/-": "plusMinus"})
        return JsonResponse(res.to_json(), safe=False)

@csrf_exempt
def predictionApi(request, scheduleId=0):
    if request.method == 'GET':
        data = get_schedule(2022, playoffs=False)
        today = datetime.today().strftime('%Y-%m-%d')
        gamesToday = data.loc[(data['DATE'] == today )]
        gamesToday.reset_index(drop=True, inplace=True)
        predData = getStats(gamesToday.at[0,"HOME"],gamesToday.at[0,"VISITOR"]) 
        for index,row in gamesToday.iterrows():
            if index > 0 :
                predToAppend = getStats(gamesToday.at[index,"HOME"],gamesToday.at[index,"VISITOR"])
                time.sleep(1)
                predData=predData.append(predToAppend)
        predData.reset_index(drop=True, inplace=True)
        y = predData.to_json()
        return JsonResponse(y, safe=False)
    


def getStats(team1,team2):

    path = os.path.dirname(os.path.dirname(os.getcwd()))
    path = path+"/CSI4900-Project/NBA-Vision/src/assets/ML"
    template = Path(path+'/template.csv')

    team1ids=normalizedName(team1)
    team2ids=normalizedName(team2)

    team1Stats = teamdashboardbyteamperformance.TeamDashboardByTeamPerformance(team1ids[1],per_mode_detailed='PerGame')
    team1Stats = team1Stats.overall_team_dashboard.get_data_frame()
    team1Stats.reset_index(drop=True, inplace=True)

    team2Stats = teamdashboardbyteamperformance.TeamDashboardByTeamPerformance(team2ids[1],per_mode_detailed='PerGame')
    team2Stats = team2Stats.overall_team_dashboard.get_data_frame()
    team2Stats.reset_index(drop=True, inplace=True)

   
    eloAndDef1 = getElo(team1)

    eloAndDef2 = getElo(team2)

    combinedStats = pd.read_csv(template)

    combinedStats.at[0,'team'] = team1ids[0]
    combinedStats.at[0,'FGM'] = team1Stats.at[0,'FGM']
    combinedStats.at[0,'FGA'] = team1Stats.at[0,'FGA']
    combinedStats.at[0,'TPM'] = team1Stats.at[0,'FG3M']
    combinedStats.at[0,'TPA'] = team1Stats.at[0,'FG3A']
    combinedStats.at[0,'FTM'] = team1Stats.at[0,'FTM']
    combinedStats.at[0,'FTA'] = team1Stats.at[0,'FTA']
    combinedStats.at[0,'OR'] = team1Stats.at[0,'OREB']
    combinedStats.at[0,'DR'] = team1Stats.at[0,'DREB']
    combinedStats.at[0,'AS'] = team1Stats.at[0,'AST']
    combinedStats.at[0,'STL'] = team1Stats.at[0,'STL']
    combinedStats.at[0,'BLK'] = team1Stats.at[0,'BLK']
    combinedStats.at[0,'TO'] = team1Stats.at[0,'TOV']
    combinedStats.at[0,'PF'] = team1Stats.at[0,'PF']
    combinedStats.at[0,'LOC'] = 1
    combinedStats.at[0,'OPP'] = team2ids[0]
    combinedStats.at[0,'ELO'] = eloAndDef1[0]
    combinedStats.at[0,'DEF'] = float(eloAndDef1[1])/(team1Stats.at[0,'FGA']-team1Stats.at[0,'OREB'] + team1Stats.at[0,'TOV'] + (0.4*team1Stats.at[0,'FTA']))
    combinedStats.at[0,'team2'] = team2ids[0]
    combinedStats.at[0,'FGM2'] = team2Stats.at[0,'FGM']
    combinedStats.at[0,'FGA2'] = team2Stats.at[0,'FGA']
    combinedStats.at[0,'TPM2'] = team2Stats.at[0,'FG3M']
    combinedStats.at[0,'TPA2'] = team2Stats.at[0,'FG3A']
    combinedStats.at[0,'FTM2'] = team2Stats.at[0,'FTM']
    combinedStats.at[0,'FTA2'] = team2Stats.at[0,'FTA']
    combinedStats.at[0,'OR2'] = team2Stats.at[0,'OREB']
    combinedStats.at[0,'DR2'] = team2Stats.at[0,'DREB']
    combinedStats.at[0,'AS2'] = team2Stats.at[0,'AST']
    combinedStats.at[0,'STL2'] = team2Stats.at[0,'STL']
    combinedStats.at[0,'BLK2'] = team2Stats.at[0,'BLK']
    combinedStats.at[0,'TO2'] = team2Stats.at[0,'TOV']
    combinedStats.at[0,'PF2'] = team2Stats.at[0,'PF']
    combinedStats.at[0,'LOC2'] = 0
    combinedStats.at[0,'OPP2'] = team1ids[0]
    combinedStats.at[0,'ELO2'] = eloAndDef2[0]
    combinedStats.at[0,'DEF2'] = float(eloAndDef2[1])/(team2Stats.at[0,'FGA']-team2Stats.at[0,'OREB'] + team2Stats.at[0,'TOV'] + (0.4*team2Stats.at[0,'FTA']))



    combinedStats.assign(outcome="")
    
    combinedStats.at[0,"OUTCOME"]=predict(combinedStats)

    return combinedStats




def predict (combinedStats):

    with open(model, 'rb') as file: 
        Pickled_LR_Model = pickle.load(file)

    return Pickled_LR_Model.predict(combinedStats)[0]

path = os.path.dirname(os.path.dirname(os.getcwd()))
path = path+"/CSI4900-Project/NBA-Vision/src/assets/ML"
model = Path( path +'/model.pkl')

URLelo = "https://projects.fivethirtyeight.com/2022-nba-predictions/"
pageElo = requests.get(URLelo)
soupElo = BeautifulSoup(pageElo.content, "html.parser")

URLdef = "https://www.teamrankings.com/nba/stat/opponent-points-per-game"
pageDef = requests.get(URLdef)
soupDef = BeautifulSoup(pageDef.content, "html.parser")

rows = soupDef.find_all("tr")

oppPointsList = []
for tr in rows[1:]:
    tds = tr.find_all('td')
    oppPointsList.append((tds[1].text))
    oppPointsList.append((tds[2].text))



def getElo(teamName):

    tName=""
    dName=""

    if teamName =="Atlanta Hawks":
        tName="ATL"
        dName='Atlanta'
    elif teamName =="Boston Celtics":
        tName="BOS"
        dName='Boston'
    elif teamName =="Cleveland Cavaliers":
        tName="CLE"
        dName='Cleveland'
    elif teamName =="New Orleans Pelicans":
        tName="NO"
        dName='New Orleans'
    elif teamName =="Chicago Bulls":
        tName="CHI"
        dName='Chicago'
    elif teamName =="Dallas Mavericks":
        tName=" DAL"
        dName='Dallas'
    elif teamName == "Denver Nuggets":
        tName="DEN"
        dName='Denver'
    elif teamName == "Golden State Warriors":
        tName="GS"
        dName='Golden State'
    elif teamName == "Houston Rockets":
        tName="HOU"
        dName='Houston'
    elif teamName == "Los Angeles Clippers":
        tName="LAC"
        dName='LA Clippers'
    elif teamName == "Los Angeles Lakers":
        tName="LAL"
        dName='LA Lakers'
    elif teamName == "Miami Heat":
        tName="MIA"
        dName='Miami'
    elif teamName == "Milwaukee Bucks":
        tName="MIL"
        dName='Milwaukee'
    elif teamName ==  "Minnesota Timberwolves":
        tName="MIN"
        dName='Minnesota'
    elif teamName ==  "Brooklyn Nets":
        tName="BKN"
        dName='Brooklyn'
    elif teamName ==  "New York Knicks":
        tName="NY"
        dName='New York'
    elif teamName ==  "Orlando Magic":
        tName="ORL"
        dName='Orlando'
    elif teamName ==  "Indiana Pacers":
        tName="IND"
        dName='Indiana'
    elif teamName ==  "Philadelphia 76ers":
        tName="PHI"
        dName='Philadelphia'
    elif teamName ==  "Phoenix Suns":
        tName="PHX"
        dName='Phoenix'
    elif teamName ==  "Portland Trail Blazers":
        tName="POR"
        dName='Portland'
    elif teamName ==  "Sacramento Kings":
        tName="SAC"
        dName='Sacramento'
    elif teamName ==  "San Antonio Spurs":
        tName="SA"
        dName='San Antonio'
    elif teamName ==  "Oklahoma City Thunder":
        tName="OKC"
        dName='Okla City'
    elif teamName ==  "Toronto Raptors":
        tName="TOR"
        dName='Toronto'
    elif teamName ==  "Utah Jazz":
        tName="UTA"
        dName='Utah'
    elif teamName ==  "Memphis Grizzlies":
        tName="MEM"
        dName='Memphis'
    elif teamName ==  "Washington Wizards":
        tName="WSH"
        dName='Washington'
    elif teamName ==  "Detroit Pistons":
        tName="DET"
        dName='Detroit'
    elif teamName == "Charlotte Hornets":
        tName="CHA"
        dName='Charlotte'


    opponentPoints=oppPointsList[oppPointsList.index(dName)+1]
    team = 'tr[data-team=' + tName +"]"
    items=soupElo.select(team)
    elo = items[0].find("td",class_="num elo carmelo-current").string
    return [int(elo),opponentPoints]


def normalizedName(teamName):
        if teamName =="Atlanta Hawks":
            return [0,1610612737]
        elif teamName =="Boston Celtics":
            return [1,1610612738]
        elif teamName =="Cleveland Cavaliers":
            return [5,1610612739]
        elif teamName =="New Orleans Pelicans":
            return [18,1610612740]
        elif teamName =="Chicago Bulls":
            return [4,1610612741]
        elif teamName =="Dallas Mavericks":
            return [6,1610612742]
        elif teamName == "Denver Nuggets":
            return [7,1610612743]
        elif teamName == "Golden State Warriors":
            return [9,1610612744]
        elif teamName == "Houston Rockets":
            return [10,1610612745]
        elif teamName == "Los Angeles Clippers":
            return [12,1610612746]
        elif teamName == "Los Angeles Lakers":
            return [13,1610612747]
        elif teamName == "Miami Heat":
            return [15,1610612748]
        elif teamName == "Milwaukee Bucks":
            return [16,1610612749]
        elif teamName ==  "Minnesota Timberwolves":
            return [17,1610612750]
        elif teamName ==  "Brooklyn Nets":
            return [2,1610612751]
        elif teamName ==  "New York Knicks":
            return [19,1610612752]
        elif teamName ==  "Orlando Magic":
            return [21,1610612753]
        elif teamName ==  "Indiana Pacers":
            return [11,1610612754]
        elif teamName ==  "Philadelphia 76ers":
            return [22,1610612755]
        elif teamName ==  "Phoenix Suns":
            return [23,1610612756]
        elif teamName ==  "Portland Trail Blazers":
            return [24,1610612757]
        elif teamName ==  "Sacramento Kings":
            return [25,1610612758]
        elif teamName ==  "San Antonio Spurs":
            return [26,1610612759]
        elif teamName ==  "Oklahoma City Thunder":
            return [20,1610612760]
        elif teamName ==  "Toronto Raptors":
            return [27,1610612761]
        elif teamName ==  "Utah Jazz":
            return [28,1610612762]
        elif teamName ==  "Memphis Grizzlies":
            return [14,1610612763]
        elif teamName ==  "Washington Wizards":
            return [29,1610612764]
        elif teamName ==  "Detroit Pistons":
            return [8,1610612765]
        elif teamName == "Charlotte Hornets":
            return [3,1610612766]


