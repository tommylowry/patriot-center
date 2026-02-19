"""Configuration constants for the Patriot Center backend."""

from enum import StrEnum

# Map year to the league ids (Sleeper league IDs for each fantasy season)
LEAGUE_IDS = {
    2019: "399260536505671680",
    2020: "567745628522500096",
    2021: "650026670341861376",
    2022: "784823696450772992",
    2023: "979405891168493568",
    2024: "1113631749025796096",
    2025: "1256401636973101056",
}

# Map usernames to real name for display
USERNAME_TO_REAL_NAME = {
    "aalvaa": "Anthony",
    "bbennick": "Benz",
    "BilliamBlowland": "Billiam",
    "senorpapi": "Christian",
    "codestoppable": "Cody",
    "dpereira7": "Davey",
    "BrownBoyLove": "Dheeraj",
    "jkjackson16": "Jack",
    "Jrazzam": "Jay",
    "lukehellyer": "Luke",
    "mitchwest": "Mitch",
    "owen0010": "Owen",
    "parkdaddy": "Parker",
    "Siemonster": "Sach",
    "samprice18": "Sam",
    "charris34": "Soup",
    "tommylowry": "Tommy",
    "bispity": "Ty",
}

# Invert the MANAGER_USERNAME_TO_REAL_NAME mapping
NAME_TO_MANAGER_USERNAME = {v: k for k, v in USERNAME_TO_REAL_NAME.items()}

# List of user IDs for managers
USER_IDS = [
    "399258572535365632",
    "399261307120963584",
    "338769223406862336",
    "447901687189860352",
    "447903340865515520",
    "447903614824869888",
    "447928129864855552",
    "448188504854228992",
    "448279276198817792",
    "461683800494043136",
    "463021579102580736",
    "730451835554529280",
    "482387309098954752",
    "591687096255700992",
    "607421766062637056",
    "724714182972395520",
    "604420930118172672",
    "982457322809151488",
]

# User ID for Tommy, used as a historical reference
TOMMY_USER_ID = "399258572535365632"
CODY_USER_ID = "482387309098954752"
DAVEY_USER_ID = "607421766062637056"


# Enum for player positions
class Position(StrEnum):
    """Enum for player positions."""

    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"


# Mapping of team IDs to their full names
TEAM_DEFENSE_NAMES = {
    "SEA": {
        "full_name": "Seattle Seahawks",
        "first_name": "Seattle",
        "last_name": "Seahawks",
    },
    "CHI": {
        "full_name": "Chicago Bears",
        "first_name": "Chicago",
        "last_name": "Bears",
    },
    "NE": {
        "full_name": "New England Patriots",
        "first_name": "New England",
        "last_name": "Patriots",
    },
    "DAL": {
        "full_name": "Dallas Cowboys",
        "first_name": "Dallas",
        "last_name": "Cowboys",
    },
    "GB": {
        "full_name": "Green Bay Packers",
        "first_name": "Green Bay",
        "last_name": "Packers",
    },
    "KC": {
        "full_name": "Kansas City Chiefs",
        "first_name": "Kansas City",
        "last_name": "Chiefs",
    },
    "SF": {
        "full_name": "San Francisco 49ers",
        "first_name": "San Francisco",
        "last_name": "49ers",
    },
    "PIT": {
        "full_name": "Pittsburgh Steelers",
        "first_name": "Pittsburgh",
        "last_name": "Steelers",
    },
    "PHI": {
        "full_name": "Philadelphia Eagles",
        "first_name": "Philadelphia",
        "last_name": "Eagles",
    },
    "BUF": {
        "full_name": "Buffalo Bills",
        "first_name": "Buffalo",
        "last_name": "Bills",
    },
    "NYG": {
        "full_name": "New York Giants",
        "first_name": "New York",
        "last_name": "Giants",
    },
    "NYJ": {
        "full_name": "New York Jets",
        "first_name": "New York",
        "last_name": "Jets",
    },
    "MIA": {
        "full_name": "Miami Dolphins",
        "first_name": "Miami",
        "last_name": "Dolphins",
    },
    "MIN": {
        "full_name": "Minnesota Vikings",
        "first_name": "Minnesota",
        "last_name": "Vikings",
    },
    "DEN": {
        "full_name": "Denver Broncos",
        "first_name": "Denver",
        "last_name": "Broncos",
    },
    "CLE": {
        "full_name": "Cleveland Browns",
        "first_name": "Cleveland",
        "last_name": "Browns",
    },
    "CIN": {
        "full_name": "Cincinnati Bengals",
        "first_name": "Cincinnati",
        "last_name": "Bengals",
    },
    "BAL": {
        "full_name": "Baltimore Ravens",
        "first_name": "Baltimore",
        "last_name": "Ravens",
    },
    "LAR": {
        "full_name": "Los Angeles Rams",
        "first_name": "Los Angeles",
        "last_name": "Rams",
    },
    "LAC": {
        "full_name": "Los Angeles Chargers",
        "first_name": "Los Angeles",
        "last_name": "Chargers",
    },
    "SD": {
        "full_name": "Los Angeles Chargers",
        "first_name": "Los Angeles",
        "last_name": "Chargers",
    },
    "ARI": {
        "full_name": "Arizona Cardinals",
        "first_name": "Arizona",
        "last_name": "Cardinals",
    },
    "ATL": {
        "full_name": "Atlanta Falcons",
        "first_name": "Atlanta",
        "last_name": "Falcons",
    },
    "CAR": {
        "full_name": "Carolina Panthers",
        "first_name": "Carolina",
        "last_name": "Panthers",
    },
    "DET": {
        "full_name": "Detroit Lions",
        "first_name": "Detroit",
        "last_name": "Lions",
    },
    "HOU": {
        "full_name": "Houston Texans",
        "first_name": "Houston",
        "last_name": "Texans",
    },
    "IND": {
        "full_name": "Indianapolis Colts",
        "first_name": "Indianapolis",
        "last_name": "Colts",
    },
    "JAX": {
        "full_name": "Jacksonville Jaguars",
        "first_name": "Jacksonville",
        "last_name": "Jaguars",
    },
    "LV": {
        "full_name": "Las Vegas Raiders",
        "first_name": "Las Vegas",
        "last_name": "Raiders",
    },
    "OAK": {
        "full_name": "Las Vegas Raiders",
        "first_name": "Las Vegas",
        "last_name": "Raiders",
    },
    "NO": {
        "full_name": "New Orleans Saints",
        "first_name": "New Orleans",
        "last_name": "Saints",
    },
    "TB": {
        "full_name": "Tampa Bay Buccaneers",
        "first_name": "Tampa Bay",
        "last_name": "Buccaneers",
    },
    "TEN": {
        "full_name": "Tennessee Titans",
        "first_name": "Tennessee",
        "last_name": "Titans",
    },
    "WAS": {
        "full_name": "Washington Commanders",
        "first_name": "Washington",
        "last_name": "Commanders",
    },
}
