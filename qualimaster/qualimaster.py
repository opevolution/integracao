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

class model_project(osv.osv):
    """Modelo de Projetos"""
    _name = 'model.project'

    def _task_count(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, 0)
        ctx = context.copy()
        ctx['active_test'] = False
        task_ids = self.pool.get('model.task').search(cr, uid, [('model_project_id', 'in', ids)], context=ctx)
        for task in self.pool.get('model.task').browse(cr, uid, task_ids, context):
            res[task.model_project_id.id] += 1
        return res
    
    def _phase_count(self, cr, uid, ids, field_name, arg, context=None):
        if context is None:
            context = {}
        res = dict.fromkeys(ids, 0)
        ctx = context.copy()
        ctx['active_test'] = False
        phase_ids = self.pool.get('model.phase').search(cr, uid, [('model_project_id', 'in', ids)], context=ctx)
        for phase in self.pool.get('model.phase').browse(cr, uid, phase_ids, context):
            res[phase.model_project_id.id] += 1
        return res

    def _get_hours_project(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cr.execute("""
            SELECT model_project_id, COALESCE(SUM(planned_hours), 0.0)
            FROM model_task WHERE model_project_id IN %s
            GROUP BY model_project_id
            """, (tuple(ids),))
        for i in ids:
            res[i] = 0.0

        for i, planned in cr.fetchall():
            res[i] += planned
        return res

    _columns = {
                'name': fields.char('Nome', size=128, required=True,),
                'use_tasks': fields.boolean('Tarefas'),
                'use_scrum': fields.boolean('Scrum'),
                'use_timesheets': fields.boolean('Apontamento de Horas'),
                'use_phases': fields.boolean('Fases'),
                'use_issues': fields.boolean('Incidentes'),
                'description': fields.text('Descrição'),
                'planned_hours': fields.float('Total Horas Planejadas',),
                'task_ids': fields.one2many('model.task','model_project_id','Tarefas'),
                'task_count': fields.function(_task_count, type='integer', string="Qtde. Tarefas"),
                'phase_count': fields.function(_phase_count, type='integer', string="Qtde. Fases"),
                'planned_hours_count': fields.function(_get_hours_project,  type='float', string='Total Horas Planejadas',), 
                }

model_project()

class model_task(osv.osv):
    """Tarefas do Modelo de Projetos"""
    _name = 'model.task'

    _columns = {
                'name': fields.char('Nome', size=128, required=True,),
                'description': fields.text('Descrição'),
                'priority': fields.selection([('4','Muito Baixa'), ('3','Baixa'), ('2','Média'), ('1','Importante'), ('0','Muito Importante')], 'Prioridade', select=True),                
                'sequence': fields.integer('Sequencia', select=True, help="Seleciona a sequencia da tarefa.", required=True,),
                'model_project_id': fields.many2one('model.project','Projeto Modelo', domain="[('use_tasks','=',True)]", ondelete='set null', required=True,),
                'planned_hours': fields.float('Horas Planejadas', select=True,  required=True,),
                'parent_ids': fields.many2many('model.task', 'model_project_task_parent_rel', 'model_task_id', 'parent_id', 'Tarefas Pai'),
                'child_ids': fields.many2many('model.task', 'model_project_task_parent_rel', 'parent_id', 'task_id', 'Tarefas Filho'),
                'phase_id': fields.many2one('model.phase','Fase Projeto Modelo',ondelete='set null',),
                }
    _defaults = {
                 'priority': '2',
                 'sequence': 10,
                 }
    _order = "priority, sequence, name, id"

model_task()

class model_phase(osv.osv):
    """Modelo de Fase de Projeto"""
    _name = "model.phase"
    _description = "Modelo de Fase de Projeto"

    _columns = {
                'name': fields.char("Name", size=64, required=True),
                'model_project_id': fields.many2one('model.project', 'Projeto Modelo', domain="[('use_tasks','=',True)]", required=True, select=True),
                'next_phase_ids': fields.many2many('model.phase', 'model_project_phase_rel', 'prv_model_phase_id', 'next_model_phase_id', u'Próxima Fase',),
                'previous_phase_ids': fields.many2many('model.phase', 'model_project_phase_rel', 'next_model_phase_id', 'prv_model_phase_id', 'Fase Anterior'),
                'sequence': fields.integer('Sequencia', select=True, required=True,),
                'product_uom': fields.many2one('product.uom', 'Unidade de Medida', required=True,),
                'task_ids': fields.one2many('model.task', 'phase_id', "Tarefas do Projeto Modelo"),
                'description': fields.text('Descrição'),
                }
    _defaults = {
                 'sequence': 10,
                 }
    _order = "model_project_id, sequence"

model_phase();

