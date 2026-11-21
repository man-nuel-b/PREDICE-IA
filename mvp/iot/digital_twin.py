"""MERMA360 IoT: prototype refrigeration twin (stdlib only).

Receives normalized readings from external gateways; no hardware drivers included.
All thresholds are configuration, not food safety limits.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def parse_timestamp(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp must have timezone")
    return dt.astimezone(timezone.utc)


@dataclass
class Asset:
    asset_id: str
    name: str
    min_temp_c: float
    max_temp_c: float
    stale_after_minutes: int = 15
    humidity_min_pct: Optional[float] = None
    humidity_max_pct: Optional[float] = None

    def __post_init__(self):
        if self.min_temp_c >= self.max_temp_c:
            raise ValueError("Invalid temperature range")
        if self.stale_after_minutes <= 0:
            raise ValueError("stale_after_minutes must be positive")


@dataclass
class Reading:
    asset_id: str
    observed_at: str
    temp_c: float
    humidity_pct: Optional[float] = None
    door_open: Optional[bool] = None
    power_ok: Optional[bool] = None

    def __post_init__(self):
        if not -100 <= self.temp_c <= 120:
            raise ValueError("Implausible temperature reading")
        if self.humidity_pct is not None and not 0 <= self.humidity_pct <= 100:
            raise ValueError("Invalid humidity percentage")
        parse_timestamp(self.observed_at)


@dataclass
class DigitalTwin:
    asset: Asset
    history: list[Reading] = field(default_factory=list)

    def ingest(self, reading: Reading):
        if reading.asset_id != self.asset.asset_id:
            raise ValueError("Reading belongs to a different asset")
        if self.history and parse_timestamp(reading.observed_at) <= parse_timestamp(self.history[-1].observed_at):
            raise ValueError("Readings must arrive in increasing timestamp order")
        self.history.append(reading)

    def state(self, now: Optional[datetime] = None) -> dict:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if not self.history:
            return {"asset_id": self.asset.asset_id, "status": "no_data", "alerts": ["NO_DATA"]}
        last = self.history[-1]
        age_minutes = (now - parse_timestamp(last.observed_at)).total_seconds() / 60
        alerts = []
        if age_minutes > self.asset.stale_after_minutes:
            alerts.append("STALE_TELEMETRY")
        if age_minutes < -1:
            alerts.append("FUTURE_TIMESTAMP")
        if last.temp_c < self.asset.min_temp_c or last.temp_c > self.asset.max_temp_c:
            alerts.append("TEMP_OUT_OF_RANGE")
        if last.humidity_pct is not None:
            if self.asset.humidity_min_pct is not None and last.humidity_pct < self.asset.humidity_min_pct:
                alerts.append("HUMIDITY_LOW")
            if self.asset.humidity_max_pct is not None and last.humidity_pct > self.asset.humidity_max_pct:
                alerts.append("HUMIDITY_HIGH")
        if last.door_open is True:
            alerts.append("DOOR_OPEN")
        if last.power_ok is False:
            alerts.append("POWER_FAILURE")
        return {
            "asset_id": self.asset.asset_id,
            "name": self.asset.name,
            "observed_at": last.observed_at,
            "temp_c": last.temp_c,
            "humidity_pct": last.humidity_pct,
            "door_open": last.door_open,
            "power_ok": last.power_ok,
            "telemetry_age_minutes": round(age_minutes, 1),
            "alerts": alerts,
            "status": "alert" if alerts else "normal",
        }


def normalize_payload(payload: dict, field_map: dict) -> Reading:
    """Adapter for gateway data: field_map maps normalized names to source keys.

    Example: {"asset_id":"device", "observed_at":"time", "temp_c":"temperature"}.
    Adapters for Modbus/MQTT/OPC UA must translate into this schema outside this module.
    """
    keys = ("asset_id", "observed_at", "temp_c", "humidity_pct", "door_open", "power_ok")
    clean = {key: payload[field_map[key]] for key in keys if key in field_map and field_map[key] in payload}
    return Reading(**clean)


if __name__ == "__main__":
    asset = Asset("CF-001", "Camara frigorifica 1", 2, 5, humidity_max_pct=90)
    twin = DigitalTwin(asset)
    twin.ingest(Reading("CF-001", datetime.now(timezone.utc).isoformat(), 8.2, 75, False, True))
    print(twin.state())
