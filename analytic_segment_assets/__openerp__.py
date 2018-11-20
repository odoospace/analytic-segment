# -*- coding: utf-8 -*-
{
    'name': "Analytic segment assets",

    'summary': """
        Analytic Segments for assets
    """,

    'description': """
        Analytic Segments for assets
    """,

    'author': "Impulzia S.L.",
    'website': "https://www.impulzia.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '8.0.1.3',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'analytic_segment', 'account_asset'],

    # always loaded
    'data': [
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo.xml',
    #],
}
