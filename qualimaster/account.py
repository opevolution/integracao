# -*- encoding: utf-8 -*-

from openerp.osv import orm, fields

class account_invoice(orm.Model):
    _inherit = 'account.payment.term'
    
    _columns = {
                'dia_emiss': fields.integer('Dia Emissão'),
                'for_contract': fields.boolean('Pagamento de Contratos'),
                'is_pos': fields.boolean('Pós Pago'),
               }

account_invoice()