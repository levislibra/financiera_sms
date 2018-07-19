# -*- coding: utf-8 -*-
from openerp import http

# class FinancieraSms(http.Controller):
#     @http.route('/financiera_sms/financiera_sms/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/financiera_sms/financiera_sms/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('financiera_sms.listing', {
#             'root': '/financiera_sms/financiera_sms',
#             'objects': http.request.env['financiera_sms.financiera_sms'].search([]),
#         })

#     @http.route('/financiera_sms/financiera_sms/objects/<model("financiera_sms.financiera_sms"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('financiera_sms.object', {
#             'object': obj
#         })