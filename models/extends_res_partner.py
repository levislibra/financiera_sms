# -*- coding: utf-8 -*-

from openerp import models, api
from random import randint

class ExtendsResPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	# Documentada en Librasoft API
	@api.one
	def button_solicitar_codigo(self):
		sms_configuracion_id = self.company_id.sms_configuracion_id
		if sms_configuracion_id.validacion_celular_codigo:
			sms_message_values = {
				'partner_id': self.id,
				'config_id': sms_configuracion_id.id,
				'to': self.app_numero_celular,
				'tipo': 'Codigo VC',
				'company_id': self.company_id.id,
			}
			message_id = self.env['financiera.sms.message'].create(sms_message_values)
			n = 4
			range_start = 10**(n-1)
			range_end = (10**n)-1
			codigo = str(randint(range_start, range_end)).zfill(n)
			self.app_codigo = codigo
			message_id.set_message_code(sms_configuracion_id.validacion_celular_mensaje, codigo)
			message_id.send()
		return True
	
	@api.multi
	def wizard_enviar_sms(self):
		self.ensure_one()
		params = {}
		view_id = self.env['financiera.pagos.360.sms.prestamo.wizard']
		new = view_id.create(params)
		return {
			'name': 'Enviar sms',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'financiera.pagos.360.sms.prestamo.wizard',
			'res_id': new.id,
			'views': [(view_id.id, 'form')],
			'view_id': view_id.id,
			'target': 'new',
		}