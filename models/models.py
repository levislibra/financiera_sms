# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime, timedelta
from dateutil import relativedelta
from openerp.exceptions import UserError, ValidationError
import time
import requests

class FinancieraSms(models.Model):
	_name = 'financiera.sms'

	name = fields.Char('Nombre', defualt='Configuracion general', readonly=True, required=True)
	usuario = fields.Char('Usuario', required=True)
	password = fields.Char('Password', required=True)
	sms_saldo = fields.Integer('SMS restantes')
	sms_numero_test = fields.Char('Movil test')
	sms_texto_test = fields.Char('Mensaje test', size=120)
	# Cuota en preventiva
	sms_preventiva = fields.Boolean('Enviar sms en Preventiva?')
	sms_preventiva_count = fields.Integer('Cuantos sms se deberan enviar en Preventiva?')
	sms_preventiva_dias = fields.Integer('Cada cuntos dias se deben enviar los sms')
	sms_preventiva_text = fields.Text('Texto a enviar en Preventiva', size=120)

	@api.one
	def actualizar_saldo(self):
		r = requests.get('http://servicio.smsmasivos.com.ar/obtener_saldo.asp?', params={'usuario': self.usuario, 'clave': self.password})
		self.sms_saldo = int(r.content)

	@api.one
	def send_sms_test(self):
		params = {
			'usuario': self.usuario,
			'clave': self.password,
			'tos': self.sms_numero_test,
			'texto': self.sms_texto_test,
		}
		r = requests.get('http://servicio.smsmasivos.com.ar/enviar_sms.asp?api=1', params=params)
		#print r.content == 'OK'

	@api.one
	def all_notification(self):
		cr = self.env.cr
		uid = self.env.uid
		cuota_obj = self.pool.get('financiera.prestamo.cuota')
		cuota_ids = cuota_obj.search(cr, uid, [
			('state', 'in', ('activa', 'facturado')),
			('state_mora', '!=', 'normal'),
		])
		print "ALL NOTIFICATION"
		print cuota_ids
		for _id in cuota_ids:
			cuota_id = cuota_obj.browse(cr, uid, _id)
			sms_send = cuota_id.cliente_id.sms_prestamo_notification and cuota_id.prestamo_id.sms_prestamo_notification
			print "sms_send:: "+str(sms_send)
			if sms_send:
				nombre_cliente = cuota_id.cliente_id.name
				numero_cliente = cuota_id.cliente_id.mobile
				monto_cuota = cuota_id.saldo
				vencimiento_cuota = cuota_id.fecha_vencimiento
				nro_cuota = cuota_id.numero_cuota
				state_mora = cuota_id.state_mora
				fpcn_values = None
				if state_mora == 'preventiva' and self.sms_preventiva:
					print "estamos en preventiva y sms_preventiva send"
					sms_count_condition = cuota_id.sms_preventiva_count < self.sms_preventiva_count
					sms_dias_condition = cuota_id.sms_preventiva_dias == 0 or cuota_id.sms_preventiva_dias == self.sms_preventiva_dias
					if sms_count_condition and sms_dias_condition:
						print "se envia mensajeeeeeeeeeeee"
						sms_preventiva_text = self.sms_preventiva_text
						sms_preventiva_text = sms_preventiva_text.replace("#nombre_cliente", nombre_cliente)
						sms_preventiva_text = sms_preventiva_text.replace("#monto_cuota", str(monto_cuota))
						sms_preventiva_text = sms_preventiva_text.replace("#vencimiento_cuota", str(vencimiento_cuota))
						sms_preventiva_text = sms_preventiva_text.replace("#nro_cuota", str(nro_cuota))
						# params = {
						# 	'usuario': self.usuario,
						# 	'clave': self.password,
						# 	'tos': self.numero_cliente,
						# 	'texto': self.sms_preventiva_text,
						# }
						# r = requests.get('http://servicio.smsmasivos.com.ar/enviar_sms.asp?api=1', params=params)
						fpcn_values = {
							#'sms_cuota_id': cuota_id.id,
							'sms_mobil': numero_cliente,
							'sms_texto': sms_preventiva_text,
							'sms_mora_tipo': 'preventiva',
							'sms_resultado': 'Demo',
						}
						cuota_id.sms_preventiva_count += 1
						cuota_id.sms_preventiva_dias = 1
					else:
						cuota_id.sms_preventiva_dias += 1
				elif state_mora == 'moraTemprana':
					pass
				elif state_mora == 'moraMedia':
					pass
				elif state_mora == 'moraTardia':
					pass
				elif state_mora == 'incobrable':
					pass
				if fpcn_values != None:
					sms_notification_id = self.env['financiera.prestamo.cuota.notificacion'].create(fpcn_values)
					cuota_id.sms_notification_ids = [sms_notification_id.id]
			
class ExtendsFinancieraPrestamo(models.Model):
	_name = 'financiera.prestamo'
	_inherit = 'financiera.prestamo'

	sms_prestamo_notification = fields.Boolean('Enviar sms')

	@api.one
	@api.onchange('cliente_id')
	def _onchange_sms_prestamo_notification(self):
		self.sms_prestamo_notification = self.cliente_id.sms_prestamo_notification

class ExtendsFinancieraPrestamoCuota(models.Model):
	_name = 'financiera.prestamo.cuota'
	_inherit = 'financiera.prestamo.cuota'

	sms_notification_ids = fields.One2many("financiera.prestamo.cuota.notificacion", "sms_cuota_id", "Notificaciones sms")
	
	sms_preventiva_count = fields.Integer('Sms enviados en Preventiva?', default=0)
	sms_preventiva_dias = fields.Integer('Dias desde el ultimo envio', default=0)

class FinancieraPrestamoCuotaNotificacion(models.Model):
	_name = 'financiera.prestamo.cuota.notificacion'

	sms_cuota_id = fields.Many2one("financiera.prestamo.cuota", "Cuota")
	sms_cliente_id = fields.Many2one(related='sms_cuota_id.cliente_id', readonly=True)
	sms_mobil = fields.Char('Movil', size=10)
	sms_fecha = fields.Date('Fecha', required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
	sms_texto = fields.Char('Mensaje', size=160)
	sms_mora_tipo = fields.Selection([('normal', 'Normal'), ('preventiva', 'Preventiva'), ('moraTemprana', 'Mora temprana'), ('moraMedia', 'Mora media'), ('moraTardia', 'Mora tardia'), ('incobrable', 'Incobrable')], string='Estado')
	sms_resultado = fields.Char('Resultado')

class ExtendsResPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	sms_prestamo_notification = fields.Boolean('Enviar sms', default=True)