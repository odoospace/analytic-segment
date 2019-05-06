# -*- coding: utf-8 -*-
# use res_users and res_company with analytic accounts

from openerp import models, fields, api, _
from lxml import etree
import json

class res_users(models.Model):
    _inherit = 'res.users'

    @api.multi
    def recalculate_user_segments(self, uid=None):
        """Function to store all user segments to speed up checks in main models"""
        if not uid:
            users = self.env['res.users'].search([])
        else:
            users = [self.env.user]

        for user in users[1:]:
            print 'Recalculating user:', user.id, user.name
            ids_to_write = []
            segment_company_all_ids = {}
            for s in user.segment_ids:
                if not s.campaign_id or (s.campaign_id and s.campaign_id.state == 'open'):
                    if not s.company_id in segment_company_all_ids:
                        segment_company_all_ids[s.company_id.id] = []
                    segment_company_all_ids[s.company_id.id] += [s.segment_id.id]
                    if s.with_childs:
                        segment_company_all_ids[s.company_id.id] += s.segment_id.get_childs_ids()
            # add virtual companies segments
            virtual_segments = self.env['analytic_segment.segment'].search([('virtual', '=', True)])
            for company in segment_company_all_ids.keys():
                segment_company_all_ids[company] += [i.id for i in virtual_segments]

            # mark segments with user id
            for segment in segment_company_all_ids.values():
                ids_to_write += segment

            print 1, segment_company_all_ids
            print 2, ids_to_write

            user_segments = [i.id for i in user.segment_segment_ids]
            if ids_to_write or user_segments:
                print 3, user_segments
                #if set(ids_to_write) != set(user_segments):
                    #user.segment_segment_ids = None
                    #user.write({'segment_segment_ids': (6, _, [ids_to_write])})
                segments = self.env['analytic_segment.segment'].search([('id', 'in', list(set(ids_to_write)))])
                user.segment_segment_ids = segments
                user.segment_by_company = json.dumps(segment_company_all_ids)
                #    print user.login, 'segments updated!', ids_to_write, user_segments
                #else:
                #    print user.login, 'segments matches!', ids_to_write, user_segments
        return
    
    # TODO: use store
    @api.multi
    def _get_default_campaign_id(self):
        """return default campaign"""
        for obj in self:
            res = [item.segment_id for item in obj.segment_ids if item.campaign_default]
            if res:
                obj.default_campaign_id = res[0].id
            else:
                obj.default_campaign_id = False

    def _get_is_campaign(self):
        return self._get_default_campaign_id and True or False


    segment_segment_ids = fields.Many2many('analytic_segment.segment', 'segment_user_rel', string='Segments segments')
    segment_by_company = fields.Char(default=None)
    segment_ids = fields.One2many('analytic_segment.user', 'user_id', string='Segments')
    default_campaign_id = fields.Many2one('analytic_segment.segment', compute='_get_default_campaign_id')
    campaign = fields.Boolean(compute='_get_is_campaign') # TODO: did we need this field???


class res_company(models.Model):
    _inherit = 'res.company'

    segment_id = fields.Many2one('analytic_segment.segment') # main segment 
    segment = fields.Char(related='segment_id.segment', readonly=True)
    segment_ids = fields.Many2many('analytic_segment.segment', 'segment_company_rel', string='Segments')
    #campaign_ids = fields.One2many('analytic_segment.campaign', 'company_id')

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            res['arch'] = res['arch'].replace('<sheet>', '').replace('</sheet>', '')
        return res
