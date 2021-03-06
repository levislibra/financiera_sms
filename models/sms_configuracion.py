# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil import relativedelta
import time
import requests

class FinancieraSmsConfig(models.Model):
	_name = 'financiera.sms.config'

	name = fields.Char('Nombre')
	usuario = fields.Char('Usuario')
	password = fields.Char('Password')
	sms_saldo = fields.Integer('SMS restantes')
	sms_numero_test = fields.Char('Movil destino de prueba')
	sms_texto_test = fields.Char('Mensaje de prueba', size=120)
	company_id = fields.Many2one('res.company', 'Empresa')
	# Mensajes
	# Aviso preventivo
	preventivo_activar = fields.Boolean("Activar mensaje preventivo")
	preventivo_mensaje = fields.Text('Mensaje')
	preventivo_dias_antes = fields.Integer("Dias antes del vencimiento")
	preventivo_activar_segundo_envio = fields.Boolean("Activar segundo envio")
	preventivo_segundo_envio_dias_antes = fields.Integer("Dias antes del vencimiento")
	preventivo_var_1 = fields.Selection([('nombre_cliente', 'Nombre de cliente')],
		'{{1}}', default='nombre_cliente',
		help="Al usar {{1}}, sera reemplazado por este valor")
	preventivo_var_2 = fields.Selection([
		('monto_cuota', 'Monto de la cuota')],
		'{{2}}', default='monto_cuota',
		help="Al usar {{2}}, sera reemplazado por este valor")
	preventivo_var_3 = fields.Selection([
		('fecha_vencimiento', 'Fecha de vencimiento')],
		'{{3}}', default='fecha_vencimiento',
		help="Al usar {{3}}, sera reemplazado por este valor")
	# Aviso cuota vencida
	cuota_vencida_activar = fields.Boolean("Activar mensaje de cuota vencida")
	cuota_vencida_mensaje = fields.Text('Mensaje')
	cuota_vencida_dias_despues = fields.Integer("Dias despues del vencimiento")
	cuota_vencida_activar_segundo_envio = fields.Boolean("Activar segundo envio")
	cuota_vencida_segundo_envio_dias_despues = fields.Integer("Dias despues del vencimiento")
	cuota_vencida_var_1 = fields.Selection([
		('nombre_cliente', 'Nombre de cliente')],
		'{{1}}', default='nombre_cliente',
		help="Al usar {{1}}, sera reemplazado por este valor")
	cuota_vencida_var_2 = fields.Selection([
		('monto_cuota', 'Monto de la cuota')],
		'{{2}}', default='monto_cuota',
		help="Al usar {{2}}, sera reemplazado por este valor")
	cuota_vencida_var_3 = fields.Selection([
		('fecha_vencimiento', 'Fecha de vencimiento')],
		'{{3}}', default='fecha_vencimiento',
		help="Al usar {{3}}, sera reemplazado por este valor")
	# Aviso notificacion deuda
	notificacion_deuda_activar = fields.Boolean("Activar mensaje de notificacion de deuda")
	notificacion_deuda_mensaje = fields.Text('Mensaje')
	notificacion_deuda_dia = fields.Integer("Dia del mes")
	notificacion_deuda_activar_segundo_envio = fields.Boolean("Activar segundo envio")
	notificacion_deuda_dia_segundo_envio = fields.Integer("Dia del mes")
	notificacion_deuda_var_1 = fields.Selection([
		('nombre_cliente', 'Nombre de cliente')],
		'{{1}}', default='nombre_cliente',
		help="Al usar {{1}}, sera reemplazado por este valor")
	notificacion_deuda_var_2 = fields.Selection([
		('monto_deuda', 'Monto de la deuda')],
		'{{2}}', default='monto_deuda',
		help="Al usar {{2}}, sera reemplazado por este valor")
	notificacion_deuda_var_3 = fields.Selection([
		('cantidad_cuotas', 'Cantidad de cuotas')],
		'{{3}}', default='cantidad_cuotas',
		help="Al usar {{3}}, sera reemplazado por este valor")

	# Notificacion Codigo Terminos y condiciones
	tc_codigo = fields.Boolean("Activar mensaje con codigo de terminos y condiciones.")
	tc_mensaje = fields.Text('Mensaje', help='Usar {{1}} como codigo.')

	# Validacion de celular para portal y App
	validacion_celular_codigo = fields.Boolean("Activar mensaje de codigo para validacion de celular.")
	validacion_celular_mensaje = fields.Text('Mensaje', help='Usar {{1}} como codigo.')

	# TC por medio de sms
	metodo_sms_tc_codigo = fields.Boolean("Activar mensaje de terminos y condiciones.")
	metodo_sms_tc_mensaje = fields.Text('Mensaje', help='Usar {{1}} como codigo.')
	metodo_sms_tc_nombre_reporte = fields.Char("Nombre reporte en pdf a adjuntar")
	metodo_sms_tc_respuesta_correcta = fields.Text('Respuesta correcta', help='Usar {{1}} como codigo.')

	@api.one
	def send_sms_test(self):
		params = {
			'usuario': self.usuario,
			'clave': self.password,
			'tos': self.sms_numero_test,
			'texto': self.sms_texto_test,
		}
		r = requests.get('http://servicio.smsmasivos.com.ar/enviar_sms.asp?api=1', params=params)
		if r.status_code != 200:
			raise ValidationError("Error de envio. Motivo: " + r.reason + ". Contacte con Librasoft.")

	@api.one
	def actualizar_saldo(self):
		params = {
			'usuario': self.usuario,
			'clave': self.password,
		}
		r = requests.get('http://servicio.smsmasivos.com.ar/obtener_saldo.asp?', params=params)
		if r.status_code == 200:
			self.sms_saldo = int(r.content)
		else:
			raise ValidationError("Error de conexion. Motivo: " + r.reason + ". Contacte con Librasoft.")

class ExtendsResCompany(models.Model):
	_inherit = 'res.company'

	sms_configuracion_id = fields.Many2one('financiera.sms.config', 'Configuracion sobre mensajes SMS')
