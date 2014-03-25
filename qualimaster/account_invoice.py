# -*- encoding: utf-8 -*-

from openerp.osv import orm, fields

class account_invoice(orm.Model):
    _inherit = 'account.invoice'
    
    _columns = {
                'date_due': fields.date('Due Date', select=True,
                    help="If you use payment terms, the due date will be computed automatically at the generation "\
                        "of accounting entries. The payment term may compute several due dates, for example 50% now and 50% in one month, but if you want to force a due date, make sure that the payment term is not set on the invoice. If you keep the payment term and the due date empty, it means direct payment."),
               'contract_id': fields.many2one('account.analytic.account', 'Contrato Objeto',readonly=True, states={'draft': [('readonly', False)]}),
               }
    
    def action_internal_number(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids):
            if inv.internal_number == False:
                super(account_invoice, self).action_internal_number(cr, uid, [inv.id], context=context)
        return True

account_invoice()