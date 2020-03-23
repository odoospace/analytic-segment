# -*- coding: utf-8 -*-
# use analytic_segment with analytic accounts

from openerp import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from odoo.tools import float_compare
from odoo.osv import osv
from odoo import workflow
import json
import time


class account_move(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        cr, uid, context = self.env.args
        context = dict(context or {})
        invoice = context.get('invoice', False)
        if invoice:
            vals['segment_id'] = context["invoice"].segment_id.id
        return super(account_move, self).create(vals)

    # @api.multi
    # def write(self, vals):
    #     result = super(account_move, self).write(vals)
    #     inv = self.env['account.invoice'].search([('number', '=' , self.ref)])
    #     if self.line_id:
    #         values = {"segment_id": self.segment_id.id}
    #         self.line_id.write(values)
    #     return result

    @api.one
    @api.constrains('segment_id', 'journal_id')
    def _check_segment_id(self):
        if not self.env.user.has_group('analytic_segment.group_analyticsegments_norestrictions'):
            if self.journal_id.check_segment_id:
                if self.journal_id.segment_id != self.segment_id:
                    raise ValidationError("Segment differs between journal and move!")
            if not self.segment_id:
                raise ValidationError("You must set a segment!")
        return

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            #print '+++', self.env.user.segment_by_company_open
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            #print '_domain_segment', self.env.user.company_id.id, segment_by_company_open
            domain = [('id', 'in', segment_by_company_open)]
        #print '>>> domains:', domain
        return domain

    def _get_default_segment_from_user(self):
        # TODO: search real default
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

    def _search_segment_user(self, operator, value):
        #user = self.env['res.users'].browse(value)
        user = self.env['res.users'].browse(self.env.context['user'])
        segment_by_company = json.loads(user.segment_by_company)[str(user.company_id.id)]
        res = [('segment_id', 'in', segment_by_company)]
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


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            #print '+++', self.env.user.segment_by_company_open
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            #print '_domain_segment', self.env.user.company_id.id, segment_by_company_open
            domain = [('id', 'in', segment_by_company_open)]
        #print '>>> domains:', domain
        return domain

    def _get_default_segment_from_user(self):
        # TODO: search real default
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

    def _search_segment_user(self, operator, value):
        #user = self.env['res.users'].browse(value)
        user = self.env['res.users'].browse(self.env.context['user'])
        #print 'account_move_line', user.id, user.company_id.id, user.company_id.name
        #print '+++', user.segment_by_company
        segment_by_company = json.loads(user.segment_by_company)[str(user.company_id.id)]
        res = [('segment_id', 'in', segment_by_company)]
        #print '>>>', res
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


    @api.depends('move_id.segment_id')
    def _update_segment_id(self):
        self.segment_id = self.move_id.segment_id

    segment_id = fields.Many2one(related='move_id.segment_id', index=True, store=True, readonly=True, domain=_domain_segment, default=2)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    campaign_segment = fields.Boolean(related='move_id.campaign_segment', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)


    #ugly hacks to avoid reconcilation between segments...
    def reconcile_partial(self, cr, uid, ids, type='auto', context=None, writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False):
        move_rec_obj = self.pool.get('account.move.reconcile')
        merges = []
        unmerge = []
        total = 0.0
        merges_rec = []
        company_list = []
        if context is None:
            context = {}

        segment_id = False
        campaign = False
        acc_exception = False

        for line in self.browse(cr, uid, ids, context=context):
            acc_exception = False
            if line.account_id.code[0:3] == '759' or uid == 1:
                acc_exception = True

            if not segment_id and line.segment_id:
                segment_id = line.segment_id.id
            if not campaign and line.campaign:
                campaign = line.campaign

            if not acc_exception:
                print('check concil', segment_id, line.segment_id)
                if segment_id != line.segment_id.id:
                    raise osv.except_osv(_('Warning!'), _('aml: To reconcile the entries segment_id must be the same'))
                if campaign != line.campaign:
                    raise osv.except_osv(_('Warning!'), _('aml: To reconcile the entries campaign must be the same'))    

        for line in self.browse(cr, uid, ids, context=context):
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
            company_list.append(line.company_id.id)

        for line in self.browse(cr, uid, ids, context=context):
            if line.account_id.currency_id:
                currency_id = line.account_id.currency_id
            else:
                currency_id = line.company_id.currency_id
            if line.reconcile_id:
                raise osv.except_osv(_('Warning'), _("Journal Item '%s' (id: %s), Move '%s' is already reconciled!") % (line.name, line.id, line.move_id.name))
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    if line2.state != 'valid':
                        raise osv.except_osv(_('Warning'), _("Journal Item '%s' (id: %s) cannot be used in a reconciliation as it is not balanced!") % (line2.name, line2.id))
                    if not line2.reconcile_id:
                        if line2.id not in merges:
                            merges.append(line2.id)
                        if line2.account_id.currency_id:
                            total += line2.amount_currency
                        else:
                            total += (line2.debit or 0.0) - (line2.credit or 0.0)
                merges_rec.append(line.reconcile_partial_id.id)
            else:
                unmerge.append(line.id)
                if line.account_id.currency_id:
                    total += line.amount_currency
                else:
                    total += (line.debit or 0.0) - (line.credit or 0.0)
        if self.pool.get('res.currency').is_zero(cr, uid, currency_id, total):
            res = self.reconcile(cr, uid, merges+unmerge, context=context, writeoff_acc_id=writeoff_acc_id, writeoff_period_id=writeoff_period_id, writeoff_journal_id=writeoff_journal_id)
            return res
        # marking the lines as reconciled does not change their validity, so there is no need
        # to revalidate their moves completely.
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid, {
            'type': type,
            'line_partial_ids': map(lambda x: (4,x,False), merges+unmerge)
        }, context=reconcile_context)
        move_rec_obj.reconcile_partial_check(cr, uid, [r_id] + merges_rec, context=reconcile_context)
        return r_id

    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context=None):
        print('^*/&%$ entro custom reconcile')
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_rec_obj = self.pool.get('account.move.reconcile')
        partner_obj = self.pool.get('res.partner')
        currency_obj = self.pool.get('res.currency')
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)
        credit = debit = 0.0
        currency = 0.0
        account_id = False
        partner_id = False
        if context is None:
            context = {}
        company_list = []

        segment_id = False
        campaign = False
        acc_exception = False

        for line in lines:
            acc_exception = False
            account = account_obj.browse(cr, uid, line['account_id']['id'], context=context)
            if account.code[0:3] == '759' or uid == 1:
                acc_exception = True

            if not segment_id and line['segment_id']:
                segment_id = line['segment_id']['id']
            if not campaign and line['campaign']:
                campaign = line['campaign']

            if not acc_exception:
                print('check concil', segment_id, line['segment_id'])
                if segment_id != line['segment_id']['id']:
                    raise osv.except_osv(_('Warning!'), _('aml: To reconcile the entries segment_id must be the same'))
                if campaign != line['campaign']:
                    raise osv.except_osv(_('Warning!'), _('aml: To reconcile the entries campaign must be the same'))

        for line in lines:
            if company_list and not line.company_id.id in company_list:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries company should be the same for all entries.'))
            company_list.append(line.company_id.id)
        for line in unrec_lines:
            if line.state <> 'valid':
                raise osv.except_osv(_('Error!'),
                        _('Entry "%s" is not valid !') % line.name)
            credit += line['credit']
            debit += line['debit']
            currency += line['amount_currency'] or 0.0
            account_id = line['account_id']['id']
            partner_id = (line['partner_id'] and line['partner_id']['id']) or False
        writeoff = debit - credit

        # Ifdate_p in context => take this date
        if context.has_key('date_p') and context['date_p']:
            date=context['date_p']
        else:
            date = time.strftime('%Y-%m-%d')

        cr.execute('SELECT account_id, reconcile_id '\
                   'FROM account_move_line '\
                   'WHERE id IN %s '\
                   'GROUP BY account_id, reconcile_id',
                   (tuple(ids), ))
        r = cr.fetchall()
        #TODO: move this check to a constraint in the account_move_reconcile object
        if len(r) != 1:
            raise osv.except_osv(_('Error'), _('Entries are not of the same account or already reconciled ! '))
        if not unrec_lines:
            raise osv.except_osv(_('Error!'), _('Entry is already reconciled.'))
        account = account_obj.browse(cr, uid, account_id, context=context)
        if not account.reconcile:
            raise osv.except_osv(_('Error'), _('The account is not defined to be reconciled !'))
        if r[0][1] != None:
            raise osv.except_osv(_('Error!'), _('Some entries are already reconciled.'))

        if (not currency_obj.is_zero(cr, uid, account.company_id.currency_id, writeoff)) or \
           (account.currency_id and (not currency_obj.is_zero(cr, uid, account.currency_id, currency))):
            if not writeoff_acc_id:
                raise osv.except_osv(_('Warning!'), _('You have to provide an account for the write off/exchange difference entry.'))
            if writeoff > 0:
                debit = writeoff
                credit = 0.0
                self_credit = writeoff
                self_debit = 0.0
            else:
                debit = 0.0
                credit = -writeoff
                self_credit = 0.0
                self_debit = -writeoff
            # If comment exist in context, take it
            if 'comment' in context and context['comment']:
                libelle = context['comment']
            else:
                libelle = _('Write-Off')

            cur_obj = self.pool.get('res.currency')
            cur_id = False
            amount_currency_writeoff = 0.0
            if context.get('company_currency_id',False) != context.get('currency_id',False):
                cur_id = context.get('currency_id',False)
                for line in unrec_lines:
                    if line.currency_id and line.currency_id.id == context.get('currency_id',False):
                        amount_currency_writeoff += line.amount_currency
                    else:
                        tmp_amount = cur_obj.compute(cr, uid, line.account_id.company_id.currency_id.id, context.get('currency_id',False), abs(line.debit-line.credit), context={'date': line.date})
                        amount_currency_writeoff += (line.debit > 0) and tmp_amount or -tmp_amount

            writeoff_lines = [
                (0, 0, {
                    'name': libelle,
                    'debit': self_debit,
                    'credit': self_credit,
                    'account_id': account_id,
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and -1 * amount_currency_writeoff or (account.currency_id.id and -1 * currency or 0.0),
                    'segment_id': segment_id,
                }),
                (0, 0, {
                    'name': libelle,
                    'debit': debit,
                    'credit': credit,
                    'account_id': writeoff_acc_id,
                    'analytic_account_id': context.get('analytic_id', False),
                    'date': date,
                    'partner_id': partner_id,
                    'currency_id': cur_id or (account.currency_id.id or False),
                    'amount_currency': amount_currency_writeoff and amount_currency_writeoff or (account.currency_id.id and currency or 0.0),
                    'segment_id': segment_id,
                })
            ]

            writeoff_move_id = move_obj.create(cr, uid, {
                'period_id': writeoff_period_id,
                'journal_id': writeoff_journal_id,
                'date':date,
                'state': 'draft',
                'line_id': writeoff_lines,
                'segment_id': segment_id,
            })

            writeoff_line_ids = self.search(cr, uid, [('move_id', '=', writeoff_move_id), ('account_id', '=', account_id)])
            if account_id == writeoff_acc_id:
                writeoff_line_ids = [writeoff_line_ids[1]]
            ids += writeoff_line_ids

        # marking the lines as reconciled does not change their validity, so there is no need
        # to revalidate their moves completely.
        reconcile_context = dict(context, novalidate=True)
        r_id = move_rec_obj.create(cr, uid, {'type': type}, context=reconcile_context)
        self.write(cr, uid, ids, {'reconcile_id': r_id, 'reconcile_partial_id': False}, context=reconcile_context)

        # the id of the move.reconcile is written in the move.line (self) by the create method above
        # because of the way the line_id are defined: (4, x, False)
        for id in ids:
            workflow.trg_trigger(uid, 'account.move.line', id, cr)

        if lines and lines[0]:
            partner_id = lines[0].partner_id and lines[0].partner_id.id or False
            if partner_id and not partner_obj.has_something_to_reconcile(cr, uid, partner_id, context=context):
                partner_obj.mark_as_reconciled(cr, uid, [partner_id], context=context)
        return r_id



