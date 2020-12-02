# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil import relativedelta
from random import randint
import requests
from lxml.html.clean import Cleaner
import re

class FinancieraSmsMessage(models.Model):
	_name = 'financiera.sms.message'

	_order = 'id desc'
	name = fields.Char("Nombre")
	partner_id = fields.Many2one('res.partner', 'Cliente')
	prestamo_id = fields.Many2one('financiera.prestamo', 'Prestamo')
	config_id = fields.Many2one('financiera.sms.config', 'Configuracion sms')
	tipo = fields.Char('Tipo de mensaje')
	to = fields.Char('Para')
	body = fields.Text('Mensaje')
	error_message = fields.Char("Mensaje de error")
	status = fields.Char("Estado")
	id_interno = fields.Char('Id interno')
	html = fields.Text('Html')
	company_id = fields.Many2one('res.company', 'Empresa')
	respuesta_ids = fields.One2many('financiera.sms.message.response', 'sms_message_id', 'Respuestas')

	@api.model
	def create(self, values):
		rec = super(FinancieraSmsMessage, self).create(values)
		rec.update({
			'name': 'SMS ' + str(rec.id).zfill(6),
		})
		return rec

	@api.one
	def send(self):
		if self.to != False and len(self.to) == 10 and self.body != False:
			params = {
				'usuario': self.config_id.usuario,
				'clave': self.config_id.password,
				'tos': self.to,
				'texto': self.body,
			}
			if self.tipo == 'TC aceptacion':
				params['idinterno'] = self.id_interno
				params['texto'] = self.body + " http://1rck.in/-000000"
				params['html'] = self.html
			r = requests.get('http://servicio.smsmasivos.com.ar/enviar_sms.asp?api=1', params=params)
			self.error_message = r.reason
			if r.status_code == 200:
				self.status = "Enviado"
		else:
			if self.body == False:
				self.error_message = "Mensaje vacio"
			else:
				self.error_message = "Numero destino"
			self.status = "No enviado"

	@api.one
	def set_message(self, mensaje, tipo_mensaje, cuota_id, partner_id, var1, var2, var3):
		if var1 != False:
			mensaje = mensaje.replace("{{1}}", var1)
		if var2 != False:
			mensaje = mensaje.replace("{{2}}", var2)
		if var3 != False:
			mensaje = mensaje.replace("{{3}}", var3)
		if tipo_mensaje == 'preventivo':
			mensaje = mensaje.replace("nombre_cliente", partner_id.name)
			monto = "${:,.2f}".format(cuota_id.saldo).replace(',', '#').replace('.', ',').replace('#', '.')
			mensaje = mensaje.replace("monto_cuota", monto)
			date = datetime.strptime(cuota_id.fecha_vencimiento, '%Y-%m-%d')
			date = date.strftime('%d-%m-%Y')
			mensaje = mensaje.replace("fecha_vencimiento", date)
		elif tipo_mensaje == 'cuota_vencida':
			mensaje = mensaje.replace("nombre_cliente", partner_id.name)
			monto = "${:,.2f}".format(cuota_id.saldo).replace(',', '#').replace('.', ',').replace('#', '.')
			mensaje = mensaje.replace("monto_cuota", monto)
			date = datetime.strptime(cuota_id.fecha_vencimiento, '%Y-%m-%d')
			date = date.strftime('%d-%m-%Y')
			mensaje = mensaje.replace("fecha_vencimiento", date)
		elif tipo_mensaje == 'notificacion_deuda':
			mensaje = mensaje.replace("nombre_cliente", partner_id.name)
			monto = "${:,.2f}".format(partner_id.saldo_cuotas_vencidas).replace(',', '#').replace('.', ',').replace('#', '.')
			mensaje = mensaje.replace("monto_deuda", monto)
			mensaje = mensaje.replace("cantidad_cuotas", str(partner_id.cantidad_cuotas_vencidas))
		self.body = mensaje

	@api.one
	def set_message_code(self, mensaje, code):
		mensaje = mensaje.replace("{{1}}", code)
		self.body = mensaje

	@api.model
	def _cron_enviar_mensajes_sms(self):
		cr = self.env.cr
		uid = self.env.uid
		fecha_actual = datetime.now()
		company_obj = self.pool.get('res.company')
		comapny_ids = company_obj.search(cr, uid, [])
		for _id in comapny_ids:
			company_id = company_obj.browse(cr, uid, _id)
			print("company_id: ", company_id.name)
			print("company_id.sms_configuracion_id: ", company_id.sms_configuracion_id)
			if len(company_id.sms_configuracion_id) > 0:
				sms_configuracion_id = company_id.sms_configuracion_id
				print("sms_configuracion_id.preventivo_activar: ", sms_configuracion_id.preventivo_activar)
				# Mensajes preventivos
				if sms_configuracion_id.preventivo_activar:
					primer_fecha = fecha_actual + relativedelta.relativedelta(days=sms_configuracion_id.preventivo_dias_antes)
					segunda_fecha = None
					if sms_configuracion_id.preventivo_activar_segundo_envio:
						segunda_fecha = fecha_actual + relativedelta.relativedelta(days=sms_configuracion_id.preventivo_segundo_envio_dias_antes)
					print("primer_fecha: ", primer_fecha)
					print("segunda_fecha: ", segunda_fecha)
					cuota_obj = self.pool.get('financiera.prestamo.cuota')
					cuota_ids = cuota_obj.search(cr, uid, [
						('company_id', '=', company_id.id),
						('state', '=', 'activa'),
						'|', ('fecha_vencimiento', '=', primer_fecha),
						('fecha_vencimiento', '=', segunda_fecha)
						])
					print("cuota_ids: ", cuota_ids)
					for _id in cuota_ids:
						cuota_id = cuota_obj.browse(cr, uid, _id)
						print("cuota_id.saldo: ", cuota_id.saldo)
						if cuota_id.saldo > 0:
							# mensaje = sms_configuracion_id.replace_values(mensaje, 'preventivo', cuota_id, cuota_id.partner_id,\
							# 	sms_configuracion_id.preventivo_var_1, sms_configuracion_id.preventivo_var_2, sms_configuracion_id.preventivo_var_3)
							sms_message_values = {
								'partner_id': cuota_id.partner_id.id,
								'config_id': sms_configuracion_id.id,
								'to': cuota_id.partner_id.mobile or False,
								'tipo': 'Preventivo',
								'company_id': company_id.id,
							}
							print("sms_message_values: ", sms_message_values)
							message_id = self.env['financiera.sms.message'].create(sms_message_values)
							message_id.set_message(
								sms_configuracion_id.preventivo_mensaje,
								'preventivo', 
								cuota_id, 
								cuota_id.partner_id,
								sms_configuracion_id.preventivo_var_1,
								sms_configuracion_id.preventivo_var_2,
								sms_configuracion_id.preventivo_var_3)
							message_id.send()
				# Mensaje cuota vencida
				if sms_configuracion_id.cuota_vencida_activar:
					primer_fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_dias_despues)
					segunda_fecha = None
					if sms_configuracion_id.cuota_vencida_activar_segundo_envio:
						segunda_fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_segundo_envio_dias_despues)
					cuota_obj = self.pool.get('financiera.prestamo.cuota')
					cuota_ids = cuota_obj.search(cr, uid, [
						('company_id', '=', company_id.id),
						('state', '=', 'activa'),
						'|', ('fecha_vencimiento', '=', primer_fecha),
						('fecha_vencimiento', '=', segunda_fecha)
						])
					for _id in cuota_ids:
						cuota_id = cuota_obj.browse(cr, uid, _id)
						if cuota_id.saldo > 0:
							sms_message_values = {
								'partner_id': cuota_id.partner_id.id,
								'config_id': sms_configuracion_id.id,
								'to': cuota_id.partner_id.mobile or False,
								'tipo': 'Cuota vencida',
								'company_id': company_id.id,
							}
							message_id = self.env['financiera.sms.message'].create(sms_message_values)
							message_id.set_message(
								sms_configuracion_id.cuota_vencida_mensaje,
								'cuota_vencida',
								cuota_id,
								cuota_id.partner_id,
								sms_configuracion_id.cuota_vencida_var_1,
								sms_configuracion_id.cuota_vencida_var_2,
								sms_configuracion_id.cuota_vencida_var_3)
							message_id.send()
				# Mensaje notificacion deuda
				if sms_configuracion_id.notificacion_deuda_activar:
					if fecha_actual.day == sms_configuracion_id.notificacion_deuda_dia\
					or fecha_actual.day == sms_configuracion_id.notificacion_deuda_dia_segundo_envio:
						partner_obj = self.pool.get('res.partner')
						partner_ids = partner_obj.search(cr, uid, [
							('company_id', '=', company_id.id),
							('cuota_ids.fecha_vencimiento', '<', fecha_actual),
							('cuota_ids.state', '=', 'activa')])
						for _id in partner_ids:
							partner_id = partner_obj.browse(cr, uid, _id)
							if partner_id.saldo_cuotas_vencidas > 0:
								sms_message_values = {
									'partner_id': partner_id.id,
									'config_id': sms_configuracion_id.id,
									'to': partner_id.mobile,
									'tipo': 'Deuda',
									'company_id': company_id.id,
								}
								message_id = self.env['financiera.sms.message'].create(sms_message_values)
								message_id.set_message(
									sms_configuracion_id.notificacion_deuda_mensaje,
									'notificacion_deuda',
									None,
									partner_id,
									sms_configuracion_id.notificacion_deuda_var_1,
									sms_configuracion_id.notificacion_deuda_var_2,
									sms_configuracion_id.notificacion_deuda_var_3)
								message_id.send()
				sms_configuracion_id.actualizar_saldo()

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
		comapny_ids = company_obj.search(cr, uid, [])
		for _id in comapny_ids:
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
					sms_configuracion_id.actualizar_saldo()
					prestamo_id.email_tc_code_sent = True

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
			sms_configuracion_id.actualizar_saldo()
		return True

