# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


def _get_places_api_key(env):
    """Return the configured Google Places API key.

    Checks this module's own config parameter first, then falls back to the
    key stored by *base_geolocalize* so that users who already have that
    module installed do not have to enter the key twice.
    """
    ICP = env['ir.config_parameter'].sudo()
    key = ICP.get_param('google_address_autocomplete.places_api_key')
    if not key:
        key = ICP.get_param('base_geolocalize.google_map_api_key')
    return key or ''


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_places_api_key = fields.Char(
        string='Google Places API Key',
        config_parameter='google_address_autocomplete.places_api_key',
        help=(
            'API key used for address autocomplete on partner forms. '
            'The Places API must be enabled for this key in your Google Cloud '
            'project. Visit https://developers.google.com/maps/documentation/'
            'places/web-service/get-api-key for instructions.\n\n'
            'Leave empty to reuse the key from the Partner Geolocation '
            '(base_geolocalize) module if it is installed.'
        ),
    )
