# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil import relativedelta
from random import randint
import requests
from lxml.html.clean import Cleaner
import re

class FinancieraSmsMessageMasive(models.Model):
	_name = 'financiera.sms.message.masive'

	_order = 'id desc'
	name = fields.Char("Nombre")
	partner_ids = fields.Many2many('res.partner', 'financiera_partner_messagemasive_rel', 'partner_id', 'masivemessage_id', string='Destinatarios')
	tipo = fields.Char('Tipo de mensaje')
	body_count_available = fields.Integer('Caracteres restantes', compute='_compute_body_count_available')
	body = fields.Text('Mensaje')
	is_html = fields.Boolean('Adjuntar html')
	html = fields.Text('Html')
	company_id = fields.Many2one('res.company', 'Empresa')
	message_ids = fields.One2many('financiera.sms.message', 'sms_message_masive_id', 'Mensajes')
	state = fields.Selection([('draft', 'Borrador'), ('send', 'Enviado')], string='Estado', readonly=True, default='draft')

	@api.model
	def create(self, values):
		rec = super(FinancieraSmsMessageMasive, self).create(values)
		sms_masivo_count = rec.company_id.sms_configuracion_id.sms_message_masive_count
		rec.update({
			'name': 'SMS MASIVO/' + str(sms_masivo_count).zfill(6),
		})
		rec.company_id.sms_configuracion_id.sms_message_masive_count = sms_masivo_count + 1
		return rec

	@api.model
	def default_get(self, fields):
		rec = super(FinancieraSmsMessageMasive, self).default_get(fields)
		# configuracion_id = self.env.user.company_id.configuracion_id
		context = dict(self._context or {})
		current_uid = context.get('uid')
		current_user = self.env['res.users'].browse(current_uid)
		company_id = current_user.company_id
		rec.update({
			'company_id': company_id.id,
		})
		return rec

	@api.onchange('body')
	def _compute_body_count_available(self):
		if self.body:
			self.body_count_available = 160 - len(self.body)
		else:
			self.body_count_available = 160

	@api.one
	def partners_cuota_preventiva(self):
		cr = self.env.cr
		uid = self.env.uid
		partner_obj = self.pool.get('res.partner')
		partner_ids = partner_obj.search(cr, uid, [
			('company_id', '=', self.company_id.id),
			('cuota_ids.state_mora', '=', 'preventiva'),
			('cuota_ids.state', '=', 'activa')])
		print("partners: ", partner_ids)
		self.partner_ids = [(6, 0, partner_ids)]

	@api.one
	def partners_cuota_vencida(self):
		cr = self.env.cr
		uid = self.env.uid
		fecha_actual = datetime.now()
		partner_obj = self.pool.get('res.partner')
		partner_ids = partner_obj.search(cr, uid, [
			('company_id', '=', self.company_id.id),
			('cuota_ids.fecha_vencimiento', '<', fecha_actual),
			('cuota_ids.state', '=', 'activa')])
		print("partners: ", partner_ids)
		self.partner_ids = [(6, 0, partner_ids)]

	@api.one
	def send_messages(self):
		config_id = self.company_id.sms_configuracion_id
		for partner_id in self.partner_ids:
			sms_message_values = {
				'partner_id': partner_id.id,
				'config_id': config_id.id,
				'to': partner_id.mobile,
				'tipo': self.tipo or 'Personalizado',
				'company_id': self.company_id.id,
			}
			message_id = self.env['financiera.sms.message'].create(sms_message_values)
			message_id.body = self.body
			if self.is_html:
				message_id.html = self.html
			message_id.send()
			self.message_ids = [message_id.id]
		self.state = 'send'
