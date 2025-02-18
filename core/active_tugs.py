import json
from datetime import datetime
from core.tug_state import TugState


class ActiveTugs:
    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    def __init__(self, tug_state: TugState):
        self.tug_state = tug_state
        self.data = self._get_all_vessels_by_type()
        self.tug_timestamps = sorted(
            set(entry["navigation"]["time"] for entry in self.data["tugs"]))

        with open("data/active-tugs.json", "r") as file:
            self.active_tugs = json.load(file)
            self.active_tug_timestamps = sorted(self.active_tugs.keys())

    def get_active_tugboats_at_time(self, timestamp: str):
        closest = min(self.active_tug_timestamps,
                      key=lambda d: abs(
                          datetime.strptime(timestamp, self.DATE_TIME_FORMAT) -
                          datetime.strptime(d, self.DATE_TIME_FORMAT)
                          ))

        time_dt = datetime.strptime(timestamp, self.DATE_TIME_FORMAT)
        closest_dt = datetime.strptime(closest, self.DATE_TIME_FORMAT)
        diff = abs(time_dt-closest_dt).total_seconds()
        if (diff < 15*60):
            return self.active_tugs[closest]

        return []

    def list_active_tugs(self):
        active_tugs = {}
        for time in self.tug_timestamps:
            positions = self.tug_state.get_all_last_vessel_positions(time)
            for tug in positions["tugs"]:
                for vessel in positions["vessels"]:
                    tugged, dist = self.tug_state.vessel_is_being_tugged(
                        tug, vessel
                    )
                    if tugged:
                        active = active_tugs.get(time, {})
                        vessel_state = active.get(vessel["vessel"]["name"], {})
                        tugs = active.get("tugs", [])
                        tugs.append({"dist": dist, "tug": tug})
                        vessel_state["state"] = vessel
                        vessel_state["tugs"] = tugs
                        active[vessel["vessel"]["name"]] = vessel_state
                        active_tugs[time] = active

        with open("data/active-tugs.json", "w") as file:
            json.dump(active_tugs, file)

    def is_active_tug_at_timestamp(self, tug, vessel, timestamp: str):
        tug_time = datetime.strptime(
            tug["navigation"]["time"], self.DATE_TIME_FORMAT)
        vessel_time = datetime.strptime(
            vessel["navigation"]["time"], self.DATE_TIME_FORMAT)

        if abs(tug_time - vessel_time) < 3600:
            return self.tug_state._vessel_is_being_tugged(
                tug, vessel
            )
        return False

    def _get_all_vessels_by_type(self):
        tugs = []
        vessels = []

        for entry in self.tug_state.ship_data:
            if entry["vessel"]["type"] == "tug":
                tugs.append(entry)
            else:
                vessels.append(entry)
        return {"tugs": tugs, "vessels": vessels}


if __name__ == "__main__":
    with open("data/tugs.json", "r") as file:
        ship_data = json.load(file)
        tug_singleton = TugState(ship_data)
        active_tugs = ActiveTugs(tug_singleton)
        print(
            active_tugs.get_active_tugboats_at_time("2021-04-08T00:19:00+00:00")
        )