class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('segment_id', 'partner_id')
    def _change_account_campaign(self):
        if self.segment_id.is_campaign == True:
            if self.partner_id.associate:
                self.account_id = self.env.user.company_id.account_associate_campaign.id
            else:
                self.account_id = self.env.user.company_id.account_provider_campaign.id
        else:
            if self.partner_id.associate:
                self.account_id = self.env.user.company_id.account_associate.id
            else:
                self.account_id = self.env.user.company_id.account_provider.id
        return

    @api.multi
    def write(self, vals):
        result = super(account_invoice, self).write(vals)
        for inv in self:
            if inv.move_id and \
               inv.segment_id != inv.move_id.segment_id:
                values = {
                    "segment_id": inv.segment_id.id,
                }
                inv.move_id.write(values)

        return result

    # add segments to payments - addons/account_voucher/invoice.py
    def invoice_pay_customer(self, cr, uid, ids, context=None):
        if not ids: return []
        dummy, view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_voucher', 'view_vendor_receipt_dialog_form')

        inv = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_("Pay Invoice"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'payment_expected_currency': inv.currency_id.id,
                'default_partner_id': self.pool.get('res.partner')._find_accounting_partner(inv.partner_id).id,
                'default_amount': inv.type in ('out_refund', 'in_refund') and -inv.residual or inv.residual,
                'default_reference': inv.name,
                'close_after_process': True,
                'invoice_type': inv.type,
                'invoice_id': inv.id,
                # segments
                'segment_id': inv.segment_id.id,
                'company_id': inv.company_id.id,
                'default_type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment',
                'type': inv.type in ('out_invoice','out_refund') and 'receipt' or 'payment'
            }
        }

    @api.one
    @api.constrains('segment_id', 'journal_id')
    def _check_segment_id(self):
        if not self.env.user.has_group('analytic_segment.group_analyticsegments_norestrictions'):
            if self.journal_id.check_segment_id:
                if self.journal_id.segment_id != self.segment_id:
                    raise ValidationError("Segment differs between journal and invoice!")
            if not self.segment_id:
                raise ValidationError("You must set a segment!")
        return

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            #print '+++', self.env.user.segment_by_company_open
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            #print '_domain_segment', self.env.user.company_id.id, segment_by_company_open
            domain = [('id', 'in', segment_by_company_open)]
        #print '>>> domains:', domain
        return domain

    def _get_default_segment_from_user(self):
        # TODO: search real default
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

    def _search_segment_user(self, operator, value):
        #user = self.env['res.users'].browse(value)
        user = self.env['res.users'].browse(self.env.context['user'])
        #print 'account_invoice', user.id, user.company_id.id, user.company_id.name
        #print '+++', user.segment_by_company
        segment_by_company = json.loads(user.segment_by_company)[str(user.company_id.id)]
        res = [('segment_id', 'in', segment_by_company)]
        #print '>>>', res
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


    segment_id = fields.Many2one('analytic_segment.segment', domain=_domain_segment, required=True, default=_get_default_segment_from_user) #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    campaign_segment = fields.Boolean(related='segment_id.is_campaign', readonly=True)
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)


