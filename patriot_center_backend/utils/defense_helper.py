"""Helper functions for generating synthetic team defense entries."""

from patriot_center_backend.constants import TEAM_DEFENSE_NAMES, Position


def get_defense_entries() -> dict[str, dict[str, str]]:
    """Returns a dictionary of synthetic team defense entries.

    Returns:
        A dictionary where keys are team abbreviations and values are
        dictionaries containing the team's full name, first name, last name,
        and position.
    """
    output = {}

    for defense in TEAM_DEFENSE_NAMES:
        output[defense] = {
            "active": True,
            "position": Position.DEF,
            "full_name": TEAM_DEFENSE_NAMES[defense]["full_name"],
            "first_name": TEAM_DEFENSE_NAMES[defense]["first_name"],
            "last_name": TEAM_DEFENSE_NAMES[defense]["last_name"],
            "sport": "nfl",
            "team": defense,
            "player_id": defense,
            "fantasy_positions": [Position.DEF],
            "injury_status": None,
        }

    return output
