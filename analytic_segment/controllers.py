# -*- coding: utf-8 -*-
from openerp import http

# class AnalyticSegment(http.Controller):
#     @http.route('/analytic_segment/analytic_segment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/analytic_segment/analytic_segment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('analytic_segment.listing', {
#             'root': '/analytic_segment/analytic_segment',
#             'objects': http.request.env['analytic_segment.analytic_segment'].search([]),
#         })

#     @http.route('/analytic_segment/analytic_segment/objects/<model("analytic_segment.analytic_segment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('analytic_segment.object', {
#             'object': obj
#         })