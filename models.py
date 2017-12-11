# -*- coding: utf-8 -*-
# More simple segment model to use in odoo analytic and no analytic objects

from openerp import models, fields, api

PATTERN = ['%i', '%02i', '%06i']
MAX_LEVEL = len(PATTERN)

class analytic_segment(models.Model):
    _name = 'analytic_segment.segment'
    _description = 'Segments for analytic porpouse'

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            name = '%s [%s]' % (obj.name, obj.type_id.name)
            res.append((obj.id, name))
        return res

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
        if self.virtual or not self.type_id:
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

    # fields
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    type_id = fields.Many2one('analytic_segment.type', required=True) # first segment
    segment = fields.Char(compute="_get_fullcode", store=True, readonly=True)
    level = fields.Integer(compute="_get_level", store=True, readonly=True)
    level_parent = fields.Integer(related="type_id.level_parent", readonly=True)
    virtual = fields.Boolean(default=False) # we can't use virtual segments
    blocked = fields.Boolean(default=False)
    parent_id = fields.Many2one('analytic_segment.segment')
    child_ids = fields.One2many('analytic_segment.segment', 'parent_id')
    # one2manys to core models
    analytic_ids = fields.One2many('account.analytic.account', 'segment_id')


class analytic_segment(models.Model):
    _name = 'analytic_segment.type'
    _description = 'Type of segments for analytic porpouse'

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    level_parent = fields.Integer(required=True)
    segment_ids = fields.One2many('analytic_segment.segment', 'type_id')
