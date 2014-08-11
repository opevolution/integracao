# -*- encoding: utf-8 -*-

import logging
import time
from datetime import datetime
from osv import osv, fields
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)

class wiz_confirm_bank(osv.osv_memory):
    """  Confirma os Extratos Marcados e Envia Email de Aviso para Gerente Financeiro """
    
    _name = 'wiz.confirm_bank'
    
    _columns = {
                'date': fields.date('Data do Fechamento',),
                'autoenv': fields.boolean('Envio Automático'),
                'line_ids': fields.one2many('wiz.confirm_bank.line','confirm_bank_id','Extratos',),
                'texto': fields.html('HTML Texto'),
                'state': fields.selection([('draft','draft'),('send','send'),('done','done')],'Estado'),
                }
    
    _defaults = {
                 'state': 'draft',
                 'date': lambda *a: time.strftime('%Y-%m-%d'),
                 'autoenv': lambda *a: True,
                }
    
    def action_confirm(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        [wizard] = self.browse(cr, uid, ids)
        obj_seq = self.pool.get('ir.sequence')
        statement_pool = self.pool.get('account.bank.statement')
        extrato_ids = context.get('active_ids', [])
        
        for st in statement_pool.browse(cr, uid, extrato_ids, context=context):
            if st.state != 'confirm':
                
                if st.balance_end != st.balance_end_real:
                    raise osv.except_osv('Extrato da Conta %s - %s' % (st.journal_id.name, st.name,),
                            'O saldo final do extrato está incorreto.\n\n'\
                            ' O saldo experado (%.2f) é diferente do saldo calculado (%.2f).' % (st.balance_end_real,st.balance_end))
                
                j_type = st.journal_id.type
                company_currency_id = st.journal_id.company_id.currency_id.id
                if not statement_pool.check_status_condition(cr, uid, st.state, journal_type=j_type):
                    continue

                statement_pool.balance_check(cr, uid, st.id, journal_type=j_type, context=context)
                if (not st.journal_id.default_credit_account_id) \
                        or (not st.journal_id.default_debit_account_id):
                    raise osv.except_osv('Erro na Configuração!',
                            'Favor verifique se uma conta está configurada no diário.')

                if not st.name == '/':
                    st_number = st.name
                else:
                    c = {'fiscalyear_id': st.period_id.fiscalyear_id.id}
                    if st.journal_id.sequence_id:
                        st_number = obj_seq.next_by_id(cr, uid, st.journal_id.sequence_id.id, context=c)
                    else:
                        st_number = obj_seq.next_by_code(cr, uid, 'account.bank.statement', context=c)

                for line in st.move_line_ids:
                    if line.state <> 'valid':
                        raise osv.except_osv('Error!',
                                'As linhas dos lançamentos não estão válidas.')
                for st_line in st.line_ids:
                    if st_line.analytic_account_id:
                        if not st.journal_id.analytic_journal_id:
                            raise osv.except_osv('Diário não identificado!',
                                                 "Não foi indicado um diário analítico no diário '%s'!" % (st.journal_id.name,))
                    if not st_line.amount:
                        continue
                    st_line_number = statement_pool.get_next_st_line_number(cr, uid, st_number, st_line, context)
                    statement_pool.create_move_from_st_line(cr, uid, st_line.id, company_currency_id, st_line_number, context)

                statement_pool.write(cr, uid, [st.id], {
                        'name': st_number,
                        'balance_end_real': st.balance_end,
                        'state': 'confirm',
                        }, context=context)

                statement_pool.message_post(cr, uid, [st.id], body=u'Extrato Bancário %s confirmado via wizard CONFIRMAR EXTRATOS, entradas de diário foram criadas.' % (st_number,), context=context)
        if wizard.autoenv:
            envmail = self.pool.get('wiz.envio_saldo')
            newmail = envmail.create(cr,uid,{},context)
            envmail.action_enviar(cr, uid, [newmail], context)        
        return True
    
        
wiz_confirm_bank()

class wiz_confirm_bank_line(osv.osv_memory):
    """  Valores com os Extratos Marcados e Envia Email de Aviso para Gerente Financeiro """
    
    _name = 'wiz.confirm_bank.line'
    
    _columns = {
                'confirm_bank_id': fields.many2one('wiz.confirm_bank', u'Confirmações',),
                'name': fields.char('Conta',size=120),
                'saldo_conta': fields.float('Saldo Anetrior',digits_compute=dp.get_precision('Product Price'),),
                'state': fields.selection([('draft','draft'),('send','send'),('done','done')])
                }
