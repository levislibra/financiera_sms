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
	# Cuota en mora temprana
	sms_mora_temprana = fields.Boolean('Enviar sms en Mora Temprana?')
	sms_mora_temprana_count = fields.Integer('Cuantos sms se deberan enviar en Mora Temprana?')
	sms_mora_temprana_dias = fields.Integer('Cada cuntos dias se deben enviar los sms')
	sms_mora_temprana_text = fields.Text('Texto a enviar en Mora Temprana', size=120)
	# Cuota en mora media
	sms_mora_media = fields.Boolean('Enviar sms en Mora Media?')
	sms_mora_media_count = fields.Integer('Cuantos sms se deberan enviar en Mora Media?')
	sms_mora_media_dias = fields.Integer('Cada cuntos dias se deben enviar los sms')
	sms_mora_media_text = fields.Text('Texto a enviar en Mora Media', size=120)
	# Cuota en mora tardia
	sms_mora_tardia = fields.Boolean('Enviar sms en Mora Tardia?')
	sms_mora_tardia_count = fields.Integer('Cuantos sms se deberan enviar en Mora Tardia?')
	sms_mora_tardia_dias = fields.Integer('Cada cuntos dias se deben enviar los sms')
	sms_mora_tardia_text = fields.Text('Texto a enviar en Mora Tardia', size=120)
	# Cuota en incobrables
	sms_incobrable = fields.Boolean('Enviar sms en Incobrable?')
	sms_incobrable_count = fields.Integer('Cuantos sms se deberan enviar en Incobrable?')
	sms_incobrable_dias = fields.Integer('Cada cuntos dias se deben enviar los sms')
	sms_incobrable_text = fields.Text('Texto a enviar en Incobrable', size=120)


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
		for _id in cuota_ids:
			cuota_id = cuota_obj.browse(cr, uid, _id)
			sms_send = cuota_id.cliente_id.sms_prestamo_notification and cuota_id.prestamo_id.sms_prestamo_notification
			if sms_send:
				state_mora = cuota_id.state_mora
				fpcn_values = None
				if state_mora == 'preventiva' and self.sms_preventiva:
					self.send_sms(cuota_id, state_mora, cuota_id.sms_preventiva_count,
						cuota_id.sms_preventiva_dias, self.sms_preventiva_count,
						self.sms_preventiva_dias, self.sms_preventiva_text)
				elif state_mora == 'moraTemprana' and self.sms_mora_temprana:
					self.send_sms(cuota_id,	state_mora,	cuota_id.sms_mora_temprana_count,
						cuota_id.sms_mora_temprana_dias, self.sms_mora_temprana_count,
						self.sms_mora_temprana_dias, self.sms_mora_temprana_text)
				elif state_mora == 'moraMedia':
					self.send_sms(cuota_id,	state_mora,	cuota_id.sms_mora_media_count,
						cuota_id.sms_mora_media_dias, self.sms_mora_media_count,
						self.sms_mora_media_dias, self.sms_mora_media_text)
				elif state_mora == 'moraTardia':
					self.send_sms(cuota_id,	state_mora,	cuota_id.sms_mora_tardia_count,
						cuota_id.sms_mora_tardia_dias, self.sms_mora_tardia_count,
						self.sms_mora_tardia_dias, self.sms_mora_tardia_text)
				elif state_mora == 'incobrable':
					self.send_sms(cuota_id,	state_mora, cuota_id.sms_incobrable_count,
						cuota_id.sms_incobrable_dias, self.sms_incobrable_count,
						self.sms_incobrable_dias, self.sms_incobrable_text)

	@api.one
	def send_sms(self, cuota_id, state_mora, sms_cuota_count, sms_cuota_dias, sms_config_count, sms_config_dias, sms_config_text):
		nombre_cliente = cuota_id.cliente_id.name
		numero_cliente = cuota_id.cliente_id.mobile
		monto_cuota = cuota_id.saldo
		vencimiento_cuota = cuota_id.fecha_vencimiento
		vencimiento_cuota = datetime.strptime(vencimiento_cuota, "%Y-%m-%d")
		nro_cuota = cuota_id.numero_cuota
		sms_count_condition = sms_cuota_count < sms_config_count
		sms_dias_condition = sms_cuota_dias == 0 or sms_cuota_dias == sms_config_dias
		if sms_count_condition and sms_dias_condition:
			print "se envia mensajeeeeeeeeeeee"
			sms_text = sms_config_text
			sms_text = sms_text.replace("#nombre_cliente", nombre_cliente)
			sms_text = sms_text.replace("#monto_cuota", str(monto_cuota))
			sms_text = sms_text.replace("#vencimiento_cuota", vencimiento_cuota.strftime('%d de %b de %Y'))
			sms_text = sms_text.replace("#nro_cuota", str(nro_cuota))
			result = 'Demo'
			# params = {
			# 	'usuario': self.usuario,
			# 	'clave': self.password,
			# 	'tos': self.numero_cliente,
			# 	'texto': sms_text,
			# }
			# r = requests.get('http://servicio.smsmasivos.com.ar/enviar_sms.asp?api=1', params=params)
			#result = r.content
			fpcn_values = {
				'sms_mobil': numero_cliente,
				'sms_texto': sms_text,
				'sms_mora_tipo': state_mora,
				'sms_resultado': result,
			}
			sms_notification_id = self.env['financiera.prestamo.cuota.notificacion'].create(fpcn_values)
			cuota_id.sms_notification_ids = [sms_notification_id.id]
			if state_mora == 'preventiva':
				cuota_id.sms_preventiva_count += 1
				cuota_id.sms_preventiva_dias = 1
			elif state_mora == 'moraTemprana':
				cuota_id.sms_mora_temprana_count += 1
				cuota_id.sms_mora_temprana_dias = 1
			elif state_mora == 'moraMedia':
				cuota_id.sms_mora_media_count += 1
				cuota_id.sms_mora_media_dias = 1
			elif state_mora == 'moraTardia':
				cuota_id.sms_mora_tardia_count += 1
				cuota_id.sms_mora_tardia_dias = 1
			elif state_mora == 'incobrable':
				cuota_id.sms_incobrable_count += 1
				cuota_id.sms_incobrable_dias = 1
		else:
			if state_mora == 'preventiva':
				cuota_id.sms_preventiva_dias += 1
			elif state_mora == 'moraTemprana':
				cuota_id.sms_mora_temprana_dias += 1
			elif state_mora == 'moraMedia':
				cuota_id.sms_mora_media_dias += 1
			elif state_mora == 'moraTardia':
				cuota_id.sms_mora_tardia_dias += 1
			elif state_mora == 'incobrable':
				cuota_id.sms_incobrable_dias += 1

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
	# SMS Preventiva
	sms_preventiva_count = fields.Integer('Sms enviados en Preventiva?', default=0)
	sms_preventiva_dias = fields.Integer('Dias desde el ultimo envio', default=0)
	# SMS Mora Temprana
	sms_mora_temprana_count = fields.Integer('Sms enviados en Mora Temprana?', default=0)
	sms_mora_temprana_dias = fields.Integer('Dias desde el ultimo envio', default=0)
	# SMS Mora Media
	sms_mora_media_count = fields.Integer('Sms enviados en Mora Media?', default=0)
	sms_mora_media_dias = fields.Integer('Dias desde el ultimo envio', default=0)	
	# SMS Mora Tardia
	sms_mora_tardia_count = fields.Integer('Sms enviados en Mora Tardia?', default=0)
	sms_mora_tardia_dias = fields.Integer('Dias desde el ultimo envio', default=0)
	# SMS Incobrable
	sms_incobrable_count = fields.Integer('Sms enviados en Incobrable?', default=0)
	sms_incobrable_dias = fields.Integer('Dias desde el ultimo envio', default=0)

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