class account_journal(models.Model):
    _inherit = 'account.journal'

    @api.one
    @api.constrains('segment_id')
    def _check_segment_id(self):
        if not self.env.user.has_group('analytic_segment.group_analyticsegments_norestrictions'):
            if not self.segment_id:
                raise ValidationError("You must set a Segment!")
        return

    def _domain_segment(self):
        if self.env.user.id == 1:
            domain = []
        else:
            #print '+++', self.env.user.segment_by_company_open
            segment_by_company_open = json.loads(self.env.user.segment_by_company_open)[str(self.env.user.company_id.id)]
            #print '_domain_segment', self.env.user.company_id.id, segment_by_company_open
            domain = [('id', 'in', segment_by_company_open)]
        #print '>>> domains:', domain
        return domain

    def _get_default_segment_from_user(self):
        # TODO: search real default
        for i in self.env.user.segment_ids:
            if i.company_id == self.env.user.company_id:
                return i.segment_id

    def _search_segment_user(self, operator, value):
        #user = self.env['res.users'].browse(value)
        user = self.env['res.users'].browse(self.env.context['user'])
        #print 'account_journal', user.id, user.company_id.id, user.company_id.name
        #print '+++', user.segment_by_company
        segment_by_company = json.loads(user.segment_by_company)[str(user.company_id.id)]
        res = [('segment_id', 'in', segment_by_company)]
        #print '>>>', res
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


    segment_id = fields.Many2one('analytic_segment.segment', index=True, domain=_domain_segment) #, required=True)
    segment = fields.Char(related='segment_id.segment', readonly=True)
    check_segment_id = fields.Boolean('Check segment', help='If active, it will check if invoice/move <=> journal segment are the same')
    segment_user_id = fields.Many2one('res.users', compute='_segment_user_id', search=_search_segment_user)


