"""Constants for the Ezviz DL03 Pro integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "ezviz_dl03_pro"
MANUFACTURER: Final = "Ezviz"
MODEL: Final = "DL03 Pro"

CONF_SERIAL: Final = "serial_number"
CONF_REGION: Final = "region"
DEFAULT_REGION: Final = "eu"
REGIONS: Final = ["eu", "us", "sa", "as", "ru"]

# Options
CONF_RELOCK_SECONDS: Final = "relock_seconds"
CONF_USE_PUSH: Final = "use_push"
CONF_POLL_INTERVAL: Final = "poll_interval"
CONF_REMOTE_CONTROL: Final = "remote_control"

DEFAULT_RELOCK_SECONDS: Final = 25
DEFAULT_USE_PUSH: Final = True
DEFAULT_POLL_INTERVAL: Final = 5
DEFAULT_REMOTE_CONTROL: Final = False

# How often device status (battery, Wi-Fi, door sensor) is refreshed.
STATUS_INTERVAL: Final = timedelta(seconds=60)
# Safety-net event polling while MQTT push is working.
PUSH_SAFETY_POLL: Final = timedelta(seconds=15)
# Delays (s) for fetching the event list after a push arrives; the cloud
# sometimes needs a moment before the event shows up in the alarm list.
PUSH_FETCH_DELAYS: Final = (0.0, 1.5, 4.0)
# How many events to fetch per poll, so bursts are not lost.
ALARM_FETCH_LIMIT: Final = 10
# How many processed event ids to remember.
SEEN_IDS_MAX: Final = 200
# How long the doorbell binary sensor stays on after a ring.
DOORBELL_RESET_SECONDS: Final = 7
# Status failures tolerated (keeping last data) before entities go unavailable.
MAX_TRANSIENT_FAILURES: Final = 3

# Kinds of lock events
KIND_DOORBELL: Final = "doorbell"
KIND_UNLOCKED: Final = "unlocked"
KIND_LOCKED: Final = "locked"
KIND_OTHER: Final = "other"

# Fired on the HA event bus for every new lock event.
BUS_EVENT: Final = f"{DOMAIN}_event"
