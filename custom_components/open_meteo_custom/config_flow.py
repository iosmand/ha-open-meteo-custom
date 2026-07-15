"""Config flow to configure the Open-Meteo Custom integration."""

from typing import Any, override

import voluptuous as vol

from homeassistant.components.zone import DOMAIN as ZONE_DOMAIN
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ZONE
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_MODEL, CONF_UPDATE_INTERVAL, CONF_USE_HA_TIMEZONE, DOMAIN, MODELS


class OpenMeteoCustomFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Open-Meteo Custom."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            zone_id = user_input[CONF_ZONE]
            model = user_input[CONF_MODEL]
            unique_id = f"{zone_id}_{model}"
            
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            state = self.hass.states.get(zone_id)
            zone_name = state.name if state else "Unknown Zone"
            model_label = MODELS.get(model, model)
            
            return self.async_create_entry(
                title=f"{zone_name} ({model_label})",
                data={
                    CONF_ZONE: zone_id,
                    CONF_MODEL: model,
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                    CONF_USE_HA_TIMEZONE: user_input[CONF_USE_HA_TIMEZONE],
                },
            )

        # Options for selection
        options = [{"label": label, "value": val} for val, label in MODELS.items()]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ZONE): EntitySelector(
                        EntitySelectorConfig(domain=ZONE_DOMAIN),
                    ),
                    vol.Required(CONF_MODEL, default="best_match"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            mode=SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Required(CONF_UPDATE_INTERVAL, default="30"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                {"label": "15 Minutes", "value": "15"},
                                {"label": "30 Minutes", "value": "30"},
                                {"label": "60 Minutes", "value": "60"},
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                    vol.Required(CONF_USE_HA_TIMEZONE, default=True): bool,
                }
            ),
        )

