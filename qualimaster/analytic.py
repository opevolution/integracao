# -*- encoding: utf-8 -*-
import logging

from datetime import datetime
from openerp.osv import osv, fields

import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    
    def _get_valor_fixo(self, cr, uid, ids, field_name, arg, context=None):
        """Valor Fixo do Contrato"""
        if not ids:
            return {}
        cr.execute("""SELECT id, COALESCE((vl_hora*hr_qtde)-vl_desconto, 0.0) AS total
                      FROM account_analytic_account
                      WHERE id in (%s)""" % (",".join([str(int(x)) for x in ids])))
        res = {}
        for record in cr.fetchall():
            aaa_id = record[0]
            valor = record[1] or 0.0
            res[aaa_id] = valor
        return res
    
    def _prepara_fatura(self, cr, uid, contrato, pedido, context=None ):
        if context is None:
            context = {}
        invoice_vals = False
        idPartner = contrato['partner_id'][0]
        
        Partner = self.pool.get('res.partner').browse(cr, uid, idPartner, context)
        
        nrParcela = context.get('nrparcela', False)
        idDiario  = context.get('iddiario', False)
        dtInvoice = context.get('date_invoice', False)
        vlName = contrato['name'] +' / '+str(nrParcela)
        _logger.info('Prepara Fatura: NrParcela: '+str(nrParcela)+' / Id Diário: '+str(idDiario)+' / Data: '+str(dtInvoice))
        
        if nrParcela:
            invoice_vals = {
                            'name': vlName,
                            'origin': contrato['name'],
                            'type': 'out_invoice',
                            'fiscal_type': 'service',
                            'reference': vlName,
                            'account_id': Partner.property_account_receivable.id,
                            'partner_id': idPartner,
                            'journal_id': idDiario,
                            #'invoice_line': [(6, 0, linhas)],
                            'currency_id': pedido.pricelist_id.currency_id.id,
                            'payment_term': contrato['inv_payment_term_id'][0],
                            'fiscal_position': Partner.property_account_position.id,
                            'date_invoice': dtInvoice,
                            'company_id': contrato['company_id'][0],
                            'user_id': uid or False,
                            'contract_id': contrato['id'],
                            'state': 'draft',
                            }
            
        return invoice_vals
    
    def _prepara_linha_fatura(self, cr, uid, idFatura, contrato, context=None):
        if context is None:
            context = {}
        vlSeq = context.get('sequencia', False)
        vlPrecoU = context.get('vlunit', False)
        vlQtde = context.get('vlqtde', False)
        pcDesc = context.get('pcDesc', False)
        linha_fat = {
                     'name': 'Teste',
                     'origin': contrato['name'],
                     'sequence': vlSeq or 10,
                     'invoice_id': int(idFatura) or None,
                     'product_id': contrato['obj_product_id'][0],
                     'price_unit': vlPrecoU or 0.00,
                     'quantity': vlQtde or 1,
                     'discount': pcDesc or 0.00,
                     }
        return linha_fat
    
    def _create_fatura(self, cr , uid, valores, context):
        """Gera fatura do contrato com os campos contidos em valores"""
        ObjFatura = self.pool.get('account.invoice')
        IdFatura = ObjFatura.create(cr,uid,valores,context)
        return IdFatura

    def _create_line_fatura(self, cr , uid, valores, context):
        """Gera linha da fatura com os campos contidos em valores"""
        ObjLineFatura = self.pool.get('account.invoice.line')
        IdLineFatura = ObjLineFatura.create(cr,uid,valores,context)
        return IdLineFatura
       
    def contract_confirm(self, cr, uid, ids, context=None):
        """Confirma o Processamento do Contrato"""
        if context is None:
            context = {}

        hj = datetime.now()
        
        idContrato = ids[0]
        _logger.info('Id Contrato: '+str(idContrato))
        Contrato = self.read(cr, uid, idContrato, context=context)
        
        _logger.info('Data Prevista para o fim do projeto '+str(Contrato['date']))
        
        if not Contrato['date_start']:
            raise osv.except_osv('Erro!',
                'Defina a data início de execução do projeto.')

        if not Contrato['date']:
            raise osv.except_osv('Erro!',
                'Defina a data máxima de termino de execução do projeto.')

        if Contrato['date'] <= Contrato['date_start']:
            raise osv.except_osv('Erro!',
                'A data de conclusão não pode ser menor que a data de inicio do projeto.')

        if Contrato['date'] <= Contrato['date_start']:
            raise osv.except_osv('Erro!',
                'A data de conclusão não pode ser menor que a data de inici.')

        if not Contrato['inv_payment_term_id']:
            raise osv.except_osv('Erro!',
                'Defina a forma de pagamento para as faturas a serem geradas.')
        
        if not Contrato['payment_term_id']:
            raise osv.except_osv('Erro!',
                'Defina a forma de pagamento do contrato.')
        

        idDiario = self.pool.get('account.journal').search(cr, uid,[('type', '=', 'sale'), ('company_id', '=', Contrato['company_id'][0])],limit=1)
        if not idDiario:
            raise osv.except_osv(_('Error!'),
                _('Defina o diário se vendas para esta empresa: "%s" (id:%d).') % (Contrato.company_id.name, Contrato.company_id.id))
        else:
            idDiario = idDiario[0]

        vlContrato = Contrato['total_proj']
        vlDias = Contrato['dias_intervalo']
