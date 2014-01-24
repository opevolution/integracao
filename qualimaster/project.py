# -*- encoding: utf-8 -*-
import logging

from openerp.osv import osv, fields

_logger = logging.getLogger(__name__)

class project(osv.osv):
    _inherit = "project.project"

    def analytic_account_search(self, cr , uid, id, context=None):
        objAnalAcc = self.pool.get('account.analytic.account')
        idAnalAcc = objAnalAcc.search(cr, uid, [('id','in',id)])
        return idAnalAcc

    def create(self, cr, uid, vals, context=None):
        project_id = super(project, self).create(cr, uid, vals, context)
#        idContrato = self.analytic_account_search(self, cr, uid, project_id)
        _logger.info('Projeto '+str(project_id)+' foi criado!')
        return project_id
