# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

from openerp.osv import osv, fields

class res_company(osv.osv):

    _inherit = 'res.company'
    _columns = {
                'porcent_comiss': fields.float('% Comissão', digits=(6,4)),
                'gestor_id': fields.many2one('hr.employee', 'Gestor da Empresa', domain="[('is_tech_mananger','=',True)]",),
                }

res_company()