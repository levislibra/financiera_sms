# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraSmsMessageResponse(models.Model):
	_name = 'financiera.sms.message.response'

	_order = 'id desc'
	name = fields.Char("Nombre")
	partner_id = fields.Many2one('res.partner', 'Cliente')
	mobile = fields.Char('Movil')
	text = fields.Text('Texto')
	id_sms_masivos = fields.Integer('Id Sms Maviso')
	id_interno = fields.Char('Id interno')
	sms_message_id = fields.Many2one('financiera.sms.message', 'Respuesta al mensaje')
	company_id = fields.Many2one('res.company', 'Empresa')

	@api.model
	def create(self, values):
		rec = super(FinancieraSmsMessageResponse, self).create(values)
		rec.update({
			'name': 'RSP ' + str(rec.id).zfill(6),
		})
		return rec
