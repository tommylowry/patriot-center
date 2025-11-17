from patriot_center_backend.utils.replacement_score_loader import load_or_update_replacement_score_cache
from patriot_center_backend.utils.starters_loader import load_or_update_starters_cache

REPLACEMENT_SCORES   = load_or_update_replacement_score_cache()
PLAYER_DATA          = load_or_update_starters_cache()

def ffWAR(manager=None, season=None, week=None):
    weekly_data = PLAYER_DATA[str(season)][str(week)]

    players      = {"QB":  {},
                    "RB":  {},
                    "WR":  {},
                    "TE":  {},
                    "K":   {},
                    "DEF": {}
                    }
    
    for manager in weekly_data:
        for position in players:
            
            old_players_position = players[position]
            old_players_position[manager] = {'total_points': weekly_data[manager]['Total_Points'], 'players': {}}
            players[position] = old_players_position
            
        for player in weekly_data[manager]:
            if player == 'Total_Points':
                continue

            position = weekly_data[manager][player]['position']
            players[position][manager]['players'][player] = weekly_data[manager][player]['points']
                
    ffWAR = calculate_ffWAR(players, season, week)


    return ffWAR




def calculate_ffWAR(scores, season, week):
    ffWAR_results = {}
    for position in scores:
        if position not in ['QB', 'RB', 'WR', 'TE']:
            continue
        calculated_ffWAR = calculate_ffWAR_position(scores[position], season, week, position)
        for player in calculated_ffWAR:
            ffWAR_results[player] = calculated_ffWAR[player]
    return ffWAR_results

def calculate_ffWAR_position(scores, season, week, position):
    
    key = f"{position}_3yr_avg"
    replacement_average = REPLACEMENT_SCORES[str(season)][str(week)][key]
    
    
    # get score minus the average
    num_players = 0
    total_position_score = 0.0
    for manager in scores:
        num_players += len(scores[manager]['players'])
        for player in scores[manager]['players']:
            total_position_score += scores[manager]['players'][player]
    
    average_player_score_this_week = total_position_score / num_players


    for manager in scores:

        player_total_for_manager = 0.0
        for player in scores[manager]['players']:
            player_total_for_manager += scores[manager]['players'][player]
        
        player_average_for_manager = player_total_for_manager / len(scores[manager]['players'])

        # total_minus_position = total_points - player_average_for_manager
        scores[manager]['total_minus_position'] = scores[manager]["total_points"] - player_average_for_manager

        # weighted_total_score = total_points - manager_average + position average
        scores[manager]['weighted_total_score'] = scores[manager]["total_points"] - player_average_for_manager  + average_player_score_this_week

    ffWAR_position = {}
    for real_manager in scores:
        for player in scores[real_manager]['players']:
            num_simulated_games = 0
            num_wins   = 0
            player_score = scores[real_manager]['players'][player]

            for manager_playing in scores:
                for manager_opposing in scores:
                    if manager_playing == manager_opposing:
                        continue

                    # score of the opponent
                    simulated_opponent_score = scores[manager_opposing]['weighted_total_score']

                    # score if player was on manager_playing's lineup
                    simulated_player_score = scores[manager_playing]['total_minus_position'] + player_score

                    # score if replacement player was on manager_playing's lineup
                    simulated_replacement_score = scores[manager_playing]['total_minus_position'] + replacement_average
                    
                    # win if player wouldve won and replacement wouldve lost
                    if (simulated_player_score > simulated_opponent_score) and (simulated_replacement_score < simulated_opponent_score):
                        num_wins += 1
                    # loss if player wouldve lost and replacement wouldve won
                    if (simulated_player_score < simulated_opponent_score) and (simulated_replacement_score > simulated_opponent_score):
                        num_wins -= 1
                    
                    num_simulated_games += 1
            
            ffWAR_score = round(num_wins / num_simulated_games, 3)

            ffWAR_position[player] = {
                'ffWAR': ffWAR_score,
                'manager': real_manager,
                'position': position
            }
    
    return ffWAR_position


di = ffWAR(season="2025", week="10")
print("")