from datetime import timedelta, datetime
from typing import Any, Dict, Optional, Tuple
import logging
import aiohttp

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.components.binary_sensor import (
        BinarySensorEntity,
        BinarySensorDeviceClass
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15) # ideally we would prefer to subscribe to updates

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.info(f"Called async setup entry for prometheus with url: {entry.data['url']}")


    coordinator = hass.data[DOMAIN][entry.entry_id]['coordinator']

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([PrometheusAlertBinarySensor(coordinator, entry, hass)])

    _LOGGER.info("We finished the setup of prometheus_import *entity*")


class PrometheusAlertBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor triggered by 'any' alert in prometheus"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        hass: HomeAssistant
    ):
        self.hass = hass
        super().__init__(coordinator)
        self._attr_name = f"Prometheus alert"
        self._attr_unique_id = f"{config_entry.entry_id}-firing-alerts"

        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

        self._attr_extra_state_attributes: Dict[str, Any] = {}

    @callback
    def _handle_coordinator_update(self) -> None:
        any_firing = False
        firing_names = []
        for group in self.coordinator.data['groups']:
            for rule in group['rules']:
                if rule['state'] == "firing":
                    firing_names.append(rule['name'])
                    any_firing = True
                    break
        firing_names.sort()
        self._attr_is_on = any_firing
        self._attr_extra_state_attributes["Firing"] = ", ".join(firing_names)
        self.async_write_ha_state()
