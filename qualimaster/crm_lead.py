# -*- coding: utf-8 -*-

from openerp.addons.base_status.base_stage import base_stage
from openerp.osv import fields, osv, orm
from base.res.res_partner import format_address


class crm_lead(base_stage, format_address, osv.osv):
    _inherit = 'crm.lead'

    _columns = {
                'obj_product_id': fields.many2one('product.product', 'Objeto', domain=[('sale_ok', '=', True)]), 
                }

crm_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