#         if vlDias:
#             dtRefer = datetime.fromordinal(hj.toordinal()+(vlDias-1)).strftime('%Y-%m-%d')
#         else:
        dtRefer = hj.strftime('%Y-%m-%d')
         
        idServico = Contrato['obj_product_id'][0]
        if idServico:
            Servico = self.pool.get('product.product').browse(cr, uid, idServico, context)
         
        idPedido = Contrato['saleorder_id'][0]
        if idPedido:
            Pedido = self.pool.get('sale.order').browse(cr, uid, idPedido, context)
         
            idFormaPgto = Contrato['payment_term_id'][0]
            if idFormaPgto:
                ObjFormaPgto = self.pool.get('account.payment.term')
                FormaPgto = ObjFormaPgto.browse(cr, uid, idFormaPgto, context)
                pagamentos = ObjFormaPgto.compute(cr, uid, idFormaPgto, value=vlContrato, date_ref=dtRefer)
                NrParc = 1
                for pagto in pagamentos:
                    context['nrparcela'] = NrParc
                    context['iddiario'] = idDiario
                    if NrParc == 1:
                        context['date_invoice'] = datetime.fromordinal(pagto[0].toordinal()+(vlDias-1)).strftime('%Y-%m-%d')
                    else:
                        context['date_invoice'] = datetime.fromordinal(pagto[0].toordinal()-10).strftime('%Y-%m-%d')
                    context['vlunit'] = pagto[1]
                    context['sequencia'] = 1
                    context['vlqtde'] = 1
                    context['pcDesc'] = 0.0
                    
                    fatura = self._prepara_fatura(cr, uid, Contrato, Pedido, context)
                    _logger.info('Fatura: '+str(fatura))
                    idFatura = self._create_fatura(cr, uid, fatura, context)
                    _logger.info('Fatura Id '+str(idFatura)+' gerada com sucesso!')
                    #idFatura = False
                    lnfatura = self._prepara_linha_fatura(cr, uid, idFatura, Contrato, context)
                    _logger.info('Linha: '+str(lnfatura))
                    idLinha = self._create_line_fatura(cr , uid, lnfatura, context)
                    _logger.info('Linha Id '+str(idLinha)+' gerada com sucesso!')
                    
                    NrParc += 1

        
        #ObjContrato = self.get(cr, uid, [IdContrato], context=context)       
        #return self.write(cr, uid, ids, {'state': 'open'}, context=context)
        return False
    
    
    
    _columns = {
                'is_training': fields.boolean('Treinamento',readonly=True, states={'draft': [('readonly', False)]}),
                'area_tecnica_id': fields.many2one('area.tecnica', 'Portal', help="Selecione a área Tec./Portal para este contrato.",readonly=True, states={'draft': [('readonly', False)]}), 
                'categ_id': fields.many2one('product.category','Categoria', domain="[('type','=','normal')]", help="Selecione o grupo/categoria para este contrato.",readonly=True, states={'draft': [('readonly', False)]}),
                'obj_product_id': fields.many2one('product.product', 'Objeto', domain=[('sale_ok', '=', True)],readonly=True, states={'draft': [('readonly', False)]}), 
                'invoice_ids' : fields.one2many('account.invoice','contract_id','Faturas',readonly=True, states={'draft': [('readonly', False)]}),
                'regional_id': fields.many2one('res.company', 'Regional',readonly=True, states={'draft': [('readonly', False)]}),
                'hr_qtde': fields.float('Horas Previstas',digits=(6,4),readonly=True, states={'draft': [('readonly', False)]}),
                'vl_hora': fields.float('Valor/Hora',digits_compute=dp.get_precision('Product Price'),readonly=True, states={'draft': [('readonly', False)]}),
                'vl_desconto': fields.float('Valor Desconto',digits_compute=dp.get_precision('Product Price'),readonly=True, states={'draft': [('readonly', False)]}),
                'tecnico_id': fields.many2one('hr.employee', u'Gte.Técnico', domain=[('is_tech_mananger', '=', True)],readonly=True, states={'draft': [('readonly', False)]}),
                'vl_porc_tec': fields.float(u'Comissão Técnica',digits=(6,4), readonly=True, states={'draft': [('readonly', False)]}),
                'vl_porc_reg': fields.float(u'Comissão Regional',digits=(6,4), readonly=True, states={'draft': [('readonly', False)]}),
                'shop_id': fields.many2one('sale.shop', 'Regional', readonly=True, states={'draft': [('readonly', False)]}),
                'saleorder_id': fields.many2one('sale.order', 'Pedido',readonly=True, states={'draft': [('readonly', False)]}),
                'payment_term_id': fields.many2one('account.payment.term', 'Forma de Pagamento', required=True, readonly=True, states={'draft': [('readonly', False)]}),
                'inv_payment_term_id': fields.many2one('account.payment.term', 'Forma de Pgto das Faturas', readonly=True, states={'draft': [('readonly', False)]}),
                'total_proj': fields.function(_get_valor_fixo,  type='float', string='Total do Projeto',),
                'dias_intervalo': fields.integer('Dias para o primeiro Faturamento'),
               }

    _defaults = {
        'dias_intervalo': 5,
        'state': 'open',
    }
    

account_analytic_account()