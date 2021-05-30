# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
import logging
import json

_logger = logging.getLogger(__name__)
# /financiera.sms/webhook?numero=*ORIGEN*&respuesta=*TEXTO*&idinterno=*IDINTERNO*
# @http.route('/mail/<string:res_model>/<int:res_id>/avatar/<int:partner_id>', type='http', auth='public')
#     def avatar(self, res_model, res_id, partner_id):
class FinancieraSMSWebhookController(http.Controller):

	@http.route("/financiera.sms/webhook/<string:origen>/<string:texto>/<int:idinterno>", type='http', auth='public')
	def webhook_listener(self, origen, texto, idinterno):
		_logger.info('SMS: nuevo webhook.')
		print("Numero: ", origen)
		print("Texto: ", texto)
		print("idinterno: ", idinterno)
		sms_id = request.env['financiera.sms.message'].sudo().browse(idinterno)
		if sms_id:
			sms_id.create_response(origen, texto)
		return json.dumps("OK")

