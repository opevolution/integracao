# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


from openerp.osv import osv, fields

class product_product(osv.osv):

    _inherit = 'product.product'
    _columns = {
                'horas_trab': fields.integer('Horas Estimadas'),
                'prazo_projeto': fields.integer('Dias para Finalizar'),
                'pagamento': fields.many2one('account.payment.term', 'Forma de Pagamento'),
                }

product_product()