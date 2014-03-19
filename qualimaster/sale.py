# -*- encoding: utf-8 -*-

import logging
import datetime
from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)

class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        'vl_porc_comiss': fields.float(u'% Comissão',digits=(6,4)),
    }

sale_shop()


class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    def account_analytic_create(self, cr , uid, valores, context):
        """Gera contrato com os campos contidos em valores"""
        ObjContrato = self.pool.get('account.analytic.account')
        IdContrato = ObjContrato.create(cr,uid,valores,context)
        return IdContrato
    
    def contrato_create(self, cr, uid, ids, context=None):
        """Gera o contrato para o pedido de vendas"""

        Order_Id = ids[0]
        Order_obj = self.read(cr, uid, Order_Id, context=context)

        Order_Shop_Id = Order_obj['shop_id'][0]
  
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', Order_Id)], context=context)
        for line in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):

            _logger.info('==> / '+line.name)
            obj_servico = self.pool.get('product.product').browse(cr, uid, line.product_id.id, context=context)
            
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
                        'name': Order_obj['name'] + ' / '+obj_servico['default_code'],
                        'type': 'contract',
                        'partner_id': int(Order_obj['partner_id'][0]),
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
                        }
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
               'area_tecnica_id': fields.many2one('area.tecnica', 'Portal'),
               'categ_prod_id': fields.many2one('product.category', 'Categoria'), 
               }

sale_order()