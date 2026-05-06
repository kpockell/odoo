# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

_AUTOCOMPLETE_URL = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
_DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'

# Google Place IDs are base64url-encoded strings; allow alphanumeric, +, /, =, -
_PLACE_ID_RE = re.compile(r'^[A-Za-z0-9+/=_\-]{1,500}$')
# Session tokens are UUIDs; allow hex and hyphens only
_SESSION_TOKEN_RE = re.compile(r'^[A-Za-z0-9\-]{1,128}$')


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


class GoogleAddressAutocomplete(http.Controller):

    # ------------------------------------------------------------------
    # /google_address_autocomplete/autocomplete
    # ------------------------------------------------------------------

    @http.route(
        '/google_address_autocomplete/autocomplete',
        type='json',
        auth='user',
        methods=['POST'],
    )
    def autocomplete(self, input='', session_token='', **_kw):
        """Return a list of address suggestions for *input*.

        The Google Places API key is read from the server configuration and
        is never forwarded to the browser.

        :param str input: partial address typed by the user (max 200 chars)
        :param str session_token: UUID reused across autocomplete+detail calls
                                   to group them into a single billing session
        :returns: ``{'suggestions': [{'description': str, 'place_id': str}]}``
                  or ``{'error': str, 'suggestions': []}`` on failure
        """
        # --- Input validation ---
        input_text = str(input or '').strip()[:200]
        if not input_text:
            return {'suggestions': []}

        session_token = str(session_token or '').strip()
        if session_token and not _SESSION_TOKEN_RE.match(session_token):
            session_token = ''

        api_key = _get_places_api_key(request.env)
        if not api_key:
            return {'error': 'no_api_key', 'suggestions': []}

        params = {
            'input': input_text,
            'key': api_key,
        }
        if session_token:
            params['sessiontoken'] = session_token

        try:
            resp = requests.get(_AUTOCOMPLETE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            _logger.exception('Google Places autocomplete request failed')
            return {'error': 'request_failed', 'suggestions': []}

        suggestions = [
            {
                'description': p.get('description', ''),
                'place_id': p.get('place_id', ''),
            }
            for p in data.get('predictions', [])
            if p.get('description') and p.get('place_id')
        ]
        return {'suggestions': suggestions}

    # ------------------------------------------------------------------
    # /google_address_autocomplete/place_details
    # ------------------------------------------------------------------

    @http.route(
        '/google_address_autocomplete/place_details',
        type='json',
        auth='user',
        methods=['POST'],
    )
    def place_details(self, place_id='', session_token='', **_kw):
        """Return parsed address fields for a Google *place_id*.

        Resolves ``country_id`` and ``state_id`` against Odoo's
        ``res.country`` / ``res.country.state`` records so that the
        frontend can directly call ``record.update(result)``.

        :param str place_id: the ``place_id`` returned by the autocomplete
        :param str session_token: same token used in the autocomplete call
        :returns: dict with keys ``street``, ``city``, ``zip``,
                  ``state_id`` ([id, name] or False),
                  ``country_id`` ([id, name] or False)
        """
        place_id = str(place_id or '').strip()
        if not place_id or not _PLACE_ID_RE.match(place_id):
            return {'error': 'invalid_place_id'}

        session_token = str(session_token or '').strip()
        if session_token and not _SESSION_TOKEN_RE.match(session_token):
            session_token = ''

        api_key = _get_places_api_key(request.env)
        if not api_key:
            return {'error': 'no_api_key'}

        params = {
            'place_id': place_id,
            'fields': 'address_components,name',
            'key': api_key,
        }
        if session_token:
            params['sessiontoken'] = session_token

        try:
            resp = requests.get(_DETAILS_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            _logger.exception('Google Places details request failed')
            return {'error': 'request_failed'}

        result = data.get('result', {})
        components = result.get('address_components', [])
        parsed = self._parse_address_components(components)
        parsed['name'] = result.get('name', '')
        return self._resolve_odoo_fields(parsed, request.env)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_address_components(self, components):
        """Extract the fields we care about from a ``address_components`` list."""
        addr = {}
        for component in components:
            types = component.get('types', [])
            long_name = component.get('long_name', '')
            short_name = component.get('short_name', '')
            if 'street_number' in types:
                addr['street_number'] = long_name
            elif 'route' in types:
                addr['route'] = long_name
            elif 'locality' in types:
                addr['city'] = long_name
            elif 'postal_code' in types:
                addr['zip'] = long_name
            elif 'administrative_area_level_1' in types:
                addr['state_code'] = short_name
            elif 'country' in types:
                addr['country_code'] = short_name  # ISO 3166-1 alpha-2

        # Combine street number and route into a single street string
        street_parts = [addr.get('street_number', ''), addr.get('route', '')]
        addr['street'] = ' '.join(p for p in street_parts if p)
        return addr

    def _resolve_odoo_fields(self, parsed, env):
        """Resolve country/state codes to Odoo record IDs."""
        country_id = False
        state_id = False

        country_code = parsed.get('country_code', '')
        if country_code:
            country = env['res.country'].search(
                [('code', '=', country_code.upper())], limit=1
            )
            if country:
                country_id = [country.id, country.name]

        state_code = parsed.get('state_code', '')
        if country_id and state_code:
            state = env['res.country.state'].search(
                [
                    ('country_id', '=', country_id[0]),
                    ('code', '=', state_code),
                ],
                limit=1,
            )
            if state:
                state_id = [state.id, state.name]

        return {
            'name': parsed.get('name', ''),
            'street': parsed.get('street', ''),
            'city': parsed.get('city', ''),
            'zip': parsed.get('zip', ''),
            'state_id': state_id,
            'country_id': country_id,
        }
