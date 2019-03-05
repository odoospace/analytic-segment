# -*- coding: utf-8 -*-
{
    'name': "Analytic segment payment ",

    'summary': """
        Analytic Segments for payments
    """,

    'description': """
        Analytic Segments for payments
    """,

    'author': "Impulzia S.L.",
    'website': "https://www.impulzia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '8.0.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'analytic_segment', 'account_banking_payment_export', 'account_payment'],

    # always loaded
    'data': [
        'views/templates.xml',
        'security/security.xml',
        'wizard/wizard.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo.xml',
    #],
}
