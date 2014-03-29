# -*- encoding: utf-8 -*-

import logging
from openerp.osv import fields, osv, orm
from openerp import netsvc
from datetime import datetime

_logger = logging.getLogger(__name__)

class account_invoice(orm.Model):
    _inherit = 'account.invoice'
 
    def _check_internal_number(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         _logger.info('Constraint')
#          
#         invoices = self.browse(cr, uid, ids, context=context)
#         domain = []
#         for invoice in invoices:
#             if not invoice.internal_number:
#                 continue
#             domain.extend(
#                 [('company_id', '=', invoice.company_id.id),
#                 ('internal_number', '=', invoice.internal_number),])
#          
#             invoice_id = self.pool.get('account.invoice').search(cr, uid, domain)
#              
#             if len(invoice_id) > 1:
#                 return False
#              
        return True
 
    _constraints = [
                    (_check_internal_number,
                     u"Error!\nNão é possível registrar \
                        faturas com o mesmo número interno.",
                        ['internal_number']), ]
   
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

    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state': 'draft',
            #'internal_number': False,
            'nfe_access_key': False,
            'nfe_status': False,
            'nfe_date': False,
            'nfe_export_date': False})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            wf_service.trg_delete(uid, 'account.invoice', inv_id, cr)
            wf_service.trg_create(uid, 'account.invoice', inv_id, cr)
        return True
    
    def date_due_change(self, cr, uid, ids, date_due, context=None):
        _logger.info('<Nova Data de pagamento>')
        for inv in self.browse(cr, uid, ids):
            if inv.state in ['proforma', 'proforma2', 'sefaz_export', 'sefaz_exception', 'open' ]:
                move_id = inv.move_id and inv.move_id.id or False
                ref = inv.internal_number or inv.reference or ''
                
                sql = "UPDATE account_move_line SET date_maturity='%s' "\
                      "WHERE date_maturity is not null and reconcile_id is null and move_id=%s" % (date_due,move_id)
                _logger.info('Nova data de pagamento: '+sql)
                
                cr.execute(sql)
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids):
            if inv.state == 'draft':
                osv.osv.unlink(self, cr, uid, [inv.id], context=context)
            else:
                super(account_invoice, self).unlink(cr,uid,[inv.id],context)
        return True

    def _check_invoice_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return True
    
account_invoice()