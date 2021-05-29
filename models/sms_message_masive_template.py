# -*- coding: utf-8 -*-

from openerp import models, fields

class FinancieraSmsMessageMasiveTemplate(models.Model):
	_name = 'financiera.sms.message.masive.template'

	_order = 'id desc'
	_rec_name = 'tipo'
	tipo = fields.Char('Tipo de mensaje')
	body = fields.Text('Mensaje', size=160)
	company_id = fields.Many2one('res.company', 'Empresa', required=False, default=lambda self: self.env['res.company']._company_default_get('financiera.sms.message.masive.template'))