from pathlib import Path
from typing import Dict
import yaml 

def _load_scoring_settings() -> Dict[str, float]:
    scoring_path = Path.cwd() / "config" / "scoring_settings.yml"
    with scoring_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    fail_safe_key = "not_found"
    sleeper_api_value = {
        # Passing
        "pass_yd":   data.get("passing_yards", fail_safe_key),
        "pass_td":   data.get("passing_td", fail_safe_key),
        "pass_2pt":  data.get("passing_2pt_conversion", fail_safe_key),
        "pass_int":  data.get("pass_interception", fail_safe_key),

        # Rushing
        "rush_yd":  data.get("rushing_yards", fail_safe_key),
        "rush_td":  data.get("rushing_td", fail_safe_key),
        "rush_2pt": data.get("rushing_2pt_conversion", fail_safe_key),

        # Receiving
        "rec":     data.get("reception", fail_safe_key),
        "rec_yd":  data.get("receiving_yards", fail_safe_key),
        "rec_td":  data.get("receiving_td", fail_safe_key),
        "rec_2pt": data.get("receiving_2pt_conversion", fail_safe_key),

        # Kicking
        "fgm_0_19":    data.get("fg_made_0-19", fail_safe_key),
        "fgm_20_29":   data.get("fg_made_20-29", fail_safe_key),
        "fgm_30_39":   data.get("fg_made_30-39", fail_safe_key),
        "fgm_40_49":   data.get("fg_made_40-49", fail_safe_key),
        "fgm_50p":     data.get("fg_made_50+", fail_safe_key),
        "xpm":         data.get("pat_made", fail_safe_key),

        "fgmiss_0_19":  data.get("fg_missed_0-19", fail_safe_key),
        "fgmiss_20_29": data.get("fg_missed_20-29", fail_safe_key),
        "fgmiss_30_39": data.get("fg_missed_30-39", fail_safe_key),
        "fgmiss_40_49": data.get("fg_missed_40-49", fail_safe_key),
        "fgmiss_50p":   data.get("fg_missed_50+", fail_safe_key),
        "xpmiss":       data.get("pat_missed", fail_safe_key),

        # Team Defense
        "def_td":         data.get("defense_td", fail_safe_key),
        "sack":           data.get("sacks", fail_safe_key),
        "int":            data.get("interceptions", fail_safe_key),
        "fum_rec":        data.get("fumble_recovery", fail_safe_key),
        "safe":           data.get("safeties", fail_safe_key),
        "ff":             data.get("fumble_forced", fail_safe_key),
        "blk_kick":       data.get("blocked_kick", fail_safe_key),

        "def_st_td":      data.get("special_teams_td", fail_safe_key),
        "def_st_ff":      data.get("special_teams_forced_fumble", fail_safe_key),
        "def_st_fum_rec": data.get("special_teams_fumble_recovery", fail_safe_key),

        # Special Teams Player
        "st_td":      data.get("special_teams_player_td", fail_safe_key),
        "st_ff":      data.get("special_teams_player_forced_fumble", fail_safe_key),
        "st_fum_rec": data.get("special_teams_player_fumble_recovery", fail_safe_key),

        # Misc
        "fum":        data.get("fumble", fail_safe_key),
        "fum_lost":   data.get("fumble_lost", fail_safe_key),
        "fum_rec_td": data.get("fumble_recovery_td", fail_safe_key)
    }
    return sleeper_api_value

def calculate_player_score(player_data: Dict[str, float]) -> float:
    
    scoring_settings = _load_scoring_settings()

    total_score = 0.0
    for stat_key, stat_value in player_data.items():
        if stat_key in scoring_settings:
            points_per_unit = scoring_settings[stat_key]
            total_score += stat_value * points_per_unit
    return total_score