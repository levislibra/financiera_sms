# -*- coding: utf-8 -*-
{
    'name': "Financiera SMS Notificaciones",

    'summary': """
        Notificaciones mediante sms en eventos particulares.""",

    'description': """
        Notificaciones mediante sms en eventos particulares.
    """,

    'author': "Librasoft",
    'website': "lirba-soft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'financial',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'financiera_prestamos'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sms_configuracion.xml',
        'views/sms_message.xml',
        'views/extends_res_company.xml',
        'data/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}