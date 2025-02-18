
from datetime import datetime
from core.haversine import haversine


class TugState:
    DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

    def __init__(self, ship_data) -> None:
        self.ship_data = ship_data
        self.timestamps = sorted(
            set(entry["navigation"]["time"] for entry in ship_data))

    def get_ship_positions_at_time(self, time_stamp: str) -> list:
        """At an individual point in time, get the positions of all ships

        Args:
            time_stamp: Time stamp in string format

        Returns:
            : List of ships at the given time
        """
        return [
            entry for entry in self.ship_data
            if entry["navigation"]["time"] == time_stamp
        ]

    def get_all_last_vessel_positions(
            self, timestamp: str) -> list:
        res = {}
        timestamp_dt = datetime.strptime(timestamp,
                                         self.DATE_TIME_FORMAT)

        for tug in self.ship_data:
            if tug["navigation"]["status"] != "moored":
                tug_timestamp = datetime.strptime(
                    tug["navigation"]["time"],
                    self.DATE_TIME_FORMAT
                )
                current = res.get(tug["vessel"]["name"])
                if (
                    timestamp_dt >= tug_timestamp and
                    (
                        current is None or
                        datetime.strptime(
                            current["navigation"]["time"],
                            self.DATE_TIME_FORMAT
                        ) < tug_timestamp
                    )
                ):
                    res[tug["vessel"]["name"]] = tug

        tugs = []
        vessels = []
        for ves in res.values():
            if ves["vessel"]["type"] == "tug":
                tugs.append(ves)
            else:
                vessels.append(ves)
        return {"tugs": tugs, "vessels": vessels}

    def get_active_tugboats_at_time(self, timestamp: str) -> list:
        """Get all active tugboats and the vessels they are tugging
        at a specific time

        Args:
        time_stamp: Time stamp in string format

        Returns:
            : List of tugboats and corresponding vessels at the given time
        """
        active_tugs = []
        active_tugs_position: dict = self._get_active_last_position(
            "tug", timestamp)
        active_vessels_position: dict = self._get_active_last_position(
            "vessel", timestamp)

        if active_tugs_position:
            for tug in active_tugs_position.values():
                for vessel in active_vessels_position.values():
                    if (
                        self.vessel_is_being_tugged(tug, vessel=vessel)
                    ):
                        active_tugs.append({
                            "tug_name": tug["vessel"]["name"],
                            "attached_vessel": vessel["vessel"]["name"]
                        })
        return active_tugs

    def vessel_is_being_tugged(self, tug: dict, vessel: dict) -> bool:
        tug_last_seen = datetime.strptime(
            tug["navigation"]["time"], self.DATE_TIME_FORMAT
        )
        vessel_last_seen = datetime.strptime(
            vessel["navigation"]["time"], self.DATE_TIME_FORMAT
        )
        diff = (tug_last_seen - vessel_last_seen).total_seconds()

        if (
            abs(diff/3600) < 1 and
            tug["navigation"]["speed"] > 0.1 and
            vessel["navigation"]["speed"] > 0.1
        ):
            tug_lat = tug["navigation"]["location"]["lat"]
            tug_lon = tug["navigation"]["location"]["long"]
            vessel_lat = vessel["navigation"]["location"]["lat"]
            vessel_lon = vessel["navigation"]["location"]["long"]

            distance = haversine(tug_lat, tug_lon, vessel_lat, vessel_lon)
            return distance <= 0.3, distance
        return False, 0

    def _get_active_last_position(self, type: str, timestamp: str) -> list:
        tug_boats = {}
        for ship in self.ship_data:
            if self._is_active(type, ship, timestamp):
                tug = tug_boats.get(ship["vessel"]["name"])
                tug_last_seen = (datetime.strptime(
                    tug["navigation"]["time"], self.DATE_TIME_FORMAT)
                    if tug is not None else None
                )
                ship_time = datetime.strptime(ship["navigation"]["time"],
                                              self.DATE_TIME_FORMAT)

                if (
                    tug is None or
                    (tug_last_seen < ship_time)
                ):
                    tug_boats[ship["vessel"]["name"]] = ship
        return tug_boats

    def _is_active(self, _type: str, ship: dict, timestamp: str) -> bool:
        if _type == "tug":
            return self._is_active_tug_boat(ship, timestamp)
        else:
            return self._is_active_vessel(ship, timestamp)

    def _is_active_vessel(self, ship: dict, timestamp: str) -> bool:
        requested_time = datetime.strptime(timestamp, self.DATE_TIME_FORMAT)
        ship_observed_time = datetime.strptime(
            ship["navigation"]["time"], self.DATE_TIME_FORMAT)
        return (
            ship["vessel"]["type"] != "tug"
            and requested_time >= ship_observed_time
        )

    def _is_active_tug_boat(self, ship: dict, timestamp: str) -> bool:
        """Checks if bboat is an active tugboat

        Args:
            ship: ship details
            time_stamp: Time in question

        Returns:
            : Boolean whether boat is active boat
        """
        requested_time = datetime.strptime(timestamp, self.DATE_TIME_FORMAT)
        ship_observed_time = datetime.strptime(
            ship["navigation"]["time"], self.DATE_TIME_FORMAT)
        return (
            ship["vessel"]["type"] == "tug"
            and requested_time >= ship_observed_time
            and ship["navigation"]["speed"] > 0.0
        )
