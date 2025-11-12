import patriot_center_backend.constants as consts
from patriot_center_backend.utils.sleeper_api_handler import fetch_sleeper_data

def get_starters(year=None, manager=None):

    # If year is None, fetch for all years
    if year is None:
        data = {}
        for yr in consts.LEAGUE_IDS.keys():
            data[yr] = get_starters(yr)
        return data
    
    # Fetch league ID for the specified year
    league_id = consts.LEAGUE_IDS[year]
    
   
    if manager is None:
        
        # Fetch managers for the year specified
        sleeper_response_users = fetch_sleeper_data(f"league/{league_id}/users")
        if sleeper_response_users[1] != 200:
            return sleeper_response_users
        
        print("Here")

    return {}, 200

print(get_starters())