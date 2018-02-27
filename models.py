# -*- coding: utf-8 -*-
# More simple segment model to use in odoo analytic and no analytic objects

from openerp import models, fields, api
from random import random

PATTERN = ['%i', '%02i', '%06i']
MAX_LEVEL = len(PATTERN)

class analytic_template(models.Model):
    _name = 'analytic_segment.template'
    _description = 'Segments for analytic porpouse'
    _rec_name = 'display_name'
    _order = 'segment'

    @api.depends('name', 'type_id')
    @api.multi
    def display_name(self):
        res = []
        for obj in self:
            obj.display_name = '%s [%s]' % (obj.name, obj.type_id.name)

    """
    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            name = '%s [%s]' % (obj.name, obj.type_id.name)
            res.append((obj.id, name))
        return res
    """

    @api.onchange('type_id')
    def _set_level(self):
        # only select stuff from your upper level
        self.parent_id = ''
        res = {}
        res['domain'] = {
            'parent_id': [('level', '=', self.type_id.level_parent)]
        }
        return res

    @api.depends('parent_id')
    @api.one
    def _get_level(self):
        """recursively get depth level in tree"""
        level = 1
        parent = self.parent_id
        while parent:
            level += 1
            parent = parent.parent_id
        self.level = level


    @api.depends('parent_id', 'code', 'type_id')
    @api.one
    def _get_fullcode(self):
        """recursively get depth level in tree"""
        # segment is empty for virtual ones
        if not self.type_id:
            self.segment = ''
        else:
            fullcode = [self.code]
            parent = self.parent_id
            while parent:
                fullcode.append(parent.code)
                parent = parent.parent_id

            # three segments...
            newfullcode = [PATTERN[0] % int(self.type_id.code)]
            if self.type_id.code in ['1', '2']:
                newfullcode.append(PATTERN[1] % int(self.code))
                newfullcode.append(PATTERN[2] % 0)
            elif self.type_id.level_parent == 2:
                newfullcode.append(PATTERN[1] % int(self.parent_id.code))
                newfullcode.append(PATTERN[2] % int(self.code))
            else:
                newfullcode.append(PATTERN[1] % int(self.parent_id.parent_id.code))
                newfullcode.append(PATTERN[2] % int(self.code))

            self.segment = '.'.join(newfullcode)

    def get_childs(self):
        """return a list with childrens, grandchildrens, etc."""
        res = [self]
        for obj in self.child_ids:
            res.append(obj)
            more_childs = obj.get_childs() # recursive!
            if more_childs:
                for child in more_childs:
                    res.append(child)
        return res

    def get_childs_ids(self):
        """return a list with ids of childrens, grandchildrens, etc."""
        res = [self.id]
        for obj in self.child_ids:
            res.append(obj.id)
            more_childs = obj.get_childs() # recursive!
            if more_childs:
                for child in more_childs:
                    res.append(child.id)
        return res

    @api.model
    def create(self, values):
        res = super(analytic_template, self).create(values)
        vals = {
            'segment_tmpl_id': res.id
        }
        # create a segment without campaign related to this template
        self.env['analytic_segment.segment'].create(vals)
        return res

    # fields
    code = fields.Char(required=True)
    display_name = fields.Char(compute=display_name, store=True, string="Name")
    name = fields.Char(required=True)
    type_id = fields.Many2one('analytic_segment.type', string='Type', required=True) # first segment
    segment = fields.Char(compute="_get_fullcode", store=True, readonly=True)
    level = fields.Integer(compute="_get_level", store=True, readonly=True)
    level_parent = fields.Integer(related="type_id.level_parent", readonly=True)
    virtual = fields.Boolean(default=False) # we can't use virtual segments
    blocked = fields.Boolean(default=False)
    parent_id = fields.Many2one('analytic_segment.template')
    child_ids = fields.One2many('analytic_segment.template', 'parent_id')
    # one2manys to core models
    analytic_ids = fields.One2many('account.analytic.account', 'segment_id')
    # base
    user_ids = fields.One2many('analytic_segment.user', 'segment_id')
    

