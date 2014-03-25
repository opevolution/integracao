# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _


class send_faturamento(osv.osv_memory):
    """ Envio do Faturamento """

    _name = 'send.faturamento'

    def action_send(self, cr, uid, ids, context=None):
        [wizard] = self.browse(cr, uid, ids)
        invoice_pool = self.pool.get('account.invoice')
        email_obj = self.pool.get('email.template')
        
        invoice_ids = context.get('active_ids', [])
        template_ids = email_obj.search(cr, uid, [('name', '=', 'envio_faturamento')])
        
        if not template_ids:
            raise osv.except_osv(_('Error!'),
                    _(u'Crie o template de e-mail chamado "envio_faturamento".'))
          
        self.write(cr, uid, [wizard.id], {'state': 'doing'})
        
        #for invoice in invoice_pool.browse(cr, uid, invoice_ids):
            
            
            

    _columns = {
                'cc': fields.char('CC', size=128,),
                'test': fields.boolean('Teste',),
                'progress_rate': fields.integer('Progresso',),
                'state': fields.selection([('init', 'init'), ('doing', 'doing'), ('done', 'done')], 'state', readonly=True),                
                }

    _defaults = {
                 'state': 'init',
                 }

send_faturamento()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
