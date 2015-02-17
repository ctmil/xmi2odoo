#!/usr/bin/env python

from xmi2odoo import uml

def tag_option(obj, name, label=None, default=None, check=True, quote='\'', negate=False, translate=False):
    if isinstance(name, list):
        valid = any(n in obj.tag for n in name)
        label = label or name[0]
        value = valid and ("%s,%s" % quote).join(obj.tag[n] for n in name if name in obj.tag)
    else:
        valid = name in obj.tag
        label = label or name
        value = valid and obj.tag[name]
    pretrans = "_(" if translate else ""
    posttrans = ")" if translate else ""
    if check and (not valid if negate else valid):
        r = "%s=%s%s%s%s%s" % (label, pretrans, quote, obj.tag[name], quote, posttrans)
    else:
        r = default
    return r 

def stereotype_option(obj, name, label=None, default=None, value='True', check=True, negate=False):
    label = label or name
    valid = obj.is_stereotype(name)
    if check and (not valid if negate else valid):
        r = "%s=%s" % (label, value)
    else:
        r = default
    return r

def model(obj, s='.'):
    try:
        return obj.oerp_id(s, False)
    except:
        return obj.oerp_id(s)

def emodel(obj, s='.'):
    return obj.oerp_id(s)

def pmodel(obj, s='.'):
    return obj.oerp_id(s, False, True)

def name(obj, prefix='', suffix='', default=''):
    return "%s%s%s" % (prefix, obj.name if obj.name not in [ None, '' ] else default, suffix)

def names(obj, prefix='', suffix='', default=''):
    return [ name(o, prefix=prefix, suffix=suffix, default=default) for o in obj ]

def attr_options(cls, obj, version=False):
    if version == '8.0':
      return ',\n        '.join([ o for o in [
         tag_option(obj,  'selection', quote=''),
         tag_option(obj,  'model_name'),
         tag_option(obj,  'relation'),
         tag_option(obj,  'comodel_name'),
         tag_option(obj,  'column1'),
         tag_option(obj,  'column2'),
         tag_option(obj,  'inverse_name'),
         tag_option(obj,  'label', label='string'),
         tag_option(obj,  'documentation', label='help', quote='"""'),
         tag_option(obj,  'ondelete', quote=''),
         tag_option(obj,  'track_visibility'),
         tag_option(obj,  'digits'),
         stereotype_option(obj, 'readonly'),
         stereotype_option(obj, 'required', check=not cls.is_extended()),
         tag_option(obj,  'size'),
         tag_option(obj,  'states', quote=''),
         tag_option(obj,  'context', quote=''),
         tag_option(obj,  'domain', quote=''),
         tag_option(obj,  'on_change'),
         tag_option(obj,  ['groups', 'module_groups'], label='groups'),
         stereotype_option(obj, 'change_default'),
         stereotype_option(obj, 'select'),
         stereotype_option(obj, 'store'),
         stereotype_option(obj, 'translatable', label='translate'),
         stereotype_option(obj, 'invisible'),
         stereotype_option(obj, 'relation',value=obj.datatype.oerp_id()),
         stereotype_option(obj, 'method'),
         stereotype_option(obj, 'view_load'),
         stereotype_option(obj, 'group_name',value=cls.tag.get('group',cls.package.tag['label'])),
         tag_option(obj,  'default', quote=''),
         tag_option(obj,  'fnct', label='compute'),
         tag_option(obj,  'fnct_inv', label='inverse'),
         tag_option(obj,  'fnct_search', label='search'),
         tag_option(obj,  'related'),
         tag_option(obj,  'related_to', label='related'),
         tag_option(obj,  'compute'),
         tag_option(obj,  'inverse'),
         tag_option(obj,  'search'),
         tag_option(obj,  'copy', quote=''),
         ] if o is not None ])
    return ','.join([ o for o in [
       tag_option(obj,  'label', label='string'),
       tag_option(obj,  'documentation', label='help', quote='"""'),
       tag_option(obj,  'ondelete', quote=''),
       tag_option(obj,  'digits'),
       stereotype_option(obj, 'readonly'),
       stereotype_option(obj, 'required', check=not cls.is_extended()),
       tag_option(obj,  'size'),
       tag_option(obj,  'states',),
       tag_option(obj,  'context'),
       tag_option(obj,  'domain'),
       tag_option(obj,  'on_change'),
       tag_option(obj,  ['groups', 'module_groups'], label='groups'),
       stereotype_option(obj, 'change_default'),
       stereotype_option(obj, 'select'),
       stereotype_option(obj, 'store'),
       stereotype_option(obj, 'translatable', label='translate'),
       stereotype_option(obj, 'invisible'),
       stereotype_option(obj, 'relation',value=obj.datatype.oerp_id()),
       stereotype_option(obj, 'method'),
       stereotype_option(obj, 'view_load'),
       stereotype_option(obj, 'group_name',value=cls.tag.get('group',cls.package.tag['label'])),
       tag_option(obj,  'fnc_inv'),
       tag_option(obj,  'fnc_search'),
       ] if o is not None ])

