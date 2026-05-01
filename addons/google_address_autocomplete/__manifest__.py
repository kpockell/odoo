# -*- coding: utf-8 -*-
{
    'name': 'Google Address Autocomplete',
    'version': '1.0',
    'summary': 'Autocomplete addresses using the Google Places API',
    'description': """
Adds an address autocomplete widget to the Street field on customer and vendor
forms. When the user starts typing, suggestions are fetched from the Google
Places API via a server-side proxy (so the API key is never exposed to the
browser). Selecting a suggestion auto-populates City, ZIP, State, and Country.

Configuration
-------------
Go to Settings → General Settings and enter a Google Places API key.
If the key is left blank the addon falls back to the key stored by the
Partner Geolocation (base_geolocalize) module, if that module is installed.

The Google Places API key requires the "Places API" to be enabled in your
Google Cloud project.
    """,
    'category': 'Hidden/Tools',
    'depends': ['base', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'google_address_autocomplete/static/src/js/address_autocomplete_field.js',
            'google_address_autocomplete/static/src/xml/address_autocomplete_field.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
