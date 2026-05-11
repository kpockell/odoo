# -*- coding: utf-8 -*-
{
    "name": "Market Sales Tracker",
    "category": "Sales",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "views/market_location_views.xml",
        "views/market_weekly_sale_views.xml",
        "views/market_sales_menus.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
