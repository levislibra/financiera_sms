# -*- coding: utf-8 -*-

from openerp import models, api

class ExtendsMailMail(models.Model):
	_name = 'mail.mail'
	_inherit = 'mail.mail'

	@api.one
	def send(self, auto_commit=False, raise_exception=False):
		context = dict(self._context or {})
		active_model = context.get('active_model')
		sub_action = context.get('sub_action')
		active_id = context.get('active_id')
		super(ExtendsMailMail, self).send(auto_commit=False, raise_exception=False)
		if active_model == 'financiera.prestamo' and sub_action and 'tc_sent' in sub_action:
			cr = self.env.cr
			uid = self.env.uid
			prestamo_obj = self.pool.get('financiera.prestamo')
			prestamo_id = prestamo_obj.browse(cr, uid, active_id)
			if sub_action == 'tc_sent':
				sms_configuracion_id = prestamo_id.company_id.sms_configuracion_id
				if sms_configuracion_id.tc_codigo and prestamo_id.partner_id in self.recipient_ids:
					sms_message_values = {
						'partner_id': prestamo_id.partner_id.id,
						'config_id': sms_configuracion_id.id,
						'to': prestamo_id.partner_id.mobile,
						'tipo': 'Codigo TC',
						'company_id': prestamo_id.company_id.id,
					}
					message_id = self.env['financiera.sms.message'].create(sms_message_values)
					message_id.set_message_code(sms_configuracion_id.tc_mensaje, prestamo_id.email_tc_code)
					message_id.send()
					prestamo_id.email_tc_code_sent = True