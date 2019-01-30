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

    segment_id = fields.Many2one(related='move_line_id.move_id.segment_id', index=True, readonly=True, domain=_domain_segment)
    segment = fields.Char(related='segment_id.segment', readonly=True)

