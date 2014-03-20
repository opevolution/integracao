# -*- encoding: utf-8 -*-

from openerp.osv import orm, fields

class account_invoice(orm.Model):
    _inherit = 'account.payment.term'
    
    _columns = {
               'for_contract': fields.boolean('Pagamento de Contratos'),
               }

account_invoice()