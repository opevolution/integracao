# -*- encoding: utf-8 -*-

import logging
#import datetime
from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

class sale_shop(orm.Model):
    _inherit = "sale.shop"
    _columns = {
        'vl_porc_comiss': fields.float(u'% Comissão',digits=(6,4)),
    }

sale_shop()

class sale_order(orm.Model):
    _inherit = 'sale.order'

#     def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
#         res = {}
#         res = super(sale_order,self)._amount_all(cr, uid, ids, field_name, arg, context)
#         for order in self.browse(cr, uid, ids, context=context):
#             res[order.id]['amount_total'] = res[order.id]['amount_total'] - 100
#         return res
# 
#     def _get_order(self, cr, uid, ids, context=None):
#         result = {}
#         for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
#             result[line.order_id.id] = True
#         return result.keys()

    def cancela_pedido(self, cr, uid, ids, context):
        ObjContrato = self.pool.get('account.analytic.account')
        for id in ids:
            IdsContrato = ObjContrato.search(cr,uid,[('saleorder_id','=',id)])
            if IdsContrato:
                for Contrato in ObjContrato.browse(cr,uid,IdsContrato,context=context):
                    if Contrato['state'] != 'cancelled':
                        raise orm.except_orm(_('Error!'),
                                            _(u'Cancele primeiro o contrato'))
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
            
    def account_analytic_create(self, cr , uid, valores, context):
        """Gera contrato com os campos contidos em valores"""
        ObjContrato = self.pool.get('account.analytic.account')
        IdContrato = ObjContrato.create(cr,uid,valores,context)
        return IdContrato
    
    def contrato_create(self, cr, uid, ids, context=None):
        """Gera o contrato para o pedido de vendas"""

        Order_Id = ids[0]
        Order_obj = self.read(cr, uid, Order_Id, context=context)

        if Order_obj['area_tecnica_id'] == False:
            raise orm.except_orm(_('Error!'),
                _(u'Informe a Área Técnica/Portal do Projeto'))

        if Order_obj['categ_prod_id'] == False:
            raise orm.except_orm(_('Error!'),
                _(u'Informe a Categoria do Projeto'))

        if Order_obj['dt_inicio'] == False:
            raise orm.except_orm(_('Error!'),
                _(u'Informe a Data Inicial do Projeto'))

        if Order_obj['dt_fim'] == False:
            raise orm.except_orm(_('Error!'),
                _(u'Informe a Data Final Projetada do Projeto'))
        
        if Order_obj['payment_term'] == False:
            raise orm.except_orm(_('Error!'),
                _(u'Informe a Forma de Pagamento'))
                

        Order_Shop_Id = Order_obj['shop_id'][0]
        
        Empresa = self.pool.get('res.partner').browse(cr, uid, int(Order_obj['partner_id'][0]), context=context)
        Contato = False
        
        if Empresa.is_company == False:
            if Empresa.parent_id:
                Contato = Empresa 
                Empresa = self.pool.get('res.partner').browse(cr, uid, Contato.parent_id.id, context=context)
        
        if  Order_obj['payment_term']:
            FormaPgto =  Order_obj['payment_term'][0]
        else:
            FormaPgto = False
  
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', Order_Id)], context=context)
        for line in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):

            _logger.info('==> / '+line.name)
            obj_servico = self.pool.get('product.product').browse(cr, uid, line.product_id.id, context=context)
            
            if obj_servico['default_code'] == False:
                codServico = ''
                raise orm.except_orm(_('Error!'),
                    _(u'Adicione um código para o Serviço no Cadastro de Produtos'))
            else:
                codServico = obj_servico['default_code']
            
            obj_shop = self.pool.get('sale.shop').browse(cr,uid,Order_Shop_Id,context=context)
            comis_reg = obj_shop['vl_porc_comiss']
            _logger.info('Objeto comis_reg ==> / '+str(comis_reg))
            
            hrqtde = line.product_uom_qty or 0
            vlhora = line.price_unit or 0
            pcDesc = line.discount/100 or 0
            vlTotal = hrqtde * vlhora
            if pcDesc > 0:
                vlDesc = (hrqtde * vlhora) * pcDesc
            else:
                vlDesc = 0
            IdAreaTec = Order_obj['area_tecnica_id'][0]
            IdResp = None
            IdTec = None
            if IdAreaTec:
                obj_AreaTec = self.pool.get('area.tecnica').browse(cr,uid,IdAreaTec,context=context)
                IdResp = obj_AreaTec['resp_id'].id
                if IdResp == False:
                    IdResp = Order_obj['user_id'][0]
                IdTec  = obj_AreaTec['tecnico_id'].id
