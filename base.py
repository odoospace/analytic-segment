# -*- coding: utf-8 -*-
# use res_users and res_company with analytic accounts

from openerp import models, fields, api
from lxml import etree

class res_users(models.Model):
    _inherit = 'res.users'

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
