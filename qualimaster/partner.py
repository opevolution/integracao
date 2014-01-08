# -*- coding: utf-8 -*-

from osv import fields, osv


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
                 'mix_contrato': fields.boolean('Mix Contrato?',help=u"Unifica todas os Serviços do pedido em Único Contrato"),
                 'produto_alter_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True),'type','=','service']),  
                }

res_partner()
