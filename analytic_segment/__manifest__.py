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
    'version': '8.0.13.3',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'analytic'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/templates.xml',
        # 'security/security.xml',
        # 'cron.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo.xml',
    #],
}