class AccountVoucher(models.Model):
    """Extends account_voucher class"""
    _inherit = 'account.voucher'


    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        # print 'entro voucher_move_line_create', context
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        #print '[CUSTOM] pre - for line in voucher,line_ids'
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = line.type =='dr' and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            #print line.move_line_id, line.move_line_id.territory_id.id, line.move_line_id.territory_level
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or ('Pago %s' % line.move_line_id.move_id.name) or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency != line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date,
                'segment_id': ctx['segment_id'],
                # 'segment_id': line.move_line_id.segment_id.id or 1,
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            #print 'voucher_line created!', voucher_line, line.move_line_id.id
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': (-1 if line.type == 'cr' else 1) * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,
                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        #print 'post - for line...'
        return (tot_line, rec_lst_ids)

    @api.multi
    def button_proforma_voucher(self):
        # print 'entro button_proforma_voucher', self, self.reference, self.number, self.move_ids

        cr, uid, context = self.env.args    
        # print context['segment_id']    

        if 'invoice_id' in context.keys():
            invoice = self.env['account.invoice'].browse(context['invoice_id'])

            if self.journal_id.segment_id.id != invoice.segment_id.id and self.journal_id.check_segment_id:
                raise osv.except_osv(_('Warning!'), _('To reconcile the entries territoriality/segments must be the same'))
            nu_context = context.copy()
            nu_context['segment_id'] = invoice.segment_id.id
            context = nu_context
            # print context['segment_id']
            self.proforma_voucher(context=context)
            # self.signal_workflow('proforma_voucher', context=context)

            # for line in invoice.payment_ids:
            #     move = line.move_id
            #     # print move
            #     # if not move.main_territory == invoice.main_territory:
            #     vals = {}
            #     vals['segment_id'] = invoice.segment_id.id

            #     # print 'vals 2', vals
            #     move.write(vals)
        return {'type': 'ir.actions.act_window_close'}