#            tmpInicio = int(obj_servico.sale_delay)
#            tmpTrab = obj_servico.prazo_projeto
            contract = {
                        'name': Order_obj['name'] + ' / '+codServico,
                        'type': 'contract',
                        'partner_id': Empresa.id,
                        'contato_id': False,
                        'user_id': IdResp, 
                        'manager_id': int(Order_obj['user_id'][0]),
                        'company_id': int(Order_obj['company_id'][0]),
                        'fix_price_invoices': True,
                        'use_timesheets': False,
                        'use_phases': False,
                        'is_training': False,
                        'hr_qtde': hrqtde,
                        'vl_hora': vlhora,
                        'amount_max': vlTotal,
                        'vl_desconto': vlDesc, 
                        'obj_product_id': line.product_id.id,
                        'area_tecnica_id': Order_obj['area_tecnica_id'][0],
                        'categ_id': Order_obj['categ_prod_id'][0], 
                        'shop_id': int(Order_Shop_Id),
                        'vl_porc_reg': comis_reg,
                        'tecnico_id': IdTec or None, 
                        'vl_porc_tec': 0,
                        'saleorder_id': Order_Id,
                        'use_timesheets': False,
                        'use_tasks': False,
                        'use_phases': False,
                        'use_issues': False,
                        'is_training': False,
                        'state': 'draft',
                        'description': Order_obj['note'] or '',
                        'payment_term_id': FormaPgto,
                        'vl_desconto': Order_obj['vl_desconto'],
                        'date_start': Order_obj['dt_inicio'],
                        'date': Order_obj['dt_fim'],
                        }
            if Contato:
                contract['contato_id'] = Contato.id 
            IdModelProjeto = obj_servico['model_project_id'].id
            if IdModelProjeto != False:
                objMdProj = self.pool.get('model.project').browse(cr,uid,IdModelProjeto,context=context)
                contract['use_timesheets']  = objMdProj['use_timesheets']
                contract['use_tasks']       = objMdProj['use_tasks']
                contract['use_phases']      = objMdProj['use_phases']
                contract['use_issues']      = objMdProj['use_issues']
                contract['is_training']     = objMdProj['is_training']
                _logger.info('Descricao do Projeto Modelo ==> / '+str(objMdProj['name']))
              
            IdContrato = self.account_analytic_create(cr, uid, contract, context)
            _logger.info('Contrato '+str(IdContrato)+' foi criado!')
            self.write(cr, uid, [Order_Id], {'state': 'done'})
        return False

    _columns = {
               'area_tecnica_id': fields.many2one('area.tecnica', 'Portal', readonly=False, states={'done': [('readonly', True)]}),
               'categ_prod_id': fields.many2one('product.category', 'Categoria', readonly=False, states={'done': [('readonly', True)]}),
               'vl_desconto': fields.float('Valor Desconto',digits_compute=dp.get_precision('Product Price'), readonly=False, states={'done': [('readonly', True)]}), 
               'dt_inicio': fields.date('Data Inicial', readonly=False, states={'done': [('readonly', True)]}),
               'dt_fim': fields.date('Data Final', readonly=False, states={'done': [('readonly', True)]}),
               }
    

sale_order()