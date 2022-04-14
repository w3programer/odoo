# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'POS Report',
    'version': '15.0.0.0',
    'category': 'Point of sale',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'summary': 'POS Sale details',
    'website': 'http://www.technaureus.com',
    'price': 30,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'description': """
        Session Reports
        ================
        1.POS Session Summary
        2.Session Order Summary Report.
        
        Sales Details XLSX Report.
        ========================
        3.Order Summary Report.
        4.Daily Sales by Salesperson.
        5.Daily Item wise sales summary.
        6.Monthly Sales by salesperson.
        7.Monthly Item wise sales summary
        8.Date range by salesperson sales summary
        9.Date range by item wise sales summary""",
    'depends': ['base','pos_sale', 'pos_hr'],
    'data': [
        'report/session_summary_report.xml',
        'report/session_summary.xml',
        'report/session_order_summary.xml',
        'wizard/pos_report.xml',
        'data/cron.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.youtube.com/watch?v=F_0PAgQgg2E&list=UUhusfuYvl4Xbf7-RLP5hHFg'
}
