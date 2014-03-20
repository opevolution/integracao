# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _


class crm_make_sale(osv.osv_memory):
    _inherit = "crm.make.sale"
    _columns = {
        'order_name': fields.char('Número FR', help='Número da FR.'),
    }
    _defaults = {
        'shop_id': _get_shop_id,
        'close': False,
        'partner_id': _selectPartner,
    }

crm_make_sale()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
