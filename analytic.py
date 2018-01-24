# -*- coding: utf-8 -*-
# use analytic_segment with analytic accounts

from openerp import models, fields, api

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    segment_id = fields.Many2one('analytic_segment.segment') #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
