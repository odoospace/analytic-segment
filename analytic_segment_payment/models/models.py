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


class PaymentOrder(models.Model):
    _inherit = 'payment.order'

    def _domain_segment(self):
        # TODO: refactor these 3 functions!!!!
        if self.env.user.id == 1:
            # no restrictions
            domain = []
            return domain
        else:
            return [('id', 'in', [i.id for i in self.env.user.segment_segment_ids])]

    def _search_segment_user(self, operator, value):
        user = self.env['res.users'].browse(value)
        return [('segment_id', 'in', [i.id for i in user.segment_segment_ids])]

    @api.multi
    def _segment_user_id(self):
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
            return
        else:
            for obj in self:
                if obj.segment_id in self.env.user.segment_segment_ids:
                    obj.segment_user_id = self.env.uid
            return

    @api.depends('mode.journal.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.mode.journal.segment_id

    segment_id = fields.Many2one(related='mode.journal.segment_id', index=True, readonly=True, store=True, domain=_domain_segment)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    # campaign_segment = fields.Boolean(related='move_id.campaign_segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)



class PaymentLine(models.Model):
    _inherit = 'payment.line'

    def _domain_segment(self):
        # TODO: refactor these 3 functions!!!!
        if self.env.user.id == 1:
            # no restrictions
            domain = []
            return domain
        else:
            return [('id', 'in', [i.id for i in self.env.user.segment_segment_ids])]


    @api.depends('move_line_id.move_id.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.move_line_id.move_id.segment_id

    segment_id = fields.Many2one(related='move_line_id.move_id.segment_id', index=True, store=True, readonly=True, domain=_domain_segment)
    segment = fields.Char(related='segment_id.segment', readonly=True)



class PaymenMode(models.Model):
    _inherit = 'payment.mode'

    def _domain_segment(self):
        # TODO: refactor these 3 functions!!!!
        if self.env.user.id == 1:
            # no restrictions
            domain = []
            return domain
        else:
            return [('id', 'in', [i.id for i in self.env.user.segment_segment_ids])]

    def _search_segment_user(self, operator, value):
        user = self.env['res.users'].browse(value)
        return [('segment_id', 'in', [i.id for i in user.segment_segment_ids])]

    @api.multi
    def _segment_user_id(self):
        # TODO: use a helper in analytic_segment if it's possible...
        if self.env.user.id == 1:
            for obj in self:
                obj.segment_user_id = self.env.uid
            return
        else:
            for obj in self:
                if obj.segment_id in self.env.user.segment_segment_ids:
                    obj.segment_user_id = self.env.uid
            return

    @api.depends('journal.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.journal.segment_id

    segment_id = fields.Many2one(related='journal.segment_id', index=True, store=True, readonly=True, domain=_domain_segment)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    # campaign_segment = fields.Boolean(related='move_id.campaign_segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)
