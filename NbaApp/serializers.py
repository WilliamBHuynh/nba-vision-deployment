from rest_framework import serializers
from NbaApp.models import Games
from NbaApp.models import Predictions


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Games
        fields = ('GameId',
                  'HomeTeamName',
                  'AwayTeamName',
                  'HomeTeamPts',
                   'AwayTeamPts',
                  'Date')


class PredSerializer(serializers.ModelSerializer):
    class Meta:
        model = Predictions
        fields = ('team',
                  'FGM',
                  'FGA',
                  'TPM',
                  'TPA',
                  'FTM',
                  'FTA',
                  'OR',
                  'DR',
                  'AS',
                  'STL',
                  'BLK',
                  'TO',
                  'PF',
                  'LOC',
                  'OPP',
                  'ELO',
                  'DEF',
                  'team2',
                  'FGM2',
                  'FGA2',
                  'TPM2',
                  'TPA2',
                  'FTM2',
                  'FTA2',
                  'OR2',
                  'DR2',
                  'AS2',
                  'STL2',
                  'BLK2',
                  'TO2',
                  'PF2',
                  'LOC2',
                  'OPP2',
                  'ELO2',
                  'DEF2',
                  'OUTCOME')

