from flask import Flask, jsonify
from constants import LEAGUE_IDS, NAME_TO_MANAGER_USERNAME
import utils
import patriot_center_backend.services.managers

app = Flask(__name__)

@app.route('/api/managers/get_starters', defaults={'year': None, 'manager': None}, methods=['GET'])
@app.route('/api/managers/get_starters/<int:year>', defaults={'manager': None}, methods=['GET'])
@app.route('/api/managers/get_starters/<int:year>/<string:manager>', methods=['GET'])
def get_starters(year, manager):
    
    # Validate year and manager
    if year not in LEAGUE_IDS and year is not None:
        return jsonify({"error": "Year not found"}), 404
    
    if manager not in NAME_TO_MANAGER_USERNAME.keys() and manager is not None:
        return jsonify({"error": "Manager not found"}), 404
    
    # Fetch starters data
    data = patriot_center_backend.services.managers.get_starters(year, manager)

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)