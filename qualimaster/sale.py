# -*- encoding: utf-8 -*-

import logging
import datetime
from openerp.osv import orm, fields

_logger = logging.getLogger(__name__)

class sale_order(orm.Model):
    _inherit = 'sale.order'
    
    def cons_id(self):
        mach=[]
        #lids=self.pool.get('res.users').search(cr,uid,[('active','=',True)])
        return 0
     
    def contrato_create(self, cr, uid, ids, context=None):
        contract_obj = self.pool.get('account.analytic.account')
        contract_ids = []
        data = self.read(cr, uid, ids, [])[0]
        dt_atual = datetime.datetime.today()
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            obj_servico = self.pool.get('product.product').browse(cr, uid, line.product_id.id, context=context)
            tmpInicio = int(obj_servico.sale_delay)
            tmpTrab = obj_servico.prazo_projeto
            contract = {
                        'name': data['name'] + ' / '+line.name,
                        'type': 'contract',
                        'partner_id': int(data['partner_id'][0]),
                        'user_id': int(data['user_id'][0]), 
                        'manager_id': int(data['user_id'][0]),
                        'company_id': int(data['company_id'][0]),
                        'fix_price_invoices': True,
                        'use_timesheets': True,
                        'use_phases': True,
                        'obj_product_id': line.product_id.id, 
                        'areaatu_id': data['areaatu_id'][0],
                        }
            _logger.info(data['name'] + ' / '+line.name)
            contract_id = contract_obj.create(cr,uid,contract,context)
            contract_ids.append(contract_id)
        
        #self.write(cr, uid, ids, ['partner_id'], context=context)
        return False

    _columns = {
               'areaatu_id': fields.many2one('area.atuacao', 'Área', required=True),
               }

sale_order()