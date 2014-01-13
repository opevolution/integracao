# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

import openerp.addons.decimal_precision as dp

class account_analytic_account(osv.osv):
    _inherit = 'account.analytic.account'
    
    _columns = {
               'area_tecnica_id': fields.many2one('area.tecnica', 'Portal', help="Selecione a área Tec./Portal para este contrato."), 
               'categ_id': fields.many2one('product.category','Categoria', domain="[('type','=','normal')]", help="Selecione o grupo/categoria para este contrato."),
               'obj_product_id': fields.many2one('product.product', 'Objeto', domain=[('sale_ok', '=', True)]), 
               'invoice_ids' : fields.one2many('account.invoice','contract_id','Faturas'),
               'regional_id': fields.many2one('res.company', 'Regional'),
               'hr_qtde': fields.float('Horas do Projeto',digits=(6,4)),
               'vl_hora': fields.float('Valor Hora',digits_compute=dp.get_precision('Product Price')),
               'tecnico_id': fields.many2one('hr.employee', u'Gte.Técnico', domain=[('is_tech_mananger', '=', True)]),
               }

account_analytic_account()