# -*- coding: utf-8 -*-
{
    'name': "Create Order in Odoo",

    'summary': """
        Create Order in Odoo from website App.""",

    'description': """
        Create Order in Odoo from website App.
    """,

    'author': "Hunain AK",
    'website': "http://www.haksolutions.com",
  'images': ['static/description/icon.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
