# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError
import requests
import logging

_logger = logging.getLogger(__name__)
class FinancieraSmsConfig(models.Model):
	_name = 'financiera.sms.config'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	name = fields.Char('Nombre')
	usuario = fields.Char('Usuario')
	password = fields.Char('Password')
	sms_saldo = fields.Integer('SMS restantes')
	sms_numero_test = fields.Char('Movil destino de prueba')
	sms_texto_test = fields.Char('Mensaje de prueba', size=120)
	sms_message_masive_count = fields.Integer("SMS masivo id", default=1)
	sms_alert_email = fields.Boolean("Activar alerta de saldo por email")
	sms_alerta_saldo = fields.Integer("Saldo menor a", default=50)
	sms_responsable_user_id = fields.Many2one('res.users', 'Usuario responsable', help='Se enviara email cuando el saldo de sms sea bajo.')
	sms_ir_mail_server_id = fields.Many2one('ir.mail_server', 'Servidor saliente')
	company_id = fields.Many2one('res.company', 'Empresa')
	# Mensajes
	# Aviso preventivo
	preventivo_activar = fields.Boolean("Activar mensaje preventivo")
	preventivo_mensaje = fields.Text('Mensaje')
	preventivo_dias_antes = fields.Integer("Dias antes del vencimiento", help="Cero o negativo no se envia.")
	preventivo_activar_segundo_envio = fields.Boolean("Activar segundo envio")#Depreciado
	preventivo_segundo_envio_dias_antes = fields.Integer("Dias antes del vencimiento", help="Cero o negativo no se envia.")
	preventivo_tercer_envio_dias_antes = fields.Integer("Dias antes del vencimiento", help="Cero o negativo no se envia.")
	preventivo_cuarto_envio_dias_antes = fields.Integer("Dias antes del vencimiento", help="Cero o negativo no se envia.")
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
	cuota_vencida_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_activar_segundo_envio = fields.Boolean("Activar segundo envio")# Depreciado
	cuota_vencida_segundo_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_tercer_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_cuarto_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_quinto_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
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
	# Aviso cuota vencida mora media
	cuota_vencida_mora_media_activar = fields.Boolean("Activar mensaje de cuota vencida")
	cuota_vencida_mora_media_mensaje = fields.Text('Mensaje')
	cuota_vencida_mora_media_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_mora_media_activar_segundo_envio = fields.Boolean("Activar segundo envio")# Depreciado
	cuota_vencida_mora_media_segundo_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_mora_media_tercer_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_mora_media_cuarto_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_mora_media_quinto_envio_dias_despues = fields.Integer("Dias despues del vencimiento", help="Cero o negativo no se envia.")
	cuota_vencida_mora_media_var_1 = fields.Selection([
		('nombre_cliente', 'Nombre de cliente')],
		'{{1}}', default='nombre_cliente',
		help="Al usar {{1}}, sera reemplazado por este valor")
	cuota_vencida_mora_media_var_2 = fields.Selection([
		('monto_cuota', 'Monto de la cuota')],
		'{{2}}', default='monto_cuota',
		help="Al usar {{2}}, sera reemplazado por este valor")
	cuota_vencida_mora_media_var_3 = fields.Selection([
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
			'idinterno': 8,
			'tos': self.sms_numero_test,
			'texto': self.sms_texto_test,
			# 'test': 1,
			'respuestanumerica': 1,
		}
		r = requests.get('http://servicio.smsmasivos.com.ar/enviar_sms.asp?api=1', params=params)
		if r.status_code != 200:
			raise ValidationError("Error de envio. Motivo: " + r.reason + ". Contacte con Librasoft.")
		else:
			raise ValidationError(r.text)

	@api.model
	def _cron_actualizar_saldo(self):
		cr = self.env.cr
		uid = self.env.uid
		company_obj = self.pool.get('res.company')
		comapny_ids = company_obj.search(cr, uid, [])
		_logger.info('SMS: controlar saldo SMS.')
		for _id in comapny_ids:
			company_id = company_obj.browse(cr, uid, _id)
			if len(company_id.sms_configuracion_id) > 0:
				sms_configuracion_id = company_id.sms_configuracion_id
				sms_configuracion_id.actualizar_saldo(False)

	def representsInt(self, s):
		try:
			int(s)
			return True
		except ValueError:
			return False

	@api.one
	def actualizar_saldo(self, show_error=True):
		params = {
			'usuario': self.usuario,
			'clave': self.password,
		}
		r = requests.get('http://servicio.smsmasivos.com.ar/obtener_saldo.asp?', params=params)
		if r.status_code == 200:
			if self.representsInt(r.content):
				self.sms_saldo = int(r.content)
				if self.sms_alert_email and self.sms_saldo < self.sms_alerta_saldo:
					self.send_mail_sms_balance_low()
			else:
				self.sms_saldo = -1
		elif show_error:
			raise ValidationError("Error de conexion. Motivo: " + r.reason + ". Contacte con Librasoft.")


	@api.one
	def send_mail_sms_balance_low(self):
		company_id = self.company_id
		subject = "Saldo de SMS en %s"%company_id.name
		message = """<h2>Hola!</h2>
		<p>Su saldo de SMS es de %s.<p/>
		<p>Recuerde contratar un nuevo plan lo mas pronto posible.</p>
		<br/><br/><br/>"""%str(self.sms_saldo)
		if self.sms_ir_mail_server_id and self.sms_responsable_user_id:
			partner_ids= [(4, self.sms_responsable_user_id.partner_id.id)]
			mail_server_id = self.sms_ir_mail_server_id
			# In partner_ids, "4" adds the ID to the list 
			# of followers and next number is the partner ID
			if len(partner_ids) > 0:
				post_vars = {
					'mail_server_id': mail_server_id.id,
					'email_from': '"'+company_id.name+'"' + '<'+company_id.email+'>',
					'reply_to': company_id.email,
					'subject': subject, 
					'body': message, 
					'partner_ids': partner_ids,
					# 'auto_delete': False,
				}
				self.message_post(
					message_type= "email",
					subtype="mt_comment",
					**post_vars)