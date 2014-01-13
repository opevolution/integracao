# -*- coding: utf-8 -*-

from osv import fields, osv

class area_tecnica(osv.osv):
    """área de atuacao técnica"""
    _name = 'area.tecnica'
    _columns = {
                'name': fields.char('Área/Portal', size=30, required=True),
                'code': fields.char('Código', size=5, required=True),
                'resp_id': fields.many2one('res.users', 'Responsável', required=True),
                }

area_tecnica()