def class_id(CLASS):
    return "%s_id" % CLASS.name

def ass_id(obj):
    return obj.participant.oerp_id()

def ass_other_name(cls, obj):
    return "%s_id" % cls.name if obj.swap[0].name in [None, ''] else obj.swap[0].name

def ass_other_id(ass):
    return "%s_id" % ass.participant.name.replace('.','_')

def ass_relational_obj(mod, ass):
    return '%s_%s_rel' % (mod,
                          '_'.join([ e.name or '_'
                                    for e in ass.association.ends]))

def ass_options(cls,obj,version=False):
    if version == '8.0':
      return ',\n        '.join([ o for o in [
        tag_option(obj,  'selection', quote=''),
        tag_option(obj,  'model_name'),
        tag_option(obj,  'relation'),
        tag_option(obj,  'comodel_name'),
        tag_option(obj,  'column1'),
        tag_option(obj,  'column2'),
        tag_option(obj,  'inverse_name'),
        tag_option(obj,  'label', label='string'),
        tag_option(obj,  'documentation', label='help', quote='"""'),
        tag_option(obj,  'ondelete'),
        tag_option(obj,  'track_visibility'),
        tag_option(obj,  'digits'),
        stereotype_option(obj, 'readonly'),
        stereotype_option(obj, 'required', check=(not cls.is_extended())),
        stereotype_option(obj, 'required', check=(not cls.is_extended()) and ((eval(obj.multiplicityrange) or (0,0))[0] > 0), negate=True),
        tag_option(obj,  'size'),
        tag_option(obj,  'states', quote=''),
        tag_option(obj,  'context', quote=''),
        tag_option(obj,  'domain', quote=''),
        tag_option(obj,  'on_change'),
        tag_option(obj,  ['groups', 'module_groups'], label='groups'),
        stereotype_option(obj, 'change_default'),
        stereotype_option(obj, 'select'),
        stereotype_option(obj, 'store'),
        stereotype_option(obj, 'translatable', label='translate'),
        stereotype_option(obj, 'invisible'),
        #stereotype_option(obj, 'relation',value=obj.datatype.oerp_id()),
        stereotype_option(obj, 'method'),
        stereotype_option(obj, 'view_load'),
        stereotype_option(obj, 'group_name',value=cls.tag.get('group',cls.package.tag['label'])),
        tag_option(obj,  'fnc_inv'),
        tag_option(obj,  'fnc_search'),
        tag_option(obj,  'default', quote=''),
        tag_option(obj,  'fnct', label='compute'),
        tag_option(obj,  'fnct_inv', label='inverse'),
        tag_option(obj,  'fnct_search', label='search'),
        tag_option(obj,  'related'),
        tag_option(obj,  'related_to', label='related'),
        tag_option(obj,  'compute'),
        tag_option(obj,  'inverse'),
        tag_option(obj,  'search'),
        tag_option(obj,  'copy', quote=''),
        ] if o is not None ])
    return ','.join([ o for o in [
       tag_option(obj,  'label', label='string', translate=True),
       tag_option(obj,  'documentation', label='help', quote='"""'),
       tag_option(obj,  'ondelete'),
       tag_option(obj,  'digits'),
       stereotype_option(obj, 'readonly'),
       stereotype_option(obj, 'required', check=(not cls.is_extended())),
       stereotype_option(obj, 'required', check=(not cls.is_extended()) and ((eval(obj.multiplicityrange) or (0,0))[0] > 0), negate=True),
       tag_option(obj,  'size'),
       tag_option(obj,  'states',),
       tag_option(obj,  'context',),
       tag_option(obj,  'domain',),
       tag_option(obj,  'on_change'),
       tag_option(obj,  ['groups', 'module_groups'], label='groups'),
       stereotype_option(obj, 'change_default'),
       stereotype_option(obj, 'select'),
       stereotype_option(obj, 'store'),
       stereotype_option(obj, 'translatable', label='translate'),
       stereotype_option(obj, 'invisible'),
       #stereotype_option(obj, 'relation',value=obj.datatype.oerp_id()),
       stereotype_option(obj, 'method'),
       stereotype_option(obj, 'view_load'),
       stereotype_option(obj, 'group_name',value=cls.tag.get('group',cls.package.tag['label'])),
       tag_option(obj,  'fnc_inv'),
       tag_option(obj,  'fnc_search'),
       ] if o is not None ])

