# -*- coding: utf-8 -*-
# use analytic_segment with analytic accounts

from openerp import models, fields, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _domain_segment(self):
        # TODO: refactor these 3 functions!!!!
        if self.env.user.id == 1:
            # no restrictions
            domain = []
            return domain
        else:
            res = [('id', 'in', [i.id for i in self.env.user.segment_segment_ids])]

    def _search_segment_user(self, operator, value):
        user = self.env['res.users'].browse(value)
        res = [('segment_id', 'in', [i.id for i in user.segment_segment_ids])]
        return res

    @api.multi
    def _segment_user_id(self):
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
        else:
            for obj in self:
                if obj.segment_id in self.env.user.segment_segment_ids:
                    obj.segment_user_id = self.env.uid


    @api.depends('move_id.move_id.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.move_id.move_id.segment_id

    segment_id = fields.Many2one(related='move_id.move_id.segment_id', index=True, store=True, readonly=True, domain=_domain_segment)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    campaign_segment = fields.Boolean(related='move_id.move_id.campaign_segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)


class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            item = self.browse(cr, uid, id, context=context)
            segment = item.segment and '.' in item.segment and item.segment.split('.')[1] or 'NN'
            try:
                res.append((id, '%s - %s' % (segment, self._get_one_full_name(item))))
            except:
                # TODO: to use an exception definition
                pass
        return res

    def _search_segment_user(self, operator, value):
        user = self.env['res.users'].browse(value)
        res = [('segment_id', 'in', [i.id for i in user.segment_segment_ids])]
        return res

    @api.multi
    def _segment_user_id(self):
        print '>>> account.analytic.account'
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
        else:
            for obj in self:
                if obj.segment_id in self.env.user.segment_segment_ids:
                    obj.segment_user_id = self.env.uid

    
    segment_id = fields.Many2one('analytic_segment.segment', index=True) #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)

#inherit in old api to workaround the function field
from openerp.osv import fields, osv
class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    def _get_full_name(self, cr, uid, ids, name=None, args=None, context=None):
        if context == None:
            context = {}
        res = {}
        for elmt in self.browse(cr, uid, ids, context=context):
            segment = elmt.segment and '.' in elmt.segment and elmt.segment.split('.')[1] or 'NN'
            res[elmt.id] = '%s - %s' % (segment, self._get_one_full_name(elmt))
        return res

    _columns = {
        'complete_name': fields.function(_get_full_name, type='char', string='Full Name')
    }