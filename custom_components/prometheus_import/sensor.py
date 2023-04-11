from datetime import timedelta, datetime
from typing import Any, Dict, Optional, Tuple
import logging
import aiohttp

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15)  # ideally we would prefer to subscribe to updates


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.info(
        f"Called async setup entry for prometheus with url: {entry.data['url']}"
    )

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    await coordinator.async_config_entry_first_refresh()

    sensors = []
    # We list existing alerts only at startup, FIXME
    for alert_name in coordinator.alerts():
        sensors.append(PrometheusAlert(alert_name, coordinator, entry, hass))

    async_add_entities(sensors)
    _LOGGER.info("We finished the setup of prometheus_import *entity*")


class PrometheusAlert(CoordinatorEntity, SensorEntity):
    """Representation of an alert in prometheus"""

    def __init__(
        self,
        alert_name: str,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        hass: HomeAssistant,
    ):
        self.hass = hass
        super().__init__(coordinator)
        self.alert_name = alert_name
        self._attr_name = f"{alert_name} alert"
        self._attr_unique_id = f"{config_entry.entry_id}-{alert_name}"
        _LOGGER.info(f"Creating an alert sensor, named {self.name}")

        self._attr_extra_state_attributes: Dict[str, Any] = {}

        self._state = None

    @property
    def state(self) -> Optional[str]:
        return self._state

    @callback
    def _handle_coordinator_update(self) -> None:
        found = False
        for group in self.coordinator.data["groups"]:
            for rule in group["rules"]:
                if rule["name"] == self.alert_name:
                    self._state = rule["state"]
                    self._attr_extra_state_attributes = rule[
                        "annotations"
                    ]  # we intentionnally don't store rule object which contains several fields that will vary at each iteration
                    self._update_icon()
                    self.async_write_ha_state()
                    found = True
                    break
        if not found:
            _LOGGER.warn(
                f"No status found for {self.alert_name}, keeping current state. Is alert still defined in prometheus?"
            )
        _LOGGER.info(f"Finish updating states of {self.alert_name}")

    def _update_icon(self):
        match self._state:
            case "inactive":
                self._attr_icon = "mdi:bell-off"
            case "pending":
                self._attr_icon = "mdi:bell-badge"
            case _:
                self._attr_icon = "mdi:bell-ring"
