# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class PaymentOrderCreateSegments(models.TransientModel):

    _name = "payment.order.create.segments"

    def _domain_segment(self):
        if self.env.user.id == 1:
            # no restrictions
            domain = []
        else:
            segment_tmpl_ids = []
            segment_ids = self.env.user.segment_ids
            for s in segment_ids:
                segment_tmpl_ids += [s.segment_id.segment_tmpl_id.id]
                if self.with_children:
                    segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            virtual_segments = self.env['analytic_segment.template'].search([('virtual', '=', True)])
            segment_tmpl_ids += [i.id for i in virtual_segments]

            segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            domain = [('id', 'in', [i.id for i in segment_ids])]
        return domain


    report_id = fields.Many2one('payment.order.create')
    segment_id = fields.Many2one('analytic_segment.segment', domain=_domain_segment) #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    with_children = fields.Boolean(default=False)

class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    segments = fields.One2many('payment.order.create.segments', 'report_id',)

    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        self.ensure_one()
        if payment_order.payment_order_type == 'payment':
            # For payables, propose all unreconciled credit lines,
            # including partially reconciled ones.
            # If they are partially reconciled with a supplier refund,
            # the residual will be added to the payment order.
            #
            # For receivables, propose all unreconciled credit lines.
            # (ie customer refunds): they can be refunded with a payment.
            # Do not propose partially reconciled credit lines,
            # as they are deducted from a customer invoice, and
            # will not be refunded with a payment.
            domain += [
                ('credit', '>', 0),
                '|',
                ('account_id.type', '=', 'payable'),
                '&',
                ('account_id.type', '=', 'receivable'),
                ('reconcile_partial_id', '=', False),
            ]

        if self.env.user.id == 1:
            # no restrictions
            continue
        else:
            segment_tmpl_ids = []
            for s in self.segments:
                segment_tmpl_ids += [s.segment_id.segment_tmpl_id.id]
                if s.with_children:
                    segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            domain += [('segment_id', 'in', [i.id for i in segment_ids])]
        return domain
