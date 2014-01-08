# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    
    _columns = {
               'obj_product_id': fields.many2one('product.product', 'Objeto', domain=[('sale_ok', '=', True)]), 
               'areaatu_id': fields.many2one('area.atuacao', 'Área', required=True),
               'invoice_ids' : fields.one2many('account.invoice','contract_id','Faturas'),
               }

account_analytic_account()