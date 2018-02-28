# -*- coding: utf-8 -*-
# use analytic_segment with analytic accounts

from openerp import models, fields, api

class account_analytic_account(models.Model):
    _inherit = 'account.analytic.account'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            segment = '.' in elmt.segment and elmt.segment.split('.')[1] or 'NN'
            res.append((id, '%s - %s' % (segment, self._get_one_full_name(elmt))))
        return res

    def _search_segment_user(self, operator, value):
        user = self.env['res.users'].browse(value)
        segment_tmpl_ids = []
        segment_ids = user.segment_ids
        for s in segment_ids:
            segment_tmpl_ids += [s.segment_id.segment_tmpl_id.id]
            segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
        virtual_segments = self.env['analytic_segment.template'].search([('virtual', '=', True)])
        segment_tmpl_ids += [i.id for i in virtual_segments]

        segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
        filter = [('segment_id', 'in', [i.id for i in segment_ids])]
        print 'FILTER ->', filter, operator, value
        return filter

    @api.multi
    def _segment_user_id(self):
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
        else:
            # add users segments
            segment_tmpl_ids = []
            segment_ids = self.env.user.segment_ids
            for s in segment_ids:
                segment_tmpl_ids += [s.segment_id.segment_tmpl_id.id]
                segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            # add virtual companies segments
            virtual_segments = self.env['analytic_segment.template'].search([('virtual', '=', True)])
            segment_tmpl_ids += [i.id for i in virtual_segments]

            # mark segments with user id
            segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            print 'SEGMENT_IDS ->', segment_ids
            for obj in self:
                if obj.segment_id in segment_ids:
                    obj.segment_user_id = self.env.uid
            
    segment_id = fields.Many2one('analytic_segment.segment') #, required=True)
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
            segment = '.' in elmt.segment and elmt.segment.split('.')[1] or 'NN'
            res[elmt.id] = '%s - %s' % (segment, self._get_one_full_name(elmt))
        return res

    _columns = {
        'complete_name': fields.function(_get_full_name, type='char', string='Full Name')
    }