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

{%  for op in CLASS_PRIVATE_OPERATIONS %}\
    def ${op.name}(self, cr, uid, ids{% for par in op.parameters %}, ${par.name}{% end %}):
        pass
{%      end %}\

    _columns = {
{%  for col in CLASS_ATTRIBUTES %}\
{%      def name(prefix='', suffix='') %}${prefix}${col.name}${suffix}{%end%}\
{%      def label %}${col.tag.get('label',name('[',']'))}{%end%}\
{%      def digits %}{% if 'digits' in col.tag %}, digits=${col.tag['digits']}{%end%}{%end%}\
{%      def size %}{% if 'digits' in col.tag %}, digits=${col.tag['digits']}{%end%}{%end%}\
{%      def required  %}{% if col.is_stereotype('required')  %}, required=True{%end %}{%end%}\
{%      def readonly  %}{% if col.is_stereotype('readonly')  %}, readonly=True{%end %}{%end%}\
{%      def select    %}{% if col.is_stereotype('select')    %}, select=True{%end   %}{%end%}\
{%      def store     %}{% if col.is_stereotype('store')     %}, store=True{%end    %}{%end%}\
{%      def invisible %}{% if col.is_stereotype('invisible') %}, invisible=True{%end%}{%end%}\
{%      def options   %}${required()}${readonly()}${select()}${store()}${invisible()}{%end%}\
{%      choose col.datatype.name %}\
        \
{%          when 'Boolean'   %}'${name()}': fields.boolean('${label()}'${options()}), {% end %}\
{%          when 'Integer'   %}'${name()}': fields.integer('${label()}'${options()}), {% end %}\
{%          when 'Float'     %}'${name()}': fields.float('${label()}'${digits()}${options()}), {% end %}\
{%          when 'Char'      %}'${name()}': fields.char('${label()}'${size()}${options()}), {% end %}\
{%          when 'Text'      %}'${name()}': fields.text('${label()}'${options()}), {% end %}\
{%          when 'Date'      %}'${name()}': fields.date('${label()}'${options()}), {% end %}\
{%          when 'Datetime'  %}'${name()}': fields.datetime('${label()}'${options()}), {% end %}\
{%          when 'Binary'    %}'${name()}': fields.binary('${label()}'${options()}), {% end %}\
{%          when 'HTML'      %}'${name()}': fields.html('${label()}'${options()}), {% end %}\
{%          otherwise        %}'${name()}': \
{%            choose col.datatype.entityclass %}\
{%            when 'cenumeration' %}fields.selection(${repr([(i.name, i.tag.get('label',i.name)) for i in col.datatype.all_literals()])}, '${label()}'${options()}), {% end %}\
{%            when 'cclass' %}fields.many2one('${col.datatype.package.name}.${col.datatype.name}', '${label()}'${options()}), {% end %}\
{%            end %}\
{%          end %}\
{%      end %}
{%  end %}\
{%  if CLASS_STATES is not None %}\
        'state': fields.selection(${repr(CLASS_STATES)}, 'State'),
{%  end %}\
{%  for ass in CLASS_ASSOCIATIONS %}\
{%      def actual_id %}${"%s_id" % CLASS_NAME}{%end%}\
{%      def other_id %}${"%s_id" % ass.participant.name.replace('.','_')}{%end%}\
{%      def name(prefix='', suffix='') %}${prefix}${ass.name if ass.name not in [ None, ''] else other_id() }${suffix}{%end%}\
{%      def label %}${ass.tag.get('label', name('[',']'))}{%end%}\
{%      def other_module %}${ass.participant.package.name}{%end%}\
{%      def other_obj %}${ass.participant.name}{%end%}\
{%      def other_name %}${actual_id() if ass.swap[0].name in [None, ''] else ass.swap[0].name}{%end%}\
{%      def relational_obj %}${'%s_%s_rel' % (MODULE_NAME, '_'.join([ e.name or '_' for e in ass.association.ends]))}{%end%}\
{%      def ondelete  %}{% if 'ondelete' in ass.tag %}, ondelete='${col.tag["ondelete"]}'{%end%}{%end%}\
{%      def composite %}{% if ass.aggregation == 'composite' %}, ondelete='cascade'{%end%}{%end%}\
{%      def required  %}{% if ass.is_stereotype('required')  %}, required=True{%end %}{%end%}\
{%      def readonly  %}{% if ass.is_stereotype('readonly')  %}, readonly=True{%end %}{%end%}\
{%      def select    %}{% if ass.is_stereotype('select')    %}, select=True{%end   %}{%end%}\
{%      def store     %}{% if ass.is_stereotype('store')     %}, store=True{%end    %}{%end%}\
{%      def invisible %}{% if ass.is_stereotype('invisible') %}, invisible=True{%end%}{%end%}\
{%      def options   %}${composite()}${required()}${readonly()}${select()}${store()}${invisible()}{%end%}\
{%      choose ass.multiplicity %}\
        \
{%          when 'one2one'   %}'${name()}': fields.many2one('${other_module()}.${other_obj()}', '${label()}'${options()}), {% end %}\
{%          when 'many2one'  %}'${name()}': fields.many2one('${other_module()}.${other_obj()}', '${label()}'${options()}), {% end %}\
{%          when 'one2many'  %}'${name()}': fields.one2many('${other_module()}.${other_obj()}', '${other_name()}', '${label()}'${options()}), {% end %}\
{%          when 'many2many' %}'${name()}': fields.many2many('${other_module()}.${other_obj()}', '${relational_obj()}', '${name()}', '${other_name()}', '${label()}'${options()}), {% end %}\
{%          when 'related'   %}'${name()}': fields.related(
                    ${"'%s'" % "','".join(ass.tag['related_by'].split(','))},
                    ${"'%s'" % ass.tag['related_to']},
                    type='${ass.participant.member_by_name("type").datatype.oerp_type}',
                    relation='${other_module()}.${other_obj()}',
                    string='${label()}'${options()}
                    ),{% end %}\
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

{%  for op in CLASS_PUBLIC_OPERATIONS %}\
    def ${op.name}(self, cr, uid, ids{% for par in op.parameters %}, ${par.name}{% end %}):
        pass
{%      end %}\

${CLASS_NAME}()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
