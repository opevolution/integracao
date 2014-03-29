# -*- encoding: utf-8 -*-

import logging
import time
from datetime import datetime
from osv import osv, fields

import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class wiz_envio_saldo(osv.osv_memory):
    """  Confirma os Extratos Marcados e Envia Email de Aviso para Gerente Financeiro """
    
    _name = 'wiz.envio_saldo'

    def __split1000(self, s, sep=',', dec=None):
        z = -1
        if dec == None:
            x = 0
            while x < len(s):
                if s[x].isdigit() == False:
                    z = x
                    dec = s[x]
                    break
                else:
                    x = x + 1
        else:
            z = s.find(dec)
    
        if z >= 0:
            #print s[:z]
            return self.__split1000(s[:z], sep, dec) + s[z:]
        else:
            if len(s) <= 3:
                return s  
            else: 
                x = s[:3]
                
                if x.isdigit() == False:
                    return s
                else:
                    return self.__split1000(s[:-3], sep) + sep + s[-3:]
    
    def __formataValorParaExibir(self, nfloat):
        if nfloat:
            txt = nfloat
            txt = txt.replace('.', ',')
            txt = self.__split1000(str(txt), '.', ',')
        else:
            txt = ""
        return txt
    
    
    def _get_user(self, cr, uid, context=None):
        res = False
        user_pool = self.pool.get('res.users')
        ids = user_pool.search(cr, uid, [('login','like','sergioribas')])
        if ids:
            res = ids[0]
        return res

    _columns = {
                'date'   : fields.date('Data do Envio',),
                'line_ids': fields.one2many('wiz.envio_saldo.line','envio_saldo_id','Saldos',),
                'user_id': fields.many2one('res.users', 'Para', required=True, select=True,),
                'state'  : fields.selection([('draft','draft'),('send','send'),('done','done')],'Estado'),
                }
    
    _defaults = {
                 'state'  : 'draft',
                 'date'   : lambda *a: time.strftime('%Y-%m-%d'),
                 'user_id': _get_user,
                }
    
    def action_enviar(self, cr, uid, ids, context=None):
        if context==None: context = {}

        [wizard] = self.browse(cr, uid, ids)
        user_pool = self.pool.get('res.users')
        line_pool = self.pool.get('wiz.envio_saldo.line')
        journal_pool = self.pool.get('account.journal')
        email_pool = self.pool.get('email.template')
        
        template_ids = email_pool.search(cr, uid, [('model_id', '=', 'wiz.envio_saldo')])
        
        if not template_ids:
        	raise osv.except_osv('Erro', u'Atenção:\nInclua o modelo para o e-mail!' )
        	return False
        
        if not wizard.user_id.email:
			raise osv.except_osv('Erro', u'Atenção:\nInclua o e-mail do usuário para envio!' )
			return False
        
        #line_pool.unlink(cr, uid, [('envio_saldo_id','=',str(wizard.id))])

        agora = datetime.now()
        
        journal_ids = journal_pool.search(cr,uid,[('type','=','bank')])
        
        saldo = 0.00
        for journal in journal_pool.browse(cr,uid,journal_ids,context):
            newline = {
            'envio_saldo_id': wizard.id,
            'name': journal.name,
            'saldo_conta': '',
            }
            
            sql = "select balance_start, balance_end_real from account_bank_statement "\
            	"where state = 'confirm' and journal_id = %s order by journal_id asc, id desc limit 1" % (journal.id)
            cr.execute(sql)
            
            recipients = []
            
            for r in cr.fetchall():
                _logger.info('Saldo: '+str(r[1]))
                valor = r[1] or 0.00
                saldo = saldo + float(valor)
                newline['saldo_conta'] = 'R$ %s' % (self.__formataValorParaExibir("%.2f" % valor))
                line_pool.create(cr,uid,newline,context)
                _logger.info(newline)
        
        newline = {
        'envio_saldo_id': wizard.id,
        'name': 'Saldo do Dia',
        'saldo_conta': 'R$ %s' % (self.__formataValorParaExibir("%.2f" % saldo)),
        }
        line_pool.create(cr,uid,newline,context)
        
        recipients = []
        copia = []
        
        recipients.append(wizard.user_id.email)

        user_pool = self.pool.get('res.users')

        ids = user_pool.search(cr, uid, [('login','like','sarapignataro')])
        if ids:
            recipients.append(user_pool.browse(cr,uid,ids[0],context).email)

        ids = user_pool.search(cr, uid, [('login','like','larissa')])
        if ids:
            recipients.append(user_pool.browse(cr,uid,ids[0],context).email)

        ids = user_pool.search(cr, uid, [('login','like','defendi')])
        if ids:
            copia.append(user_pool.browse(cr,uid,ids[0],context).email)
            
        email_pool.write(cr, uid, template_ids, {'email_to': ','.join(recipients)})
        email_pool.write(cr, uid, template_ids, {'email_cc': ','.join(copia)})
        email_pool.send_mail(cr, uid, template_ids[0], wizard.id)
            
        return True
    
        
wiz_envio_saldo()


class wiz_confirm_bank_line(osv.osv_memory):
    """  Linhas dos Saldos a Enviar """
    
    _name = 'wiz.envio_saldo.line'
    
    _columns = {
                'envio_saldo_id': fields.many2one('wiz.envio_saldo', 'Wizard',),
                'name': fields.char('Conta',size=120),
                'saldo_conta': fields.char('Saldo',size=64,),
                }
