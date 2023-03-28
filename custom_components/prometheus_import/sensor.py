from datetime import timedelta, datetime
from typing import Any, Dict, Optional, Tuple
import logging
import asyncio

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.info("Called async setup entry")
    sensors = []
    # We list existing alerts only at startup, FIXME
    for alert_name in await alerts():
        sensors.append(PrometheusAlert(alert_name, entry, hass))

    async_add_entities(sensors)
    _LOGGER.info("We finished the setup of prometheus_import *entity*")

async def alerts() -> list[str]:
    return ["DemoAlert", "FakeAlert"]


class PrometheusAlert(SensorEntity):
    """Representation of an alert in prometheus"""

    def __init__(
        self,
        alert_name: str,
        config_entry: ConfigEntry,
        hass: HomeAssistant
    ):
        self._attr_name = f"{alert_name} alert"
        self._attr_unique_id = f"{config_entry.entry_id}-{alert_name}"
        self.hass = hass
        self._attr_extra_state_attributes: Dict[str, Any] = {}
        _LOGGER.info(f"Creating an alert sensor, named {self.name}")
        self._state = None

    @property
    def state(self) -> Optional[str]:
        return self._state

    async def async_update(self):
        """For now it does nothing"""
        _LOGGER.info("Polling state")
        return
