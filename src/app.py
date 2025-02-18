from flask import Flask, render_template, jsonify, request
import json
from core.tug_state import TugState
from core.active_tugs import ActiveTugs

app = Flask(__name__)

# Load ship data once
with open("data/tugs.json", "r") as file:
    ship_data = json.load(file)
    tug_singleton = TugState(ship_data)
    active_tugs = ActiveTugs(tug_singleton)


# Extract unique timestamps from the data
timestamps = sorted(set(entry["navigation"]["time"] for entry in ship_data))


@app.route("/")
def index():
    return render_template("index.html", timestamps=timestamps)


@app.route("/ship_data")
def get_ship_data():
    """Returns vessel positions for the requested timestamp."""
    requested_time = request.args.get("time")
    if not requested_time:
        return jsonify([])

    filtered_data = tug_singleton.get_all_last_vessel_positions(
        requested_time
    )
    res = []
    [res.extend(item) for item in filtered_data.values()]
    return jsonify(res)


@app.route('/active_tugboats', methods=['GET'])
def get_active_tugboats():
    current_time = request.args.get('time')
    tugs = active_tugs.get_active_tugboats_at_time(current_time)
    return jsonify(tugs)


@app.route("/timestamps")
def get_timestamps():
    """Returns available timestamps for the slider."""
    return jsonify(timestamps)


if __name__ == "__main__":
    app.run(debug=True)
