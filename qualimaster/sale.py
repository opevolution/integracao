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
    
    def cons_id(self):
        mach=[]
        #lids=self.pool.get('res.users').search(cr,uid,[('active','=',True)])
        return 0
     
    def contrato_create(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('account.analytic.account')
        contract_ids = []
        Order_Id = ids[0]
        Order_obj = self.read(cr, uid, Order_Id, context=context)
        _logger.info('Objeto Order.Sale ==> / '+str(Order_Id))
        Order_Shop_Id = Order_obj['shop_id'][0]
        _logger.info('Objeto shop.order ==> / '+str(Order_Shop_Id))
        dt_atual = datetime.datetime.today()
  
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
                #_logger.info('Objeto area_tecnica_id ==> / '+str(IdAreaTec))
                obj_AreaTec = self.pool.get('area.tecnica').browse(cr,uid,IdAreaTec,context=context)
                IdResp = obj_AreaTec['resp_id'].id
                #_logger.info('Objeto nome ==> / '+obj_AreaTec['name'])
                #_logger.info('Objeto IdResp A ==> / '+str(IdResp))
                if IdResp == False:
                    IdResp = Order_obj['user_id'][0]
                    #_logger.info('Objeto IdResp B ==> / '+str(IdResp))
                IdTec  = obj_AreaTec['tecnico_id'].id
                #_logger.info('Objeto IdTec ==> / '+str(IdTec))
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
                        'tecnico_id': int(IdTec), 
                        'vl_porc_tec': 0,
                        'state': 'draft',
                        }
            #_logger.info(data['name'] + ' / '+line.name)
            contract_id = contract_obj.create(cr,uid,contract,context)
            contract_ids.append(contract_id)
            
            #self.write(cr, uid, [Order_Id], {'state': 'done'})
        return False

    _columns = {
               'area_tecnica_id': fields.many2one('area.tecnica', 'Portal', required=True),
               'categ_prod_id': fields.many2one('product.category', 'Categoria', required=True), 
               }

sale_order()