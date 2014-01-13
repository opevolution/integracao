# -*- coding: utf-8 -*-
##############################################################################
#
##############################################################################


from openerp.osv import osv, fields

class product_product(osv.osv):

    _inherit = 'product.product'
    _columns = {
                'project_template_id': fields.many2one('project.project', 'Projeto Modelo',  domain=[('state', '=', 'template')]),
                'area_tecnica_id': fields.many2one('area.tecnica', u'Área/Portal'),
                }

product_product()