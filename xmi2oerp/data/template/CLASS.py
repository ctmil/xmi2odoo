# -*- coding: utf-8 -*-
${LICENSE_HEADER}

from osv import osv, fields

class ${CLASS_NAME}(osv.osv):
    """
    ${CLASS_DOCUMENTATION}\
    """
    _name = '${CLASS_MODULE}.${CLASS_NAME}'
{%  if CLASS_PARENT_NAME is not None %}\
    _inherit = '${CLASS_PARENT_MODULE}.${CLASS_PARENT_NAME}'
{%  end %}\

    _columns = {
{%  for col in CLASS_ATTRIBUTES %}\
{%      def label %}${col.tag.get('label', col.name)}{%end%}\
{%      choose col.datatype.name %}\
        \
{%          when 'Boolean'   %}'${col.name}': fields.boolean('${label()}'), {% end %}\
{%          when 'Integer'   %}'${col.name}': fields.integer('${label()}'), {% end %}\
{%          when 'Float'     %}'${col.name}': fields.float('${label()}'{% if 'digits' in col.tag %}, digits=${col.tag['digits']}{% end %}), {% end %}\
{%          when 'Char'      %}'${col.name}': fields.char('${label()}'{% if 'size' in col.tag %}, size=${col.tag['size']}{% end %}), {% end %}\
{%          when 'Text'      %}'${col.name}': fields.text('${label()}'), {% end %}\
{%          when 'Date'      %}'${col.name}': fields.date('${label()}'), {% end %}\
{%          when 'Datetime'  %}'${col.name}': fields.datetime('${label()}'), {% end %}\
{%          when 'Binary'    %}'${col.name}': fields.binary('${label()}'), {% end %}\
{%          when 'HTML'      %}'${col.name}': fields.html('${label()}'), {% end %}\
{%          otherwise        %}'${col.name}': \
{%            choose type(col.datatype).__tablename__ %}\
{%            when 'cenumeration' %}fields.selection(${repr([(i.name, i.tag.get('label',i.name)) for i in col.datatype.literals])}, '${label()}'), {% end %}\
{%            when 'cclass' %}fields.one2many('${col.datatype.package.name}.${col.datatype.name}', '${label()}'), {% end %}\
{%            end %}\
{%          end %}\
{%      end %}
{%  end %}\
{%  for ass in CLASS_ASSOCIATIONS %}\
{%      def name %}${ass.name}{%end%}\
{%      def label %}${ass.tag.get('label', ass.name)}{%end%}\
{%      def actual_id %}${"%s_id" % CLASS_NAME}{%end%}\
{%      def other_id %}${"%s_id" % ass.participant.name.replace('.','_')}{%end%}\
{%      def other_module %}${ass.participant.package.name}{%end%}\
{%      def other_obj %}${ass.participant.name}{%end%}\
{%      def other_name %}${ass.swap[0].name}{%end%}\
{%      def relational_obj %}${'%s_%s_rel' % (MODULE_NAME, '_'.join([ e.name or '_' for e in ass.association.ends]))}{%end%}\
{%      choose ass.multiplicity %}\
        \
{%          when 'one2one'   %}'${name()}': fields.many2one('${other_module()}.${other_obj()}', '${label()}'), {% end %}\
{%          when 'many2one'  %}'${name()}': fields.many2one('${other_module()}.${other_obj()}', '${label()}'), {% end %}\
{%          when 'one2many'  %}'${name()}': fields.one2many('${other_module()}.${other_obj()}', '${other_name()}', '${label()}'), {% end %}\
{%          when 'many2many' %}'${name()}': fields.many2many('${other_module()}.${other_obj()}', '${relational_obj()}', '${name()}', '${other_name()}', '${label()}'), {% end %}\
{%      end %}
{%  end %}\
    }

    _defaults = {
{%  for col in CLASS_ATTRIBUTES %}\
{%      if col.tag.get('default', None) is not None %}\
        '${col.name}': ${col.tag['default']},
{%      end %}\
{%  end %}\
    }

{%  for op in CLASS_OPERATIONS %}\
    def ${op}(self, cr, uid, ids{% for par in op.parameters %}, ${par.name}{% end %}):
        pass
{%      end %}\

${CLASS_NAME}()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