class analytic_segment(models.Model):
    # TODO: add campaign to name
    _name = 'analytic_segment.segment'
    _description = 'Segments for analytic porpouse'
    _inherits = {'analytic_segment.template': 'segment_tmpl_id'}
    _rec_name = 'display_name'

    @api.multi
    def _is_campaign(self):
        for obj in self:
            obj.is_campaign = obj.campaign_id and True or False

    # override this function from template to add 3 if campaign is True
    @api.depends('parent_id', 'code', 'type_id', 'campaign_id', 'is_campaign')
    @api.one
    def _get_fullcode(self):
        """recursively get depth level in tree"""
        # segment is empty for virtual ones
        if not self.type_id:
            self.segment = ''
        else:
            fullcode = [self.code]
            parent = self.parent_id
            while parent:
                fullcode.append(parent.code)
                parent = parent.parent_id

            # three segments...
            newfullcode = [PATTERN[0] % (int(self.type_id.code) + (self.is_campaign and 3 or 0))]
            if self.type_id.code in ['1', '2']:
                newfullcode.append(PATTERN[1] % int(self.code))
                newfullcode.append(PATTERN[2] % 0)
            elif self.type_id.level_parent == 2:
                newfullcode.append(PATTERN[1] % int(self.parent_id.code))
                newfullcode.append(PATTERN[2] % int(self.code))
            else:
                newfullcode.append(PATTERN[1] % int(self.parent_id.parent_id.code))
                newfullcode.append(PATTERN[2] % int(self.code))

            self.segment = '.'.join(newfullcode)

    @api.depends('campaign_id', 'segment_tmpl_id')
    @api.multi
    def display_name(self):
        res = []
        for obj in self:
            if obj.campaign_id:
                obj.display_name = '%s <%s>' % (obj.segment_tmpl_id.display_name, obj.campaign_id.name)
            else:
                obj.display_name = obj.segment_tmpl_id.display_name

    display_name = fields.Char(compute=display_name, store=True, string="Name")
    segment_tmpl_id = fields.Many2one('analytic_segment.template', ondelete="cascade", required=True)
    segment = fields.Char(compute="_get_fullcode", readonly=True)
    campaign_id = fields.Many2one('analytic_segment.campaign')
    is_campaign = fields.Boolean(compute='_is_campaign')
    user_ids = fields.One2many('analytic_segment.user', 'segment_id')
    #user_id = fields.Many2one('analytic_segment.user') # to support calculate field
    # base
    #company_ids = fields.Many2many('res.company', 'segment_company_rel')


class analytic_segment_type(models.Model):
    _name = 'analytic_segment.type'
    _description = 'Type of segments for analytic porpouse'

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    level_parent = fields.Integer(required=True)
    segment_ids = fields.One2many('analytic_segment.segment', 'type_id')


class analytic_segment_user(models.Model):
    _name = 'analytic_segment.user'
    _description = 'Collection of segments by user'

    # TODO: Fix selection when company_id is set (not a new row)
    @api.multi
    def _company_segment_ids(self):
        for obj in self:
            segment_tmpl_ids = []
            for s in obj.company_id.segment_ids:
                segment_tmpl_ids += s.segment_tmpl_id.get_childs_ids()
            segments = obj.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
            obj.company_segment_ids = segments

    @api.onchange('company_id')
    def company_id_onchange(self):
        print 'ON CHANGE!!!'
        segment_tmpl_ids = []
        res = {}
        for s in self.company_id.segment_ids:
            segment_tmpl_ids += s.segment_tmpl_id.get_childs_ids()
        segment_ids = self.env['analytic_segment.segment'].search([('segment_tmpl_id', 'in', segment_tmpl_ids)])
        res['domain'] = {
            'segment_id': [('id', 'in', [i.id for i in segment_ids])]
        }
        #res['warning'] = {'title': 'Error!', 'message': 'Something went wrong! Please check your data'}
        self.segment_id = None
        return res

    company_id = fields.Many2one('res.company')
    segment_id = fields.Many2one('analytic_segment.segment') #, domain="[('id', 'in', 'company_segment_ids[0][2]')]") # with campaign
    segment = fields.Char(related='segment_id.segment', readonly=True) #TODO: store
    campaign_id = fields.Many2one(related='segment_id.campaign_id', readonly=True) #TODO: store
    user_id = fields.Many2one('res.users')
    company_segment_ids = fields.One2many('analytic_segment.segment', compute='_company_segment_ids')


class analytic_segment_campaign(models.Model):
    _name = 'analytic_segment.campaign'
    _description = 'Data for campaigns'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([('open', 'Open'), ('closed', 'Closed'), ('disabled', 'Disabled')])
    date_start = fields.Date()
    date_end = fields.Date()
    # segments
    segment_top = fields.Many2one('analytic_segment.template')
    segment_ids = fields.One2many('analytic_segment.segment', 'campaign_id')
    # base
    company_id = fields.Many2one('res.company', required=True)

    @api.model
    def create(self, values):
        segment_top = self.env['analytic_segment.template'].browse(values['segment_top'])
        if segment_top:
            segments = segment_top.get_childs()
            # remove segments
            for s in self.segment_ids:
                s.unlink()
            # create segments
            s_ids = []
            for s in segments:
                vals = {
                    'campaign_id': self.id,
                    'segment_tmpl_id': s.id
                }
                n = self.env['analytic_segment.segment'].create(vals)
                s_ids.append(n.id)
            values['segment_ids'] = [(6, 0, s_ids)]
        res_id = super(analytic_segment_campaign, self).create(values)
        return res_id

    @api.multi
    def write(self, values, context=None):
        if values.has_key('segment_top') and self.segment_top.id != values['segment_top']:
            segment_top = self.env['analytic_segment.template'].browse(values['segment_top'])
            segments = [segment_top] + segment_top.get_childs()
            # remove segments
            for s in self.segment_ids:
                s.unlink()
            # create segments
            s_ids = []
            for s in segments:
                vals = {
                    'campaign_id': self.id,
                    'segment_tmpl_id': s.id
                }
                n = self.env['analytic_segment.segment'].create(vals)
                s_ids.append(n.id)
            values['segment_ids'] = [(6, 0, s_ids)]
        rec = super(analytic_segment_campaign, self).write(values)
        return rec
        

    # TODO: override create and write functions in order to generate segments with campaign info
