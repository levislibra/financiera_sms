# -*- coding: utf-8 -*-

from openerp import models, fields, api
from lxml.html.clean import Cleaner
import re

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