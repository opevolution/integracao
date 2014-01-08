# -*- coding: utf-8 -*-

from osv import fields, osv

class area_atuacao(osv.osv):
    """área de atuacao do Serviço"""
    _name = 'area.atuacao'
    _columns = {
                'name': fields.char('Área', size=30, required=True),
                'code': fields.char('Código', size=5, required=True),
                'resp_id': fields.many2one('res.users', 'Responsável', required=True),
                }

area_atuacao()
