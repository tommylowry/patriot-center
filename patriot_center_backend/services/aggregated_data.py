from patriot_center_backend.services.managers import fetch_starters
from decimal import Decimal


def fetch_aggregated_players(manager, season=None, week=None):
    """
    Fetch aggregated player data for a specific manager.

    Args:
        manager (str): The manager to fetch data for.
        season (int, optional): The season to filter by. Defaults to None.
        week (int, optional): The week to filter by. Defaults to None.

    Returns:
        dict: Aggregated player data with total points, games started, and position.
    """
    raw_dict = fetch_starters(manager, season=season, week=week)
    players_dict_to_return = {}

    if not raw_dict:
        return players_dict_to_return

    for year, weeks in raw_dict.items():
        for week, manager_data in weeks.items():
            for player, player_data in manager_data[manager].items():
                if player == "Total_Points":
                    continue

                if player in players_dict_to_return:
                    _update_player_data(players_dict_to_return, player, player_data)
                else:
                    _initialize_player_data(players_dict_to_return, player, player_data)

    return players_dict_to_return


def fetch_aggregated_managers(player, season=None, week=None):
    """
    Fetch aggregated manager data for a specific player.

    Args:
        player (str): The player to fetch data for.
        season (int, optional): The season to filter by. Defaults to None.
        week (int, optional): The week to filter by. Defaults to None.

    Returns:
        dict: Aggregated manager data with total points, games started, and position.
    """
    raw_dict = fetch_starters(season=season, week=week)
    managers_dict_to_return = {}

    for year, weeks in raw_dict.items():
        for week, managers in weeks.items():
            for manager, manager_data in managers.items():
                if player in manager_data:
                    raw_item = manager_data[player]

                    if manager in managers_dict_to_return:
                        _update_manager_data(managers_dict_to_return, manager, raw_item)
                    else:
                        _initialize_manager_data(managers_dict_to_return, manager, raw_item)

    return managers_dict_to_return


def _update_player_data(players_dict, player, player_data):
    """
    Update the aggregated data for an existing player.

    Args:
        players_dict (dict): The dictionary containing aggregated player data.
        player (str): The player to update.
        player_data (dict): The raw data for the player.
    """
    player_dict_item = players_dict[player]
    player_dict_item['total_points'] += player_data['points']
    player_dict_item['num_games_started'] += 1

    # Round the total points to two decimal places
    player_dict_item["total_points"] = float(
        Decimal(player_dict_item["total_points"]).quantize(Decimal('0.01')).normalize()
    )

    players_dict[player] = player_dict_item


def _initialize_player_data(players_dict, player, player_data):
    """
    Initialize the aggregated data for a new player.

    Args:
        players_dict (dict): The dictionary containing aggregated player data.
        player (str): The player to initialize.
        player_data (dict): The raw data for the player.
    """
    players_dict[player] = {
        "total_points": player_data['points'],
        "num_games_started": 1,
        "position": player_data['position']
    }


def _update_manager_data(managers_dict, manager, raw_item):
    """
    Update the aggregated data for an existing manager.

    Args:
        managers_dict (dict): The dictionary containing aggregated manager data.
        manager (str): The manager to update.
        raw_item (dict): The raw data for the manager.
    """
    manager_dict_item = managers_dict[manager]
    manager_dict_item['total_points'] += raw_item['points']
    manager_dict_item['num_games_started'] += 1

    # Round the total points to two decimal places
    manager_dict_item["total_points"] = float(
        Decimal(manager_dict_item["total_points"]).quantize(Decimal('0.01')).normalize()
    )

    managers_dict[manager] = manager_dict_item


def _initialize_manager_data(managers_dict, manager, raw_item):
    """
    Initialize the aggregated data for a new manager.

    Args:
        managers_dict (dict): The dictionary containing aggregated manager data.
        manager (str): The manager to initialize.
        raw_item (dict): The raw data for the manager.
    """
    managers_dict[manager] = {
        "total_points": raw_item['points'],
        "num_games_started": 1,
        "position": raw_item['position']
    }
