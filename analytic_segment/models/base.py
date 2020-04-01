# -*- coding: utf-8 -*-
# use res_users and res_company with analytic accounts

from odoo import models, fields, api, _
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

        for user in users:
            print('Recalculating user:', user.id, user.name)
            ids_to_write = []
            segment_company_all_ids = {}
            segment_company_open_ids = {}
            print('segments:', [i.segment_id.id for i in user.segment_ids])
            for s in user.segment_ids:
                if not s.company_id.id in segment_company_all_ids:
                    segment_company_all_ids[s.company_id.id] = []
                segment_company_all_ids[s.company_id.id] += [s.segment_id.id]
                if s.with_childs:
                    segments_tmpl_ids = s.segment_id.segment_tmpl_id.get_childs_ids()
                    # TODO: review check campaign
                    if not s.campaign_id:
                        campaign_id = False
                    else:
                        campaign_id = s.campaign_id.id
                    segments_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segments_tmpl_ids), ('campaign_id', '=', campaign_id )])
                    segment_company_all_ids[s.company_id.id] += [i.id for i in segments_ids]
                
                # show only campaigns with status 'open'
                if not s.campaign_id or (s.campaign_id and s.campaign_id.state == 'open'):
                    if not s.company_id.id in segment_company_open_ids:
                        segment_company_open_ids[s.company_id.id] = []
                    segment_company_open_ids[s.company_id.id] += [s.segment_id.id]
                    # add all segment of 
                    if s.campaign_id and s.with_childs:
                        segment_company_open_ids[s.company_id.id] += [i.id for i in s.segment_id.campaign_id.segment_ids]
                    elif s.with_childs:
                        segments_tmpl_ids = s.segment_id.segment_tmpl_id.get_childs_ids()
                        segments_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segments_tmpl_ids), ('campaign_id', '=', False)])
                        segment_company_open_ids[s.company_id.id] += [i.id for i in segments_ids]
        
            # add virtual companies segments
            virtual_segments = self.env['analytic_segment.segment'].search([('virtual', '=', True)])
            for company in segment_company_all_ids.keys():
                segment_company_all_ids[company] += [i.id for i in virtual_segments]
                if not company in segment_company_open_ids:
                    segment_company_open_ids[company] = []
                segment_company_open_ids[company] += [i.id for i in virtual_segments]

            # mark segments with user id
            for segment in segment_company_all_ids.values():
                ids_to_write += segment

            print(1, segment_company_all_ids)
            print(2, segment_company_open_ids)
            #print 2, ids_to_write

            #user_segments = [i.id for i in user.segment_segment_ids]
            #if ids_to_write or user_segments:
                #print 3, user_segments
                #if set(ids_to_write) != set(user_segments):
                    #user.segment_segment_ids = None
                    #user.write({'segment_segment_ids': (6, _, [ids_to_write])})
            segments = self.env['analytic_segment.segment'].search([('id', 'in', list(set(ids_to_write)))])
            user.segment_segment_ids = segments
            user.segment_by_company = json.dumps(segment_company_all_ids)
            user.segment_by_company_open = json.dumps(segment_company_open_ids)
                #    print user.login, 'segments updated!', ids_to_write, user_segments
                #else:
                #    print user.login, 'segments matches!', ids_to_write, user_segments
        return
    
    def get_campaign_default(self):
        """return default campaign"""
        return [obj for obj in self.segment_ids if obj.campaign_default][0]


    segment_segment_ids = fields.Many2many('analytic_segment.segment', 'segment_user_rel', string='Segments segments')
    segment_by_company = fields.Char(default=None)
    segment_by_company_open = fields.Char(default=None)
    segment_ids = fields.One2many('analytic_segment.user', 'user_id', string='Segments')


class res_company(models.Model):
    _inherit = 'res.company'

    segment_ids = fields.Many2many('analytic_segment.segment', 'segment_company_rel', string='Segments')
    #campaign_ids = fields.One2many('analytic_segment.campaign', 'company_id')

    # def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    #     res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'form':
    #         res['arch'] = res['arch'].replace('<sheet>', '').replace('</sheet>', '')
    #     return res
