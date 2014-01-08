# -*- encoding: utf-8 -*-

from openerp.osv import orm, fields

class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    
    _columns = {
               'contract_id': fields.many2one('account.analytic.account', 'Contrato',readonly=True, states={'draft': [('readonly', False)]}),
               }

account_invoice()