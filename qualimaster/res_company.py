# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################

from openerp.osv import osv, fields

class res_company(osv.osv):

    _inherit = 'res.company'
    _columns = {
                'porcent_comiss': fields.float('% Comissão', digits=(6,4)),
                }

res_company()