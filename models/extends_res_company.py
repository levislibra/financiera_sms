# -*- coding: utf-8 -*-

from openerp import models, fields, api

class ExtendsResCompany(models.Model):
	_inherit = 'res.company'

	sms_configuracion_id = fields.Many2one('financiera.sms.config', 'Configuracion sobre mensajes SMS')
