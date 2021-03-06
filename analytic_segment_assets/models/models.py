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



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_cancel(self):
        asset = self.env['account.asset.asset'].search([('company_id', '=', self.company_id.id),('code', '=', self.number)])
        if asset:
            for ass in asset:
                for depreciation in ass.depreciation_line_ids:
                    if depreciation.move_check and depreciation.move_id:
                        raise ValidationError("Can't cancel invoice with related assets with depreciation executed. Cancel the depreciation first and try again")
        return super(AccountInvoice, self).action_cancel()

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
        print 'account_asset', user.id, user.company_id.id, user.company_id.name
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


    segment_id = fields.Many2one('analytic_segment.segment', index=True, domain=_domain_segment, required=True, default=_get_default_segment_from_user) #)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    campaign_segment = fields.Boolean(related='segment_id.is_campaign', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)
    closure_date = fields.Date(string='Closure Date', states={'close':[('readonly',True)]})

    @api.multi
    def set_to_open(self):
        if self.closure_date:
            self.closure_date = ''
        self.state = 'open'
        return

    @api.multi
    def set_to_close(self):
        if not self.closure_date:
            self.closure_date = time.strftime('%Y-%m-%d')
        self.state = 'close'
        return


class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'

    rel_purchase_date = fields.Date(related='asset_id.purchase_date')
    rel_closure_date = fields.Date(related='asset_id.closure_date', readonly=True)

    def create_move(self, cr, uid, ids, context=None):
        months_dict = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto', 
            9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
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
            asset_name = "Amortización " + months_dict[datetime.strptime(depreciation_date, '%Y-%m-%d').month] + ' ' + str(datetime.strptime(depreciation_date, '%Y-%m-%d').year)
            reference = line.asset_id.name
            move_vals = {
                'name': "/",
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




class account_invoice_line(osv.osv):

    _inherit = 'account.invoice.line'
    
    def asset_create(self, cr, uid, lines, context=None):
        context = context or {}
        asset_obj = self.pool.get('account.asset.asset')
        asset_ids = []
        for line in lines:
            if line.invoice_id.number:
                #FORWARDPORT UP TO SAAS-6
                asset_ids += asset_obj.search(cr, SUPERUSER_ID, [('code', '=', line.invoice_id.number), ('company_id', '=', line.company_id.id)], context=context)
        asset_obj.write(cr, SUPERUSER_ID, asset_ids, {'active': False})
        for line in lines:
            if line.asset_category_id:
                #FORWARDPORT UP TO SAAS-6
                #add functionality to generate multiple assets based on the units of the line
                line_units = line.quantity
                for x in range(1, int(line_units)+1):
                    sign = -1 if line.invoice_id.type in ("in_refund", 'out_refund') else 1
                    name = line.name
                    if line_units != 1:
                        name = line.name + ' ' + str(x) + '/' + str(int(line_units))
                    vals = {
                        'name': name,
                        'code': line.invoice_id.number or False,
                        'category_id': line.asset_category_id.id,
                        'purchase_value': sign * line.price_subtotal / line_units,
                        'partner_id': line.invoice_id.partner_id.id,
                        'company_id': line.invoice_id.company_id.id,
                        'currency_id': line.invoice_id.currency_id.id,
                        'purchase_date': line.invoice_id.date_invoice,
                        'segment_id': line.invoice_id.segment_id.id,
                        'note': line.invoice_id.comment
                    }
                    changed_vals = asset_obj.onchange_category_id(cr, uid, [], vals['category_id'], context=context)
                    vals.update(changed_vals['value'])
                    asset_id = asset_obj.create(cr, uid, vals, context=context)
                    if line.asset_category_id.open_asset:
                        asset_obj.validate(cr, uid, [asset_id], context=context)
        return True

class AccountMoveLine(osv.osv):

    _inherit = 'account.move.line'

    #defalut behaviour don't change move_check field to false when a depreciation related move
    #is deleted. in this method we override unlink method to force the value of the depreciation
    #to False via sql
    @api.multi
    def unlink(self):
        obj = {}
        for i in self:
            if i.asset_id:
                for j in i.asset_id.depreciation_line_ids:
                    if j.depreciation_date == i.date:
                        sql = "UPDATE account_asset_depreciation_line set move_check=False where id=%d" % j.id
                        self.env.cr.execute(sql)
        res = super(AccountMoveLine, self).unlink()
        return res



