# -*- coding: utf-8 -*-

from openerp import models, fields, api

class FinancieraSmsMessageResponse(models.Model):
	_name = 'financiera.sms.message.response'

	_order = 'id desc'
	name = fields.Char("Nombre")
	partner_id = fields.Many2one('res.partner', 'Cliente')
	mobile = fields.Char('Movil')
	text = fields.Text('Texto')
	date = fields.Datetime('Fecha')
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

	@api.model
	def _cron_read_response(self):
		cr = self.env.cr
		uid = self.env.uid
		company_obj = self.pool.get('res.company')
		company_ids = company_obj.search(cr, uid, [])
		for _id in company_ids:
			company_id = company_obj.browse(cr, uid, _id)
			if len(company_id.sms_configuracion_id) > 0:
				config_id = company_id.sms_configuracion_id
				params = {
					'usuario': config_id.usuario,
					'clave': config_id.password,
					'solonoleidos': 1,
					'marcarcomoleidos': 1,
					'traeridinterno': 1,
				}
				r = requests.get('http://servicio.smsmasivos.com.ar/obtener_sms_entrada.asp?', params=params)
				if r.status_code == 200:
					for responses in r.text.split('\n'):
						value = responses.split('\t')
						if len(value) >= 4:
							partner_obj = self.pool.get('res.partner')
							partner_ids = partner_obj.search(cr, uid, [
								('mobile', '=', value[0])
							])
							partner_id = None
							if len(partner_ids) > 0:
								partner_id = partner_ids[0]
							params = {
								'partner_id': partner_id,
								'mobile': value[0],
								'text': value[1],
								'date': value[2],
								'id_sms_masivos': value[3],
								'id_interno': value[4].replace('\r', ''),
								'company_id': self.env.user.company_id.id,
							}
							response_id = self.env['financiera.sms.message.response'].create(params)
							sms_obj = self.pool.get('financiera.sms.message')
							sms_ids = sms_obj.search(cr, uid, [
								('id_interno', '=', response_id.id_interno)
							])
							if len(sms_ids) > 0:
								response_id.sms_message_id = sms_ids[0]
								# Comprobar si la respuesta es correcta
								sms_message_id = sms_obj.browse(cr, uid, sms_ids[0])
								if len(sms_message_id.prestamo_id) > 0:
									prestamo_id = sms_message_id.prestamo_id
									respuesta_correcta = config_id.metodo_sms_tc_respuesta_correcta.replace('{{1}}', prestamo_id.email_tc_code)
									if response_id.text == respuesta_correcta:
										prestamo_id.sms_response_confirma_tc()
