# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

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


    def _get_default_segments(self):
        if not self.env.user.id == 1:
            seg = False
            #add payment mode segments
            order = self.env['payment.order'].search([('id', '=', self._context['active_id'])])
            seg = order.mode.segment_id
            with_children = not order.mode.journal.check_segment_id
            #or add user segments
            # for i in self.env.user.segment_ids:
            #     if i.company_id == self.env.user.company_id:
            #         seg = i.segment_id
            #         break
            #ugly hack...
            #at this point the wizard don't exist, need to commit to get an id
            self._cr.commit()
            if seg:
                data = {
                    'report_id': self.id,
                    'segment_id': seg.id,
                    'with_children': with_children
                }
                return [(0, 0, data)]
            else:
                return None


    segments = fields.One2many('payment.order.create.segments', 'report_id', default=_get_default_segments)
    
    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        super(PaymentOrderCreate, self).extend_payment_order_domain(
            payment_order, domain)
        if not self.env.user.id == 1:
            segment_tmpl_ids = []
            for s in self.segments:
                segment_tmpl_ids += [s.segment_id.segment_tmpl_id.id]
                if s.with_children:
                    segment_tmpl_ids += s.segment_id.segment_tmpl_id.get_childs_ids()
            segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            domain.insert(0, ('segment_id', 'in', [i.id for i in segment_ids]))
        return domain
