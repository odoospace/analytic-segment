# -*- coding: utf-8 -*-
# use analytic_segment with analytic accounts

from openerp import models, fields, api

class account_move(models.Model):
    _inherit = 'account.move'

    segment_id = fields.Many2one('analytic_segment.segment_id') #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    segment_id = fields.Many2one(related='move_id.segment_id', readonly=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)