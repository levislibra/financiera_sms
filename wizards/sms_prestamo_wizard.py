# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError


class FinancieraPagos360SmsPrestamoWizard(models.TransientModel):
	_name = 'financiera.pagos.360.sms.prestamo.wizard'
	
	template_id = fields.Many2one('financiera.sms.message.masive.template', 'Plantilla')
	tipo = fields.Char('Tipo de mensaje')
	body_count_available = fields.Integer('Caracteres restantes', compute='_compute_body_count_available')
	body = fields.Text('Mensaje', size=160)
	is_html = fields.Boolean('Adjuntar html')
	html = fields.Text('Html')
	send_now = fields.Boolean("Enviar ahora", default=True)

	@api.multi
	def send_sms(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids')
		active_model = context.get('active_model')
		print("active_model: ", active_model)
		print("active_ids: ", active_ids)
		if active_model == 'financiera.prestamo':
			partner_ids = []
			for _id in active_ids:
				prestamo_id = self.env['financiera.prestamo'].browse(_id)
				partner_ids.append(prestamo_id.partner_id.id)
		if active_model == 'res.partner':
			partner_ids = active_ids
		sms_message_masive_values = {
			'partner_ids': [(6,0, partner_ids)],
			'template_id': self.template_id.id,
			'tipo': self.tipo,
			'body': self.body,
			'is_html': self.is_html,
			'html': self.html,
		}
		message_masive_id = self.env['financiera.sms.message.masive'].create(sms_message_masive_values)
		if self.send_now:
			message_masive_id.send_messages()


	@api.onchange('body', 'is_html')
	def _compute_body_count_available(self):
		if self.body:
			if not self.is_html:
				self.body_count_available = 160 - len(self.body)
			else:
				self.body_count_available = 137 - len(self.body)
		else:
			if not self.is_html:
				self.body_count_available = 160
			else:
				self.body_count_available = 137

	@api.constrains('body', 'is_html')
	def _check_body(self):
		if self.body:
			if self.body_count_available < 0:
				raise UserError("Debe borrar al menos %s caracteres."%str(abs(self.body_count_available)))

	@api.onchange('template_id')
	def _onchange_template_id(self):
		if self.template_id.tipo:
			self.tipo = self.template_id.tipo
		if self.template_id.body:
			self.body = self.template_id.body