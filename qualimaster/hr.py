# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields

class hr_employee(osv.osv):

    _inherit = 'hr.employee'
    
    
    _columns = {
               'is_tech_mananger': fields.boolean(u'Gerente Técnico'),
               'pr_comiss_tec': fields.float(u'% Comissão Técnica', digits=(6,4)),
               }

hr_employee()
