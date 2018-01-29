# -*- coding: utf-8 -*-
# use analytic_segment with analytic accounts

from openerp import models, fields, api

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    def _search_segment_user(self, operator, value):
        user = self.env['res.users'].browse(value)
        segment_tmpl_ids = []
        segment_ids = user.segment_ids
        for s in segment_ids:
            segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
        segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])

        return [('segment_id', 'in', [i.id for i in segment_ids])]

    @api.multi
    def get_segment_user_id(self):
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
        else:
            segment_tmpl_ids = []
            #segment_ids = self.env['analytic_segment.segment'].search([('name', '=', 'Andalucía')])
            segment_ids = self.env.user.segment_ids
            for s in segment_ids:
                segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            for obj in self:
                if obj.segment_id in segment_ids:
                    obj.segment_user_id = self.env.uid

    segment_id = fields.Many2one('analytic_segment.segment') #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='get_segment_user_id', search=_search_segment_user)
