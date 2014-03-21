# -*- encoding: utf-8 -*-

from openerp.osv import orm, fields

class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    
    _columns = {
               'contract_id': fields.many2one('account.analytic.account', 'Contrato Objeto',readonly=True, states={'draft': [('readonly', False)]}),
               }
    
    def action_internal_number(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids):
            if inv.internal_number == False:
                super(account_invoice, self).action_internal_number(cr, uid, [inv.id], context=context)
        return True

account_invoice()