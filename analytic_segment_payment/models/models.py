# -*- coding: utf-8 -*-
# More simple segment model to use in odoo analytic and no analytic objects

from openerp import SUPERUSER_ID
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, Warning
from openerp.tools import float_compare
from openerp.osv import osv
import time
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json



class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            print '+++', self.env.user.segment_by_company_open
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            print '_domain_segment', self.env.user.company_id.id, segment_by_company_open
            domain = [('id', 'in', segment_by_company_open)]
        print '>>> domains:', domain
        return domain

    def _get_default_segment_from_user(self):
        # TODO: search real default
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

    def _search_segment_user(self, operator, value):
        #user = self.env['res.users'].browse(value)
        user = self.env['res.users'].browse(self.env.context['user'])
        print 'payment_order', user.id, user.company_id.id, user.company_id.name
        print '+++', user.segment_by_company
        segment_by_company = json.loads(user.segment_by_company)[str(user.company_id.id)]
        res = [('segment_id', 'in', segment_by_company)]
        print '>>>', res
        return res

    @api.multi
    def _segment_user_id(self):
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
            return
        else:
            for obj in self:
                segment_by_company = json.loads(self.env.user.segment_by_company)[str(self.env.user.company_id.id)]
                if obj.segment_id in segment_by_company:
                    obj.segment_user_id = self.env.uid
            return


    @api.depends('mode.journal.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.mode.journal.segment_id

    segment_id = fields.Many2one(related='mode.journal.segment_id', index=True, readonly=True, store=True, domain=_domain_segment, default=2)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    # campaign_segment = fields.Boolean(related='move_id.campaign_segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)



class PaymentLine(models.Model):
    _inherit = 'payment.line'

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            print '+++', self.env.user.segment_by_company_open
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            print '_domain_segment', self.env.user.company_id.id, segment_by_company_open
            domain = [('id', 'in', segment_by_company_open)]
        print '>>> domains:', domain
        return domain

    def _get_default_segment_from_user(self):
        # TODO: search real default
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

    def _search_segment_user(self, operator, value):
        #user = self.env['res.users'].browse(value)
        user = self.env['res.users'].browse(self.env.context['user'])
        print 'payment_line', user.id, user.company_id.id, user.company_id.name
        print '+++', user.segment_by_company
        segment_by_company = json.loads(user.segment_by_company)[str(user.company_id.id)]
        res = [('segment_id', 'in', segment_by_company)]
        print '>>>', res
        return res

    @api.multi
    def _segment_user_id(self):
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
            return
        else:
            for obj in self:
                segment_by_company = json.loads(self.env.user.segment_by_company)[str(self.env.user.company_id.id)]
                if obj.segment_id in segment_by_company:
                    obj.segment_user_id = self.env.uid
            return



    @api.depends('move_line_id.move_id.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.move_line_id.move_id.segment_id

    segment_id = fields.Many2one(related='move_line_id.move_id.segment_id', index=True, store=True, readonly=True, domain=_domain_segment, default=2)
    segment = fields.Char(related='segment_id.segment', readonly=True)



class PaymenMode(models.Model):
    _inherit = 'payment.mode'

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            print '+++', self.env.user.segment_by_company_open
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            print '_domain_segment', self.env.user.company_id.id, segment_by_company_open
            domain = [('id', 'in', segment_by_company_open)]
        print '>>> domains:', domain
        return domain

    def _get_default_segment_from_user(self):
        # TODO: search real default
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

    def _search_segment_user(self, operator, value):
        #user = self.env['res.users'].browse(value)
        user = self.env['res.users'].browse(self.env.context['user'])
        print 'payment_mode', user.id, user.company_id.id, user.company_id.name
        print '+++', user.segment_by_company
        segment_by_company = json.loads(user.segment_by_company)[str(user.company_id.id)]
        res = [('segment_id', 'in', segment_by_company)]
        print '>>>', res
        return res

    @api.multi
    def _segment_user_id(self):
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
            return
        else:
            for obj in self:
                segment_by_company = json.loads(self.env.user.segment_by_company)[str(self.env.user.company_id.id)]
                if obj.segment_id in segment_by_company:
                    obj.segment_user_id = self.env.uid
            return


    @api.depends('journal.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.journal.segment_id

    segment_id = fields.Many2one(related='journal.segment_id', index=True, store=True, readonly=True, domain=_domain_segment, default=2)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    # campaign_segment = fields.Boolean(related='move_id.campaign_segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)