class ExtendsFinancieraPrestamo(models.Model):
	_name = 'financiera.prestamo'
	_inherit = 'financiera.prestamo'

	sms_aceptacion_tc_id = fields.Many2one('financiera.sms.message', 'SMS aceptacion TC')

	@api.one
	def metodo_aceptacion_sms_enviar_tc(self):
		sms_configuracion_id = self.company_id.sms_configuracion_id
		if sms_configuracion_id.metodo_sms_tc_codigo:
			reporte_html = self.report_render_html()
			sms_message_values = {
				'partner_id': self.partner_id.id,
				'prestamo_id': self.id,
				'config_id': sms_configuracion_id.id,
				'to': self.partner_id.mobile,
				'id_interno': str(self.id),
				'tipo': 'TC aceptacion',
				'html': reporte_html,
				'company_id': self.company_id.id,
			}
			message_id = self.env['financiera.sms.message'].create(sms_message_values)
			codigo = self.email_tc_code
			message_id.set_message_code(sms_configuracion_id.metodo_sms_tc_mensaje, codigo)
			message_id.send()
			sms_configuracion_id.actualizar_saldo()
			self.sms_aceptacion_tc_id = message_id.id
	
	@api.multi
	def report_render_html(self, data=None):
		report_name = self.company_id.sms_configuracion_id.metodo_sms_tc_nombre_reporte
		report_obj = self.env['report']
		report = report_obj._get_report_from_name(report_name)
		docargs = {
				'doc_ids': self._ids,
				'doc_model': report.model,
				'docs': self,
		}
		html = report_obj.render(report_name, docargs)
		html = html.replace('\n', '')
		html3 = re.sub("(<img.*?>)", "", html, 0, re.IGNORECASE | re.DOTALL | re.MULTILINE)
		html3 = self.sanitize(html3)
		return html3

	def sanitize(self, dirty_html):
		cleaner = Cleaner(
			page_structure=True,
			meta=True,
			embedded=True,
			links=True,
			style=True,
			processing_instructions=True,
			# inline_style=True,
			scripts=True,
			javascript=True,
			comments=True,
			frames=True,
			forms=True,
			annoying_tags=True,
			remove_unknown_tags=True,
			safe_attrs_only=True,
			safe_attrs=frozenset(['src','color', 'href', 'title', 'class', 'name', 'id']),
			remove_tags=('span', 'font', 'div')
		)
		return cleaner.clean_html(dirty_html)