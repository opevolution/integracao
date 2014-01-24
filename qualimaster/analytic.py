# -*- encoding: utf-8 -*-
import logging

from openerp.osv import osv, fields

import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    
    def _prepara_linha_fatura(self, cr, uid, idFatura, contrato, context=None):
        if context is None:
            context = {}
        vlSeq = context.get('sequencia', False)
        vlPrecoU = context.get('vlunit', False)
        vlQtde = context.get('vlqtde', False)
        pcDesc = context.get('pcDesc', False)
        linha_fat = {
                     'origin': contrato.name,
                     'sequence': vlSeq or 10,
                     'invoice_id': idFatura,
                     'product_id': contrato.obj_product_id.id,
                     'price_unit': vlPrecoU or 0,
                     'quantity': vlQtde or 1,
                     'discount': pcDesc or 0,
                     }
        return linha_fat
        

    def _prepara_fatura(self, cr, uid, nrParcela, contrato, pedido, linhas, context=None ):
        """ Prepara o dicionário da fatura para criar a nova fatura
            :param int Número da Parcela
            :param browse_record contrato
            :param browse_record pedido
            :param list(int) Lista da linha da fatura para ser anexada
            :return: dicionário de valores para criar a fatura
        """
        if context is None:
            context = {}
        idDiario = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', contrato.company_id.id)],
            limit=1)
        if not idDiario:
            raise osv.except_osv(_('Error!'),
                _('Defina o diário se vendas para esta empresa: "%s" (id:%d).') % (contrato.company_id.name, contrato.company_id.id))
        
        invoice_vals = {
            'name': contrato.name +'_'+str(nrParcela),
            'origin': contrato.name,
            'type': 'out_invoice',
            'reference': contrato.name +'_'+str(nrParcela),
            'account_id': contrato.partner_id.property_account_receivable.id,
            'partner_id': contrato.partner_id.id,
            'journal_id': idDiario[0],
            #'invoice_line': [(6, 0, linhas)],
            'currency_id': pedido.pricelist_id.currency_id.id,
            'payment_term': False,
            'fiscal_position': contrato.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': contrato.company_id.id,
            'user_id': uid or False
        }
        return invoice_vals
    
    def _constroi_fatura(self, cr, uid, nrParcela, contrato, pedido, linhas, context=None):
        if context is None:
            context = {}
       
        
    def search_sale_order(self, cr, uid, id, context=None):
        """Procura Ordem de Venda ID"""
        if context is None:
            context = {}
        Order = self.pool.get('sale.order')
        idObj = Order.search(cr, uid, [('id','==',id)])
        return idObj

    def search_account_payment_term(self, cr, uid, id, context=None):
        """Procura Forma de Pagamento ID"""
        if context is None:
            context = {}
        Payment = self.pool.get('account.payment.term')
        idObj = Payment.search(cr, uid, [('id','==',id)])
        return idObj

    def contract_confirm(self, cr, uid, ids, context=None):
        """Confirma o Processamento do Contrato"""
        if context is None:
            context = {}
        IdContrato = ids[0]
        objContrato = self.read(cr, uid, IdContrato, context=context)
        
        
        _logger.info('Objeto Id Contrato ==> / '+str(IdContrato))
        #ObjContrato = self.get(cr, uid, [IdContrato], context=context)       
        #return self.write(cr, uid, ids, {'state': 'open'}, context=context)
        return False
    
    
    
    _columns = {
                'is_training': fields.boolean('Treinamento'),
                'area_tecnica_id': fields.many2one('area.tecnica', 'Portal', help="Selecione a área Tec./Portal para este contrato."), 
                'categ_id': fields.many2one('product.category','Categoria', domain="[('type','=','normal')]", help="Selecione o grupo/categoria para este contrato."),
                'obj_product_id': fields.many2one('product.product', 'Objeto', domain=[('sale_ok', '=', True)]), 
                'invoice_ids' : fields.one2many('account.invoice','contract_id','Faturas'),
                'regional_id': fields.many2one('res.company', 'Regional'),
                'hr_qtde': fields.float('Horas do Projeto',digits=(6,4)),
                'vl_hora': fields.float('Valor Hora',digits_compute=dp.get_precision('Product Price')),
                'vl_desconto': fields.float('Valor Desconto',digits_compute=dp.get_precision('Product Price')),
                'tecnico_id': fields.many2one('hr.employee', u'Gte.Técnico', domain=[('is_tech_mananger', '=', True)]),
                'vl_porc_tec': fields.float(u'Comissão Técnica',digits=(6,4)),
                'vl_porc_reg': fields.float(u'Comissão Regional',digits=(6,4)),
                'shop_id': fields.many2one('sale.shop', 'Regional', readonly=True, states={'draft': [('readonly', False)]}),
                'saleorder_id': fields.many2one('sale.order', 'Pedido', readonly=True),               
               }

    _defaults = {
        'state': 'open',
    }
    

account_analytic_account()