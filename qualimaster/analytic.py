# -*- encoding: utf-8 -*-
import logging

from openerp.osv import osv, fields

import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'

    def contract_confirm(self, cr, uid, ids, context=None):
        IdContrato = ids[0]
        _logger.info('Objeto Id Contrato ==> / '+str(IdContrato))
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)
    
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
               }

    _defaults = {
        'state': 'open',
    }
    

account_analytic_account()