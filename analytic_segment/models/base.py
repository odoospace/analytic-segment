# -*- coding: utf-8 -*-
# use res_users and res_company with analytic accounts

from openerp import models, fields, api, _
from lxml import etree

class res_users(models.Model):
    _inherit = 'res.users'

    @api.multi
    def recalculate_user_segments(self):
        """Function to store all user segments to speed up chekcs in main models"""
        user_ids = self.env['res.users'].search([])
        for user in user_ids:
            print 'Recalculating user:', user
            ids_to_write = []
            segment_tmpl_ids = []
            segment_ids = self.env['res.users'].browse(user.id).segment_ids
            for s in segment_ids:
                segment_tmpl_ids += [s.segment_id.segment_tmpl_id.id]
                segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            # add virtual companies segments
            virtual_segments = self.env['analytic_segment.template'].search([('virtual', '=', True)])
            segment_tmpl_ids += [i.id for i in virtual_segments]

            # mark segments with user id
            segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            for segment in segment_ids:
                ids_to_write.append(segment.id)
            usr_segments = [i.id for i in user.segment_segment_ids]
            if not (set(ids_to_write) == set(usr_segments)):
                user.segment_segment_ids = None
                #user.write({'segment_segment_ids': (6, _, [ids_to_write])})
                user.segment_segment_ids = segment_ids
                print user, 'segmetns updated!', ids_to_write, usr_segments
            else:
                print user, 'segments matches!', ids_to_write, usr_segments
        return
    
    def get_campaign_default(self):
        """return default campaign"""
        return [obj for obj in self.segment_ids if obj.campaign_default][0]


    segment_segment_ids = fields.Many2many('analytic_segment.segment', 'segment_user_rel', string='Segments segments')
    segment_ids = fields.One2many('analytic_segment.user', 'user_id', string='Segments')


class res_company(models.Model):
    _inherit = 'res.company'

    segment_ids = fields.Many2many('analytic_segment.segment', 'segment_company_rel', string='Segments')
    #campaign_ids = fields.One2many('analytic_segment.campaign', 'company_id')

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            res['arch'] = res['arch'].replace('<sheet>', '').replace('</sheet>', '')
        return res
