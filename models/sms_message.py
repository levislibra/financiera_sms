# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import datetime
from dateutil import relativedelta
import requests


class FinancieraSmsMessage(models.Model):
	_name = 'financiera.sms.message'

	_order = 'id desc'
	name = fields.Char("Nombre")
	partner_id = fields.Many2one('res.partner', 'Cliente')
	prestamo_id = fields.Many2one('financiera.prestamo', 'Prestamo')
	sms_message_masive_id = fields.Many2one('financiera.sms.message.masive', 'Mensaje masivo')
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
			if self.html:
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
		company_ids = company_obj.search(cr, uid, [])
		for _id in company_ids:
			company_id = company_obj.browse(cr, uid, _id)
			if len(company_id.sms_configuracion_id) > 0:
				sms_configuracion_id = company_id.sms_configuracion_id
				# Mensajes preventivos
				if sms_configuracion_id.preventivo_activar:
					fechas_preventiva = []
					if sms_configuracion_id.preventivo_dias_antes > 0:
						fecha = fecha_actual + relativedelta.relativedelta(days=sms_configuracion_id.preventivo_dias_antes)
						fechas_preventiva.append(fecha)
					if sms_configuracion_id.preventivo_segundo_envio_dias_antes > 0:
						fecha = fecha_actual + relativedelta.relativedelta(days=sms_configuracion_id.preventivo_segundo_envio_dias_antes)
						fechas_preventiva.append(fecha)
					if sms_configuracion_id.preventivo_tercer_envio_dias_antes > 0:
						fecha = fecha_actual + relativedelta.relativedelta(days=sms_configuracion_id.preventivo_tercer_envio_dias_antes)
						fechas_preventiva.append(fecha)
					if sms_configuracion_id.preventivo_cuarto_envio_dias_antes > 0:
						fecha = fecha_actual + relativedelta.relativedelta(days=sms_configuracion_id.preventivo_cuarto_envio_dias_antes)
						fechas_preventiva.append(fecha)
					cuota_obj = self.pool.get('financiera.prestamo.cuota')
					cuota_ids = cuota_obj.search(cr, uid, [
						('company_id', '=', company_id.id),
						('prestamo_id.state', '=', 'acreditado'),
						('state', '=', 'activa'),
						('fecha_vencimiento', 'in', fechas_preventiva)])
					for _id in cuota_ids:
						cuota_id = cuota_obj.browse(cr, uid, _id)
						if cuota_id.saldo > 0:
							sms_message_values = {
								'partner_id': cuota_id.partner_id.id,
								'config_id': sms_configuracion_id.id,
								'to': cuota_id.partner_id.mobile or False,
								'tipo': 'Preventivo',
								'company_id': company_id.id,
							}
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
				# Mensaje cuota vencida mora temprana
				if sms_configuracion_id.cuota_vencida_activar:
					fechas_cuota_vencida = []
					if sms_configuracion_id.cuota_vencida_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_dias_despues)
						fechas_cuota_vencida.append(fecha)
					if sms_configuracion_id.cuota_vencida_segundo_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_segundo_envio_dias_despues)
						fechas_cuota_vencida.append(fecha)
					if sms_configuracion_id.cuota_vencida_tercer_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_tercer_envio_dias_despues)
						fechas_cuota_vencida.append(fecha)
					if sms_configuracion_id.cuota_vencida_cuarto_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_cuarto_envio_dias_despues)
						fechas_cuota_vencida.append(fecha)
					if sms_configuracion_id.cuota_vencida_quinto_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_quinto_envio_dias_despues)
						fechas_cuota_vencida.append(fecha)
					cuota_obj = self.pool.get('financiera.prestamo.cuota')
					cuota_ids = cuota_obj.search(cr, uid, [
						('company_id', '=', company_id.id),
						('prestamo_id.state', '=', 'acreditado'),
						('state', '=', 'activa'),
						('fecha_vencimiento', 'in', fechas_cuota_vencida)])
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
				# Mensaje cuota vencida mora media
				if sms_configuracion_id.cuota_vencida_mora_media_activar:
					fechas_cuota_vencida_mora_media = []
					if sms_configuracion_id.cuota_vencida_mora_media_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_mora_media_dias_despues)
						fechas_cuota_vencida_mora_media.append(fecha)
					if sms_configuracion_id.cuota_vencida_mora_media_segundo_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_mora_media_segundo_envio_dias_despues)
						fechas_cuota_vencida_mora_media.append(fecha)
					if sms_configuracion_id.cuota_vencida_mora_media_tercer_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_mora_media_tercer_envio_dias_despues)
						fechas_cuota_vencida_mora_media.append(fecha)
					if sms_configuracion_id.cuota_vencida_mora_media_cuarto_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_mora_media_cuarto_envio_dias_despues)
						fechas_cuota_vencida_mora_media.append(fecha)
					if sms_configuracion_id.cuota_vencida_mora_media_quinto_envio_dias_despues > 0:
						fecha = fecha_actual - relativedelta.relativedelta(days=sms_configuracion_id.cuota_vencida_mora_media_quinto_envio_dias_despues)
						fechas_cuota_vencida_mora_media.append(fecha)
					cuota_obj = self.pool.get('financiera.prestamo.cuota')
					cuota_ids = cuota_obj.search(cr, uid, [
						('company_id', '=', company_id.id),
						('prestamo_id.state', '=', 'acreditado'),
						('state', '=', 'activa'),
						('fecha_vencimiento', 'in', fechas_cuota_vencida_mora_media)])
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
								sms_configuracion_id.cuota_vencida_mora_media_mensaje,
								'cuota_vencida',
								cuota_id,
								cuota_id.partner_id,
								sms_configuracion_id.cuota_vencida_mora_media_var_1,
								sms_configuracion_id.cuota_vencida_mora_media_var_2,
								sms_configuracion_id.cuota_vencida_mora_media_var_3)
							message_id.send()
				# Mensaje notificacion deuda
				if sms_configuracion_id.notificacion_deuda_activar:
					if fecha_actual.day == sms_configuracion_id.notificacion_deuda_dia\
					or fecha_actual.day == sms_configuracion_id.notificacion_deuda_dia_segundo_envio:
						partner_obj = self.pool.get('res.partner')
						partner_ids = partner_obj.search(cr, uid, [
							('company_id', '=', company_id.id),
							('prestamo_id.state', '=', 'acreditado'),
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
