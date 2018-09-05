# -*- coding: utf-8 -*-
{
    'name': "Analytic segment",

    'summary': """
        Analytic Segments
    """,

    'description': """
        Analytic Segments
    """,

    'author': "Impulzia S.L.",
    'website': "https://www.impulzia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '8.0.12.2',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'universal_account', 'account_budget'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'templates.xml',
        'security/security.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo.xml',
    #],
}
