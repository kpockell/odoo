# -*- coding: utf-8 -*-
{
    'name': 'MRP Phantom BoM Batch Weighing',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Track ingredient batch weighings for phantom BoMs in Manufacturing Orders',
    'description': """
        MRP Phantom BoM Batch Weighing Tracker
        =======================================
        
        This module allows tracking individual batch weighings of ingredients during 
        Manufacturing Order (MO) processing when phantom BoMs are used.
        
        Features:
        ---------
        * Track actual weights of ingredients weighed in batches
        * Record batch numbers and lot/serial numbers
        * Calculate and display variance from theoretical quantities
        * Multi-session weighing support (can record weights over multiple sessions)
        * Full traceability of all weighing operations
        * Easy-to-use wizard popup for data entry
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['mrp', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_batch_weighing_views.xml',
        'views/mrp_production_views.xml',
        'wizard/mrp_batch_weighing_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
