import os
import json
import logging
from datetime import timedelta, datetime
import aiohttp
from dateutil import tz


from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Called async setup entry from __init__.py")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {} # if we need to store data
    coordinator = PrometheusAlertCoordinator(hass, entry.data)
    hass.data[DOMAIN][entry.entry_id]['coordinator'] = coordinator

    # will make sure async_setup_entry from sensor.py is called
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR, Platform.BINARY_SENSOR])

    # subscribe to config updates
    entry.async_on_unload(entry.add_update_listener(update_entry))

    return True


async def update_entry(hass, entry):
    """
    This method is called when options are updated
    We trigger the reloading of entry (that will eventually call async_unload_entry)
    """
    _LOGGER.debug("update_entry method called")
    # will make sure async_setup_entry from sensor.py is called
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """This method is called to clean all sensors before re-adding them"""
    _LOGGER.debug("async_unload_entry method called")
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR]
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class PrometheusAlertCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry_data):
        super().__init__(
                hass,
                _LOGGER,
                name=f"Prometheus alert coordinator {entry_data['url']}",
                update_interval=timedelta(seconds=15),
                )
        self.entry_data = entry_data

    def alerts(self):
        """Assuming we've already queried with success once"""
        alert_names = []
        for group in self.data['groups']:
            for rule in group['rules']:
                alert_names.append(rule['name'])
        return alert_names

    async def _async_update_data(self):
        _LOGGER.debug(f"Polling state for {self.name}")
        try:
            async with aiohttp.ClientSession() as session:
                complete_url = self.entry_data['url'] + '/api/v1/rules'
                async with session.get(complete_url, params={'type': 'alert'}) as response:
                    _LOGGER.debug(f"Status was {response.status}")
                    data = await response.json()
                    _LOGGER.debug(f"response was {data}")
                    return data['data']
        except Exception as e:
            raise UpdateFailed(f"Generic error when talking to prometheus API: {e}")