# class account_voucher(osv.osv):
#     _inherit = 'account.voucher'

    # add segments to move in payments - addons/account_voucher/account_voucher.py
    def account_move_get(self, cr, uid, voucher_id, context=None):
        '''
        This method prepare the creation of the account move related to the given voucher.

        :param voucher_id: Id of voucher for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        # print 'entro account_move_get', self, context
        seq_obj = self.pool.get('ir.sequence')
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        if voucher.number:
            name = voucher.number
        elif voucher.journal_id.sequence_id:
            if not voucher.journal_id.sequence_id.active:
                raise osv.except_osv(_('Configuration Error !'),
                    _('Please activate the sequence of selected journal !'))
            c = dict(context)
            c.update({'fiscalyear_id': voucher.period_id.fiscalyear_id.id})
            name = seq_obj.next_by_id(cr, uid, voucher.journal_id.sequence_id.id, context=c)
        else:
            raise osv.except_osv(_('Error!'),
                        _('Please define a sequence on the journal.'))
        if not voucher.reference:
            ref = name.replace('/','')
        else:
            ref = voucher.reference

        move = {
            'name': name,
            'journal_id': voucher.journal_id.id,
            'narration': voucher.narration,
            'date': voucher.date,
            'ref': ref,
            'period_id': voucher.period_id.id,
            'segment_id': context['segment_id'],
            # 'segment_id': voucher.journal_id.segment_id.id,
        }
        return move

class AccountAutomaticReconcile(osv.osv_memory):

    _inherit = 'account.automatic.reconcile'

    #TODO: cleanup and comment this code... For now, it is awfulllll
    # (way too complex, and really slow)...
    def do_reconcile(self, cr, uid, credits, debits, max_amount, power, writeoff_acc_id, period_id, journal_id, context=None):
        """
        for one value of a credit, check all debits, and combination of them
        depending on the power. It starts with a power of one and goes up
        to the max power allowed.
        """
        move_line_obj = self.pool.get('account.move.line')
        if context is None:
            context = {}
        def check2(value, move_list, power):
            def check(value, move_list, power):
                for i in range(len(move_list)):
                    move = move_list[i]
                    if power == 1:
                        if abs(value - move[1]) <= max_amount + 0.00001:
                            return [move[0]]
                    else:
                        del move_list[i]
                        res = check(value - move[1], move_list, power-1)
                        move_list[i:i] = [move]
                        if res:
                            res.append(move[0])
                            return res
                return False

            for p in range(1, power+1):
                res = check(value, move_list, p)
                if res:
                    return res
            return False


        def check4(list1, list2, power):
            """
            for a list of credit and debit and a given power, check if there
            are matching tuples of credit and debits, check all debits, and combination of them
            depending on the power. It starts with a power of one and goes up
            to the max power allowed.
            """
            def check3(value, list1, list2, list1power, power):
                for i in range(len(list1)):
                    move = list1[i]
                    if list1power == 1:
                        res = check2(value + move[1], list2, power - 1)
                        if res:
                            return ([move[0]], res)
                    else:
                        del list1[i]
                        res = check3(value + move[1], list1, list2, list1power-1, power-1)
                        list1[i:i] = [move]
                        if res:
                            x, y = res
                            x.append(move[0])
                            return (x, y)
                return False

            for p in range(1, power):
                res = check3(0, list1, list2, p, power)
                if res:
                    return res
            return False

        def check5(list1, list2, max_power):
            for p in range(2, max_power+1):
                res = check4(list1, list2, p)
                if res:
                    return res
            return False

        ok = True
        reconciled = 0
        while credits and debits and ok:
            res = check5(credits, debits, power)
            if res:
                #add checkeo de territorialidad
                if res[0].segment_id.id == res[1].segment_id.id:
                    move_line_obj.reconcile(cr, uid, res[0] + res[1], 'auto', writeoff_acc_id, period_id, journal_id, context)
                    reconciled += len(res[0]) + len(res[1])
                    credits = [(id, credit) for (id, credit) in credits if id not in res[0]]
                    debits = [(id, debit) for (id, debit) in debits if id not in res[1]]
                else:
                    ok = False
            else:
                ok = False
        return (reconciled, len(credits)+len(debits))

    def reconcile(self, cr, uid, ids, context=None):

        move_line_obj = self.pool.get('account.move.line')
        obj_model = self.pool.get('ir.model.data')
        if context is None:
            context = {}
        form = self.browse(cr, uid, ids, context=context)[0]
        max_amount = form.max_amount or 0.0
        power = form.power
        allow_write_off = form.allow_write_off
        reconciled = unreconciled = 0
        if not form.account_ids:
            raise osv.except_osv(_('User Error!'), _('You must select accounts to reconcile.'))
        for account_id in form.account_ids:
            params = (account_id.id,)
            if not allow_write_off:
                query = """SELECT partner_id FROM account_move_line WHERE account_id=%s AND reconcile_id IS NULL
                AND state <> 'draft' GROUP BY partner_id
                HAVING ABS(SUM(debit-credit)) = 0.0 AND count(*)>0"""
            else:
                query = """SELECT partner_id FROM account_move_line WHERE account_id=%s AND reconcile_id IS NULL
                AND state <> 'draft' GROUP BY partner_id
                HAVING ABS(SUM(debit-credit)) < %s AND count(*)>0"""
                params += (max_amount,)
            # reconcile automatically all transactions from partners whose balance is 0
            cr.execute(query, params)
            partner_ids = [id for (id,) in cr.fetchall()]
            to_break = False
            for partner_id in partner_ids:
                cr.execute(
                    "SELECT segment_id " \
                    "FROM account_move " \
                    "WHERE id in (SELECT move_id FROM account_move_line " \
                    "WHERE account_id=%s " \
                    "AND partner_id=%s " \
                    "AND state <> 'draft' " \
                    "AND reconcile_id IS NULL)",
                    (account_id.id, partner_id))
                segment_ids = [segment_id for (segment_id,) in cr.fetchall()]
                cr.execute(
                    "SELECT id " \
                    "FROM account_move_line " \
                    "WHERE account_id=%s " \
                    "AND partner_id=%s " \
                    "AND state <> 'draft' " \
                    "AND reconcile_id IS NULL",
                    (account_id.id, partner_id))
                line_ids = [id for (id,) in cr.fetchall()]
                if line_ids:
                    if (segment_ids==[segment_ids[0]] * len(segment_ids)):
                        reconciled += len(line_ids)
                        if allow_write_off:
                            move_line_obj.reconcile(cr, uid, line_ids, 'auto', form.writeoff_acc_id.id, form.period_id.id, form.journal_id.id, context)
                        else:
                            move_line_obj.reconcile_partial(cr, uid, line_ids, 'manual', context=context)
                    else:
                        to_break = True


            # get the list of partners who have more than one unreconciled transaction
            cr.execute(
                "SELECT partner_id " \
                "FROM account_move_line " \
                "WHERE account_id=%s " \
                "AND reconcile_id IS NULL " \
                "AND state <> 'draft' " \
                "AND partner_id IS NOT NULL " \
                "GROUP BY partner_id " \
                "HAVING count(*)>1",
                (account_id.id,))
            partner_ids = [id for (id,) in cr.fetchall()]
            #filter?
            for partner_id in partner_ids:
                # get the list of unreconciled 'debit transactions' for this partner
                cr.execute(
                    "SELECT id, debit " \
                    "FROM account_move_line " \
                    "WHERE account_id=%s " \
                    "AND partner_id=%s " \
                    "AND reconcile_id IS NULL " \
                    "AND state <> 'draft' " \
                    "AND debit > 0 " \
                    "ORDER BY date_maturity",
                    (account_id.id, partner_id))
                debits = cr.fetchall()

                # get the list of unreconciled 'credit transactions' for this partner
                cr.execute(
                    "SELECT id, credit " \
                    "FROM account_move_line " \
                    "WHERE account_id=%s " \
                    "AND partner_id=%s " \
                    "AND reconcile_id IS NULL " \
                    "AND state <> 'draft' " \
                    "AND credit > 0 " \
                    "ORDER BY date_maturity",
                    (account_id.id, partner_id))
                credits = cr.fetchall()

                if not to_break:
                    (rec, unrec) = self.do_reconcile(cr, uid, credits, debits, max_amount, power, form.writeoff_acc_id.id, form.period_id.id, form.journal_id.id, context)
                    reconciled += rec
                    unreconciled += unrec

            # add the number of transactions for partners who have only one
            # unreconciled transactions to the unreconciled count
            partner_filter = partner_ids and 'AND partner_id not in (%s)' % ','.join(map(str, filter(None, partner_ids))) or ''
            cr.execute(
                "SELECT count(*) " \
                "FROM account_move_line " \
                "WHERE account_id=%s " \
                "AND reconcile_id IS NULL " \
                "AND state <> 'draft' " + partner_filter,
                (account_id.id,))
            additional_unrec = cr.fetchone()[0]
            unreconciled = unreconciled + additional_unrec
        context = dict(context, reconciled=reconciled, unreconciled=unreconciled)
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','account_automatic_reconcile_view1')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.automatic.reconcile',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
