# -*- coding: utf-8 -*-
# More simple segment model to use in odoo analytic and no analytic objects

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError, Warning
from openerp.tools import float_compare
from openerp.osv import osv

class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.one
    @api.constrains('segment_id', 'category_id')
    def _check_segment_id(self):
        if not self.env.user.has_group('analytic_segment.group_analyticsegments_norestrictions'):
            if self.category_id.journal_id.check_segment_id:
                if self.journal_id.segment_id != self.segment_id:
                    raise ValidationError("Segment differs between journal and move!")
            if not self.segment_id:
                raise ValidationError("You must set a segment!")
        return

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
            return domain
        else:
            return [('id', 'in', [i.id for i in self.env.user.segment_segment_ids])]

    def _get_default_segment_from_user(self):
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

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


    segment_id = fields.Many2one('analytic_segment.segment', index=True, domain=_domain_segment, required=True, default=_get_default_segment_from_user) #)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    campaign_segment = fields.Boolean(related='segment_id.is_campaign')
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)

class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'

    def create_move(self, cr, uid, ids, context=None):
        context = dict(context or {})
        can_close = False
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            depreciation_date = context.get('depreciation_date') or line.depreciation_date or time.strftime('%Y-%m-%d')
            period_ids = period_obj.find(cr, uid, depreciation_date, context=context)
            company_currency = line.asset_id.company_id.currency_id.id
            current_currency = line.asset_id.currency_id.id
            context.update({'date': depreciation_date})
            amount = currency_obj.compute(cr, uid, current_currency, company_currency, line.amount, context=context)
            sign = (line.asset_id.category_id.journal_id.type == 'purchase' and 1) or -1
            asset_name = "/"
            reference = line.asset_id.name
            move_vals = {
                'name': asset_name,
                'date': depreciation_date,
                'ref': reference,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': line.asset_id.category_id.journal_id.id,
                'segment_id': line.asset_id.segment_id.id
                }
            move_id = move_obj.create(cr, uid, move_vals, context=context)
            journal_id = line.asset_id.category_id.journal_id.id
            partner_id = line.asset_id.partner_id.id
            prec = self.pool['decimal.precision'].precision_get(cr, uid, 'Account')
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_depreciation_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
                'date': depreciation_date,
            })
            move_line_obj.create(cr, uid, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.asset_id.category_id.account_expense_depreciation_id.id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                'analytic_account_id': line.asset_id.category_id.account_analytic_id.id,
                'date': depreciation_date,
                'asset_id': line.asset_id.id
            })
            self.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            asset_ids.append(line.asset_id.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.currency_id, asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids

