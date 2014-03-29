# -*- encoding: utf-8 -*-
import logging
import time
import calendar
from datetime import datetime
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
import re

_logger = logging.getLogger(__name__)

def DiasMes(f):
    firstweekday,days=calendar.monthrange(f.year,f.month)
    return days

def DiasMesEx(Mes,Ano):
    firstweekday,days=calendar.monthrange(Ano,Mes)
    return days

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'

    def search_invoice_number(self, cr, uid,idCompany,nrInternal, context=None):
        if context is None:
            context = {}
        _logger.info('Procura Invoice Number:'+str(nrInternal)+' / '+str(idCompany))
         
        domain = []
        domain.extend(
            [('company_id', '=', idCompany),
            ('internal_number', '=', nrInternal),])
         
        invoice_id = self.pool.get('account.invoice').search(cr, uid, domain)
             
        if len(invoice_id) > 0:
            return invoice_id
             
        return False

    def set_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
    
    def _only_digits(self, v):
        return re.sub('[^0-9]', '', v)

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
    
    def _data_venc_prox(self, cr, uid, DataFat):
        context = {}
        ObjFormPagto = self.pool.get('account.payment.term')
        if isinstance(DataFat, datetime):
            Dia = DataFat.day
            Mes = DataFat.month
            Ano = DataFat.year
            Udi = DiasMes(DataFat)
            if Dia > Udi:
                Dia = Dia - Udi
                Mes = Mes + 1
                if Mes > 12:
                    Ano = Ano + 1
                Udi = DiasMes(datetime(Ano, Mes, Dia, 0, 0))
            ids = ObjFormPagto.search(cr,uid,[('for_contract', '=', True)],order='dia_emiss')
            diasel = 0
            diapri = 0
            for FormPagto in ObjFormPagto.browse(cr,uid,ids,context):
                
                if FormPagto.dia_emiss < Udi:
                    x = FormPagto.dia_emiss
                else:
                    x = Udi
                if diapri == 0:
                    diapri = x
                if Dia < x:
                    diasel = x
                    break
            if diasel == 0:
                diasel = diapri
                Mes = Mes + 1
                if Mes > 12:
                    Mes = 1
                    Ano = Ano + 1
            return datetime(Ano, Mes, diasel, 0, 0)
    
    def _prepara_fatura(self, cr, uid, contrato, pedido, context=None ):
        if context is None:
            context = {}
        invoice_vals = False
        idPartner = contrato['partner_id'][0]
        
        Partner = self.pool.get('res.partner').browse(cr, uid, idPartner, context)
        fcateg = self.pool.get('l10n_br_account.fiscal.category')
#        idfcateg = False
        idfcateg = fcateg.search(cr,uid,[('code', '=', u'Serviço')])[0]
        
        if not idfcateg:
            idfcateg = False
            
        nrParcela = context.get('nrparcela', False)
        idDiario  = context.get('iddiario', False)
        dtInvoice = context.get('date_invoice', False)
        dtVenc    = context.get('date_due', False)

        if contrato['name'] == False:
            raise osv.except_osv(_('Error!'),
                _(u'Informe um Número para o Contrato'))
       

        nrcontrato = contrato['name']
        
        x = nrcontrato.find(' / ')
        nrcontrato = nrcontrato[0:x] 

        vlName = contrato['name'] +' / '+str(nrParcela)
        
        nrfatura = self._only_digits(nrcontrato)
        
        _logger.info('Prepara Fatura: NrParcela: '+str(nrParcela)+' / Id Diário: '+str(idDiario)+' / Data: '+str(dtInvoice))
        
        if dtVenc == False:
            FormaPgtoId = contrato['inv_payment_term_id'][0]
        else:
            FormaPgtoId = False
        
        if nrParcela:
            invoice_vals = {
                            'name': vlName,
                            'origin': contrato['name'],
                            'type': 'out_invoice',
                            'fiscal_type': 'service',
                            'fiscal_category_id': idfcateg,
                            'reference': vlName,
                            'account_id': Partner.property_account_receivable.id,
                            'partner_id': idPartner,
                            'journal_id': idDiario,
                            #'invoice_line': [(6, 0, linhas)],
                            'currency_id': pedido.pricelist_id.currency_id.id,
                            'payment_term': FormaPgtoId,
                            'fiscal_position': Partner.property_account_position.id,
                            'date_invoice': dtInvoice,
                            'date_due': dtVenc,
                            'company_id': contrato['company_id'][0],
                            'user_id': uid or False,
                            'contract_id': contrato['id'],
                            'internal_number': '%s%02d' % (nrfatura,nrParcela),
                            'state': 'draft',
                            }
            
        return invoice_vals
    
    def _prepara_linha_fatura(self, cr, uid, idFatura, contrato, context=None):
        if context is None:
            context = {}


        idProd = contrato['obj_product_id'][0]
        produto = self.pool.get('product.product').browse(cr, uid, idProd, context)
        
        vlSeq = context.get('sequencia', False)
        vlPrecoU = context.get('vlunit', False)
        vlQtde = context.get('vlqtde', False)
        pcDesc = context.get('pcDesc', False)
        linha_fat = {
                     'name': produto.name_template,
                     'origin': contrato['name'],
                     'sequence': vlSeq or 10,
                     'invoice_id': int(idFatura) or None,
                     'product_id': idProd,
                     'price_unit': vlPrecoU or 0.00,
                     'quantity': vlQtde or 1,
                     'discount': pcDesc or 0.00,
                     'product_type': 'service',
                     'service_type_id': produto.service_type_id.id,
                     'fiscal_classification_id': produto.property_fiscal_classification.id,
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

        #hj = datetime.now()
        
        idContrato = ids[0]
        Contrato  = self.read(cr, uid, idContrato, context=context)
        objFatura = self.pool.get('account.invoice')
        
        if not Contrato['date_start']:
            raise osv.except_osv('Erro!',
                u'Defina a data início de execução do projeto.')

        if not Contrato['date']:
            raise osv.except_osv('Erro!',
                u'Defina a data máxima de termino de execução do projeto.')

        if Contrato['date'] <= Contrato['date_start']:
            raise osv.except_osv('Erro!',
                u'A data de conclusão não pode ser menor que a data de inicio do projeto.')

        if Contrato['date'] <= Contrato['date_start']:
            raise osv.except_osv('Erro!',
                u'A data de conclusão não pode ser menor que a data de inici.')

        if not Contrato['inv_payment_term_id']:
            raise osv.except_osv('Erro!',
                u'Defina a forma de pagamento para as faturas a serem geradas.')
        
        if not Contrato['payment_term_id']:
            raise osv.except_osv('Erro!',
                u'Defina a forma de pagamento do contrato.')

        ObjFormaPgto = self.pool.get('account.payment.term')

        idCliente = Contrato['partner_id'][0]
        Cliente = self.pool.get('res.partner').browse(cr, uid, idCliente, context)
        if Cliente.parent_id:
            raise osv.except_osv(_('Error!'),
                    _(u'O cliente não pode ser um contato./n Informe a empresa que este contato pertence.'))

        idDiario = self.pool.get('account.journal').search(cr, uid,[('type', '=', 'sale'), ('company_id', '=', Contrato['company_id'][0])],limit=1)
        if not idDiario:
            raise osv.except_osv(_('Error!'),
                _(u'Defina o diário se vendas para esta empresa: "%s" (id:%d).') % (Contrato.company_id.name, Contrato.company_id.id))
        else:
            idDiario = idDiario[0]

        vlContrato = Contrato['total_proj']

        #= hj.strftime('%Y-%m-%d')
         
        idServico = Contrato['obj_product_id'][0]
        if idServico:
            Servico = self.pool.get('product.product').browse(cr, uid, idServico, context)
            if Servico.service_type_id.id == False:
                raise osv.except_osv(_('Error!'),
                    _(u'Este produto não tem o tipo de serviço.'))

            if Servico.property_fiscal_classification.id == False:
                raise osv.except_osv(_('Error!'),
                    _(u'Este produto não tem a Classificação Fiscal.'))

        
        # context['date_invoice'] = datetime.fromordinal(dtFat.toordinal()-10).strftime('%Y-%m-%d') 
        idPedido = Contrato['saleorder_id'][0]
        if idPedido:
            Pedido = self.pool.get('sale.order').browse(cr, uid, idPedido, context)
            idFormaPgto = Contrato['payment_term_id'][0]
            idInvFormaPagto = Contrato['inv_payment_term_id'][0]
            if idFormaPgto:
                FormaPgto = ObjFormaPgto.browse(cr, uid, idFormaPgto, context)
                Is_Pos    = FormaPgto.is_pos
                
                if Is_Pos:
                    dtRefer = Contrato['date']
                else:
                    dtRefer = Contrato['date_start']
                _logger.info('Data Referencia Para Faturamento do Contrato: '+str(dtRefer))
            
                InvFormaPagto = ObjFormaPgto.browse(cr, uid, idInvFormaPagto, context)
                DiaBaseFatu = InvFormaPagto.dia_emiss
                #DiaBasePgto = InvFormaPagto.line_ids[0].days2
                    
                dtFat = datetime.strptime(dtRefer,"%Y-%m-%d")
                DiaFatu = dtFat.day
                MesFatu = dtFat.month
                AnoFatu = dtFat.year
                #if DiaFatu > DiasMesEx(MesFatu,AnoFatu):
                #    xDiaFatu = DiasMesEx(MesFatu,AnoFatu)
                #else:
                #    xDiaFatu = DiaFatu
                    
                DiaPagto = InvFormaPagto.line_ids[0].days2
                MesPagto = dtFat.month
                AnoPagto = dtFat.year
                if DiaPagto <= DiaFatu:
                    MesPagto = MesPagto+1
                    while MesPagto > 12:
                        MesPagto = MesPagto - 12
                        AnoPagto = dtFat.year + 1
                if DiaPagto > DiasMesEx(MesPagto,AnoPagto):
                    xDiaPagto = DiasMesEx(MesPagto,AnoPagto)
                else:
                    xDiaPagto = DiaPagto
                    
                _logger.info('Contrato:'+str(Contrato['name']))

                pagamentos = ObjFormaPgto.compute(cr, uid, idFormaPgto, value=vlContrato, date_ref=dtRefer)
                
                NrParc = 1
                for pagto in pagamentos:
                    _logger.info('Parcela: '+str(NrParc)+'/'+str(len(pagamentos)))
                    context = {}
                    context['nrparcela'] = NrParc
                    context['iddiario'] = idDiario
                    if NrParc == 1:
                        _logger.info('Parcela: '+str(NrParc)+
                                     ' / Dia Faturamento: '+str(DiaFatu)+'/'+str(MesFatu)+'/'+str(AnoFatu)+
                                     ' / Dia Pagamento: '+str(xDiaPagto)+'/'+str(MesPagto)+'/'+str(AnoPagto))

                        dtFat  = datetime.strptime(str(AnoFatu)+'-'+str(MesFatu)+'-'+str(DiaFatu),'%Y-%m-%d')
                        dtVenc = datetime.strptime(str(AnoPagto)+'-'+str(MesPagto)+'-'+str(DiaPagto),'%Y-%m-%d')
                        context['date_invoice'] = dtFat.strftime('%Y-%m-%d')
                        context['date_due'] = dtVenc.strftime('%Y-%m-%d')
                        _logger.info("1. Fatura: ["+str(context['date_invoice'])+' -> '+context['date_due'])
                        if DiaFatu < DiaBaseFatu: 
                            MesFatu = MesFatu - 1
                    else:
                        DiaFatu = DiaBaseFatu
                        MesFatu = MesFatu + 1
                        while MesFatu > 12:
                            MesFatu = MesFatu - 12
                            AnoFatu = AnoFatu + 1
                        if DiaFatu > DiasMesEx(MesFatu,AnoFatu):
                            xDiaFatu = DiasMesEx(MesFatu,AnoFatu)
                        else:
                            xDiaFatu = DiaFatu

                        MesPagto = MesPagto + 1
                        while MesPagto > 12:
                            MesPagto = MesPagto - 12
                            AnoPagto = AnoPagto + 1
                        
                        if DiaPagto > DiasMesEx(MesPagto,AnoPagto):
                            xDiaPagto = DiasMesEx(MesPagto,AnoPagto)
                        else:
                            xDiaPagto = DiaPagto

                        _logger.info('Parcela: '+str(NrParc)+
                                     ' / Dia Faturamento: '+str(xDiaFatu)+'/'+str(MesFatu)+'/'+str(AnoFatu)+
                                     ' / Dia Pagamento: '+str(xDiaPagto)+'/'+str(MesPagto)+'/'+str(AnoPagto))

                        dtFat  = datetime.strptime(str(AnoFatu)+'-'+str(MesFatu)+'-'+str(DiaFatu),'%Y-%m-%d')
                        dtVenc = datetime.strptime(str(AnoPagto)+'-'+str(MesPagto)+'-'+str(DiaPagto),'%Y-%m-%d')
                        context['date_invoice'] = dtFat.strftime('%Y-%m-%d')
                        context['date_due'] = dtVenc.strftime('%Y-%m-%d')
                        _logger.info(str(NrParc)+". Fatura: ["+str(context['date_invoice'])+' -> '+context['date_due'])
                    context['vlunit'] = pagto[1]
                    context['sequencia'] = 1
                    context['vlqtde'] = 1
                    context['pcDesc'] = 0.0

                    fatura = self._prepara_fatura(cr, uid, Contrato, Pedido, context)
                    _logger.info('Fatura: '+str(fatura))
                    
                    idFatura = self.search_invoice_number(cr, uid,Contrato['company_id'][0],fatura['internal_number'],context)
                    
                    _logger.info('Tem Faturas? '+str(idFatura))
                    
                    if not idFatura:                    
                        idFatura = self._create_fatura(cr, uid, fatura, context)
                        _logger.info('Fatura Id '+str(idFatura)+' gerada com sucesso!')
                        #idFatura = False
                        lnfatura = self._prepara_linha_fatura(cr, uid, idFatura, Contrato, context)
                        _logger.info('Linha: '+str(lnfatura))
                        idLinha = self._create_line_fatura(cr , uid, lnfatura, context)
                        _logger.info('Linha Id '+str(idLinha)+' gerada com sucesso!')
                        NrParc += 1
                    else:
                        [Fatura] = objFatura.browse(cr,uid,idFatura,context)
                        if Fatura.state == 'cancel':
                            objFatura.write(cr, uid, idFatura, {'contract_id': Contrato['id'],'state':'draft'}, context)
                        else:
                            objFatura.write(cr, uid, idFatura, {'contract_id': Contrato['id']}, context)
                        NrParc += 1

        
        #ObjContrato = self.get(cr, uid, [idContrato], context=context)       
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)
#        return False
    
    def set_cancel(self, cr, uid, ids, context=None):
        ObjFatura = self.pool.get('account.invoice')
        for account in self.browse(cr, uid, ids, context=context):
            for idf in account.invoice_ids:
                fatura = ObjFatura.browse(cr, uid, idf.id,context=context) 
                if fatura.state in ['draft','cancel']:
                    _logger.info('Fatura é draft:'+str(fatura.id))
                    ObjFatura.write(cr,uid,[fatura.id],{'state': 'cancel'})
                elif fatura.state in ['proforma','proforma2','sefaz_export']:
                    wf_service = netsvc.LocalService('workflow')
                    wf_service.trg_validate(uid, 'account.invoice', fatura.id, 'invoice_cancel', cr)
                else:
                    raise osv.except_osv(_('Error!'),
                        _(u'Cancele manualmente a/as fatura/as que já foram emitidas a NF.'))
        return self.write(cr, uid, ids, {'state': 'cancelled'}, context=context)
    
    
    _columns = {
                'is_training': fields.boolean('Treinamento',readonly=True, states={'draft': [('readonly', False)]}),
                'area_tecnica_id': fields.many2one('area.tecnica', 'Portal', help="Selecione a área Tec./Portal para este contrato.",readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},), 
                'categ_id': fields.many2one('product.category','Categoria', domain="[('type','=','normal')]", help="Selecione o grupo/categoria para este contrato.",readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'obj_product_id': fields.many2one('product.product', 'Objeto', domain=[('sale_ok', '=', True)],readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},), 
                'invoice_ids' : fields.one2many('account.invoice','contract_id','Faturas',readonly=True, states={'draft': [('readonly', False)],'open': [('readonly', False)]}),
                'regional_id': fields.many2one('res.company', 'Regional',readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'hr_qtde': fields.float('Horas Previstas',digits=(6,4),readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'vl_hora': fields.float('Valor/Hora',digits_compute=dp.get_precision('Product Price'),readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'vl_desconto': fields.float('Valor Desconto',digits_compute=dp.get_precision('Product Price'),readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'tecnico_id': fields.many2one('hr.employee', u'Gte.Técnico', domain=[('is_tech_mananger', '=', True)],readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'vl_porc_tec': fields.float(u'Comissão Técnica',digits=(6,4), readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'vl_porc_reg': fields.float(u'Comissão Regional',digits=(6,4), readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'shop_id': fields.many2one('sale.shop', 'Regional', readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'saleorder_id': fields.many2one('sale.order', 'Pedido',readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'payment_term_id': fields.many2one('account.payment.term', 'Forma de Pagamento', readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]},),
                'inv_payment_term_id': fields.many2one('account.payment.term', 'Forma de Pgto das Faturas', domain=[('for_contract','=',True)], readonly=True, states={'open': [('readonly', False)],'draft': [('readonly', False)]}),
                'total_proj': fields.function(_get_valor_fixo,  type='float', string='Total do Projeto',),
                'contato_id': fields.many2one('res.partner', u'Contato/Responsável',  domain="[('is_company','=',False),('parent_id','=',partner_id)]", states={'open': [('readonly', False)],'draft': [('readonly', False)]},), 
               }

    _defaults = {
        'state': 'open',
    }
    

account_analytic_account()