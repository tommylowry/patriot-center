from patriot_center_backend.utils.ffWAR.replacement_score_loader import replacement_score_loader
from patriot_center_backend.utils.ffWAR.reaplacement_average_loader import replacement_average_loader
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

REPLACEMENT_SCORES   = replacement_score_loader()
REPLACEMENT_AVERAGES = replacement_average_loader()
PLAYER_DATA          = load_or_update_starters_cache()

def calculate_ffWAR(manager=None, season=None, week=None):
    weekly_data = PLAYER_DATA[str(season)][str(week)]

    final_scores = []
    players      = {}
    for manager in weekly_data:
        final_scores.append(weekly_data[manager]['Total_Points'])
        for player in weekly_data[manager]:
            
            if player == 'Total_Points':
                continue

            position = weekly_data[manager][player]['position']
            if position in players:
                
                current_position_dict = players[position]
                current_position_dict[player] = weekly_data[manager][player]['points']
                players[position] = current_position_dict

            else:
                players[position] = {player: weekly_data[manager][player]['points']}

    QBs = calculate_QB_WAR(final_scores, players['QB'], season, week)


    print("")




def calculate_QB_WAR(final_scores, players, season, week):
    bye_weeks = REPLACEMENT_SCORES[str(season)][str(week)]['byes']

    replacement_average = 0.0
    if bye_weeks == 0:
        replacement_average = REPLACEMENT_AVERAGES[season][week]['QB'][0]
    elif bye_weeks == 2:
        replacement_average = REPLACEMENT_AVERAGES[season][week]['QB'][1]
    elif bye_weeks == 4:
        replacement_average = REPLACEMENT_AVERAGES[season][week]['QB'][2]
    elif bye_weeks == 6:
        replacement_average = REPLACEMENT_AVERAGES[season][week]['QB'][3]
    else:
        return "bad"
    
    print("")

calculate_ffWAR(season="2019", week="1")