def sel_literals(col):
    return repr([(i.name, i.tag.get('label',i.name)) for i in col.datatype.all_literals()]) if col.datatype.not_is_stereotype('function') else "_get_%s" % col.datatype.name

def fnc_name(col):
    return name(col, prefix='property_' if col.is_stereotype('property') else '')

def parameters(op, prefix='', suffix=''):
    parms = [par.name for par in [ p for p in op.parameters if p.name != 'return']]
    if parms:
        return '%s%s%s' % (prefix, ', '.join(parms), suffix)
    else:
        return ''

def view_filter_id(cls):
    return "view_%s_filter" % model(cls, '_')

def view_form_id(cls):
    return "view_%s_form" % model(cls, '_')

def view_tree_id(cls):
    return "view_%s_tree" % model(cls, '_')

def form_colors(cls):
    r = ''
    for sm in [ sm for sm in cls.get_statemachines(no_stereotypes=['extend','prototype'])]:
        r = "grey:state=='cancelled';blue:state in %s;black:state in %s;red:state in %s" % (
            repr(tuple(names(sm.initial_states()))),
            repr(tuple(set(names(sm.middle_states()))-set(names(sm.stereotype_states('exceptional'))))),
            repr(tuple(names(sm.stereotype_states('exceptional'))))
        )
    return r

def tree_sufix(menu):
    return (menu.is_stereotype('hierarchical') and '_hier' or '') + (menu.is_stereotype('editable') and '_edit' or '')

def wkf_name(cls, obj):
    return "%s_%s_wkf" % (cls.name, obj.name)

def wkf_guard(cls, u=' and '):
    if cls.oerp_id('-', False) != cls.oerp_id('-') and cls.has_member('type', uml.CAttribute):
        r = 'type =="%s"%s' % (model(cls), u)
    else:
        r = 'True%s' % u
    return r

def groups(obj):
    return ','.join([ '(4, ref(\'%s\'))' % (name if '.' in name else 'group_%s' % name) for name in obj.tag['groups'].split(',')])

def is_related(obj):
    return obj.relateds(uml.CClass)

def related(obj):
    assert list(obj.relateds(uml.CClass)) > 1, "You have more than one class related to %s.\n%s" % (obj.name, names(obj.relateds(uml.CClass)))
    return obj.relateds(uml.CClass)[0]

def walk_by_associations(CLASS, related_by):
    if related_by:
        relation = CLASS.association_by_name(related_by[0])
        if relation:
            return walk_by_associations(relation.participant, related_by[1:])
        else:
            return None
    return CLASS

def debug(*values):
    import pdb; pdb.set_trace()
    return values


