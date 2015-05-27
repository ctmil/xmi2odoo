#!/usr/bin/env python
##############################################################################
#
#    XMI2OERP, XMI convesort to OpenERP module
#    Copyright (C) 2012 Coop Trab Moldeo Interactive, Grupo AdHoc S.A.
#    (<http://www.moldeointeractive.com.ar>; <www.grupoadhoc.com.ar>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import pkg_resources, os, sys, shutil
from xmi2odoo import uml
from xmi2odoo.model import Model
from datetime import date
from pprint import PrettyPrinter
import logging
from xml.sax.saxutils import escape as xmlescape
from mako.template import Template
from mako.exceptions import RichTraceback

import itertools

def escape(s, entities={}):
    if isinstance(s, unicode):
        s = s.encode('ascii', 'xmlcharrefreplace')
    s = xmlescape(s, entities)
    return s

def names(items):
    return [ i.name.encode('ascii', 'ignore') for i in items ]

def stereotype_dict(items, attribute, dictmap, default=None, prefix=None, suffix=None):
    prefix = prefix or ''
    suffix = suffix or ''
    stereotypes = set(dictmap.keys())
    r = {}
    for i in items:
        k = '%s%s%s' % (prefix, getattr(i, attribute).encode('ascii', 'ignore'), suffix)
        active_stereotypes = stereotypes & set(names(i.stereotypes))
        if len(active_stereotypes) > 0:
            r[k] = dictmap[active_stereotypes.pop()]
        elif default is not None:
            r[k] = default
    return r

class Builder:
    """Builder engine for addons.

    Build code for version api 7.0.

    >>> model = Model("xmi2odoo/test/data/test_003.xmi")
    >>> import tempfile; tmpdir = tempfile.mkdtemp()
    >>> builder = Builder(tmpdir, model)
    >>> builder.build('7.0')
    >>> shutil.rmtree(tmpdir)

    Build code for version api 8.0.

    >>> model = Model("xmi2odoo/test/data/test_003.xmi")
    >>> import tempfile; tmpdir = tempfile.mkdtemp()
    >>> builder = Builder(tmpdir, model)
    >>> builder.build('8.0')
    >>> shutil.rmtree(tmpdir)
    """

    def __init__(self, path, model):
        self.path = path
        self.model = model
        self.variables = None
        self.pp = PrettyPrinter(indent=4)
        self.t = 0

    def update(self, tags, filename):
        if filename[0] == "." or filename[-4:] == ".swp":
           return
        logging.info('Updating %s' % filename)
        try:
            tmpl = Template(filename=filename, module_directory='/tmp/mako_modules')
            with open(filename, 'w') as out:
                s = tmpl.render(**tags)
                out.write(s.encode('utf-8'))
        except UnicodeEncodeError, e:
            print "Error in file %s.\nMessage: %s" % (filename, e)
            raise
        except:
            traceback = RichTraceback()
            m = ""
            for (filename, lineno, function, line) in traceback.traceback:
                m += "File %s, line %s, in %s\n" % (filename, lineno, function)
                m += line + "\n"
            m += "%s: %s\n" % (str(traceback.error.__class__.__name__), traceback.error)
            raise RuntimeError(m)

    def reset(self):
        """
        Remove target directories. Do not remove root directory.
        """
        for k in self.model.iterclass(uml.CPackage):
            package = self.model[k]
            if package.is_stereotype('external'):
                continue
            target = os.path.join(self.path, package.name)
            if os.path.exists(target): shutil.rmtree(target)

    def sort_menues(self, menues):
        if len(menues)==0:
            return []
        sorted_items = []
        take_first = 0

        while len(sorted_items) != len(menues):
            # Solve group of menues taking one and iterating to the leafs.
            r = []

            items = [ m for m in menues[take_first].prev_leafs(uml.CUseCase, uml.CUseCase) ]

            while items:
                repeated_menues = (set([ i.xmi_id for i in items ]) & set([ ri.xmi_id for ri in r ]))
                if repeated_menues != set():
                    raise RuntimeError, 'Loop in menues. Repeat for %s.' \
                            'Check if they have undirected association ' \
                            'or exists a loop in directed associations.' \
                            % [ i.name for i in items if i.xmi_id in repeated_menues ]
                r.extend( m for m in items if m.package.xmi_id == menues[take_first].package.xmi_id )
                items = sorted(set(itertools.chain(*[ i.nexts(uml.CUseCase) for i in items ])), key=lambda a: a.name)

            sorted_items += r

            # If exists other groups of menues, prepare them to solve.
            menues_xmi_id = set([ i.xmi_id for i in menues ])
            items_xmi_id = set([ ri.xmi_id for ri in r ])
            problematic_menues_xmi_id = menues_xmi_id - items_xmi_id

            if problematic_menues_xmi_id:
                take_first = menues.index([ i for i in menues if i.xmi_id in problematic_menues_xmi_id ][0])

        return sorted_items

    def sort_by_gen(self, entities):
        tree = {}
        obj = {}
        for ent in entities:
            obj[ent.oerp_id()] = ent
            tree[ent.oerp_id()] = (ent.parents(), ent.childs())
        roots = [ obj[k] for k in tree.keys() if len(tree[k][0]) == 0 ]

        # Sorting algorithm
        def sorttree(root, tree):
            root_name = root.oerp_id()
            if root in tree[root_name][0]:
                logging.warning('Preventing infinite recursion for %s.' % root_name)
                tree[root_name][0].remove(root)
            if root in tree[root_name][1]:
                logging.warning('Preventing infinite recursion for %s.' % root_name)
                tree[root_name][1].remove(root)
            r = [ root ] + reduce(lambda a,b: a+b, [ sorttree(child, tree) for child in tree[root_name][1] ], [])
            return r

        # Build list
        result = reduce(lambda a,b: a+b, [ sorttree(root, tree) for root in roots ], [])
        return result



    def sort_classes(self, classes):
        # Build forest of classes
        tree = {}
        for cls in classes:
            parents = [ gen.parent.name for gen in cls.child_of if gen.parent.package == cls.package ]
            childs  = [ gen.child.name for gen in cls.parent_of if gen.parent.package == cls.package ]
            tree[cls.name] = (parents, childs)

        # Take roots
        roots = [ cls for cls in tree.keys() if len(tree[cls][0]) == 0 ]

        # Sorting algorithm
        def sorttree(root, tree):
            if root not in tree:
                raise Exception, "Class %s could have an non declared external relation. Please check it." % root
            if root in tree[root][0]:
                logging.warning('Preventing infinite recursion for %s.' % root)
                tree[root][0].remove(root)
            if root in tree[root][1]:
                logging.warning('Preventing infinite recursion for %s.' % root)
                tree[root][1].remove(root)
            r = [ root ] + reduce(lambda a,b: a+b, [ sorttree(child, tree) for child in tree[root][1] ], [])
            return r

        # Build list
        result = reduce(lambda a,b: a+b, [ sorttree(root, tree) for root in roots ], [])

        return result

    def copy_template(self, source, target, ignore=[]):
            logging.info("Copy template structure from: %s to %s" % ( source, target) )
            shutil.copytree(source, target, ignore=ignore)

    def build(self, version, logfile=sys.stderr):
        logging.info("Starting Building")
        # Store dependencies to check circular ones.
        dependencies_map = {}
        # Por cada paquete generar un directorio de addon.
        for k in self.model.iterclass(uml.CPackage):
            package = self.model[k]
            # Si el paquete es externo no lo construyo.
            if package.is_stereotype('external'):
                logging.debug("Ignoring external package %s" % package.name)
                continue
            logging.debug("Building package %s" % package.name)
            # Configuro las variables y tags para este paquete
            ptag = package.tag
            root_classes_obj = package.get_entities(uml.CClass, no_stereotypes=["wizard", "report"])
            wizard_classes_obj = package.get_entities(uml.CClass, stereotypes=["wizard"])
            report_classes_obj = package.get_entities(uml.CClass, stereotypes=["report"])
            root_classes = [ (c.xmi_id, c.name) for c in root_classes_obj ]
            wizard_classes = [ (c.xmi_id, c.name) for c in wizard_classes_obj ]
            report_classes = [ (c.xmi_id, c.name) for c in report_classes_obj ]
            #view_files = [ 'view/%s_view.xml' % name for xml_id, name in root_classes ]
            view_files = [ "view/%s_view.xml" % n for n in self.sort_classes(root_classes_obj) ]
            wizard_view_files = [ "wizard/%s_view.xml" % n for n in self.sort_classes(wizard_classes_obj) ]
            wizard_workflow_files = [ 'wizard/%s_workflow.xml' % name for xml_id, name in wizard_classes if len(list(self.model[xml_id].iter_over_inhereted_attrs('statemachines'))[0:1])>0 ]
            menu_files = ['view/%s_menuitem.xml' % package.name,
                          'view/%s_actions.xml' % package.name]
            properties_files = [ "data/%s_properties.xml" % n for n in self.sort_classes(root_classes_obj) ]
            track_files = [ "data/%s_track.xml" % n for n in self.sort_classes(root_classes_obj) ]
            group_files = [ 'security/%s_group.xml' % package.name ]
            workflow_files = [ 'workflow/%s_workflow.xml' % name for xml_id, name in root_classes if len(list(self.model[xml_id].iter_over_inhereted_attrs('statemachines'))[0:1])>0 ]
            app_files = [ '%s_app.xml' % package.name ]
            security_files = [ 'security/ir.model.access.csv' ]
            # Calcula dependencias
            att_depends = [ self.model[a].datatype.package.name for a in self.model.iterclass(uml.CAttribute)
                           if self.model[a].package.xmi_id == package.xmi_id and self.model[a].datatype.package ]
            ass_depends = [ self.model[a].participant.package.name for a in self.model.iterclass(uml.CAssociationEnd)
                           if self.model[a].swap[0].isNavigable
                           and self.model[a].swap[0].participant.package.xmi_id == package.xmi_id
                           and self.model[a].participant.package ]
            gen_depends = [ self.model[a].parent.package.name for a in self.model.iterclass(uml.CGeneralization)
                           if self.model[a].child.package.name == package.name ]
            exp_depends = package.tag.get('depends','').split(',')
            dependencies = set(att_depends + ass_depends + gen_depends + exp_depends) - set(['', 'res', 'ir', package.name])
            dependencies_map[package.name] = dependencies
            # Construyo los tags
            tags = {
                'stereotype_dict': stereotype_dict,
                'names': names,
                'unicode': unicode,
                'escape': escape,
                'quote': lambda s: escape(s, {'"':'&quot;', "'":'&quot;'}),
                'doublequote': lambda s: escape(s, {"'":'"'}),
                'uml': uml,
                'PACKAGE': package,
                'YEAR': str(date.today().year),
                'MODULE_NAME': package.name,
                'MODULE_LABEL': ptag.get('label', package.name),
                'MODULE_SHORT_DESCRIPTION': ptag.get('label','\n').split('\n')[0],
                'MODULE_DESCRIPTION': ptag.get('documentation', 'No documented'),
                'MODULE_AUTHOR': ptag.get('author', 'No author.'),
                'MODULE_AUTHOR_EMAIL': ptag.get('email','No email'),
                'MODULE_VERSION': ptag.get('version', 'No version'),
                'MODULE_CATEGORY': ptag.get('category', 'base.module_category_hidden'),
                'MODULE_WEBSITE': ptag.get('website', ''),
                'MODULE_LICENSE': ptag.get('license', 'AGPL-3'),
                'MODULE_DEPENDS': ptag.get('depends', ''),
                'MENUES': self.sort_menues([ cu for cu in self.model.session.query(uml.CUseCase)
                                            if cu.is_stereotype('menu') and
                                               cu.package and
                                               cu.package.xmi_id == k]),
                'SERVER_ACTIONS': self.sort_menues([ cu for cu in self.model.session.query(uml.CUseCase)
                                            if cu.is_stereotype('server_action') and
                                               cu.package and
                                               cu.package.xmi_id == k]),
                'GROUPS': self.sort_by_gen([ ac for ac in self.model.session.query(uml.CActor)
                                            if ac.is_stereotype('group') and
                                               ac.package and
                                               ac.package.xmi_id == k]),
                'ROOT_IMPORT': '\n'.join([ "import %s" % n
                                          for n in self.sort_classes(root_classes_obj) ]),
                'WIZARD_IMPORT': '\n'.join([ "import %s" % n
                                            for n in self.sort_classes(wizard_classes_obj) ]),
                'REPORT_IMPORT': '\n'.join([ "import %s" % n
                                            for n in self.sort_classes(report_classes_obj) ]),
            }
            if version=='8.0':
                tags.update({
                    'datatype': {
                        'Selection': 'Selection',
                        'Many2many': 'Many2many',
                        'One2many': 'One2many',
                        'Many2one': 'Many2one',
                        'Boolean': 'Boolean',
                        'Integer': 'Integer',
                        'Float':   'Float',
                        'Char':    'Char',
                        'Text':    'Text',
                        'Date':    'Date',
                        'Datetime':'Datetime',
                        'Binary':  'Binary',
                        'HTML':    'Html',
                    },
                })
            else:
                tags.update({
                    'datatype': {
                        'Boolean': 'boolean',
                        'Integer': 'integer',
                        'Float':   'float',
                        'Char':    'char',
                        'Text':    'text',
                        'Date':    'date',
                        'Datetime':'datetime',
                        'Binary':  'binary',
                        'HTML':    'html',
                    },
                })                
            tags.update({
                'uml': uml,
                'LICENSE_HEADER': str(Template(
                    pkg_resources.resource_stream(__name__,
                                                  os.path.join('data',
                                                               'licenses',
                                                               filter(lambda c: c.isalpha() or c.isdigit(), tags['MODULE_LICENSE'].lower())+'-header.txt')
                                                 ).read()).render(**tags)),
                'MODULE_DICTIONARY': self.pp.pformat({
                    'name': tags['MODULE_SHORT_DESCRIPTION'],
                    'version': tags['MODULE_VERSION'],
                    'author': tags['MODULE_AUTHOR'],
                    'category': tags['MODULE_CATEGORY'],
                    'website': tags['MODULE_WEBSITE'],
                    'license': tags['MODULE_LICENSE'],
                    'description': tags['MODULE_DESCRIPTION'],
                    'depends': list(dependencies),
                    'data': group_files + view_files + properties_files + track_files + workflow_files + security_files + wizard_view_files + wizard_workflow_files + menu_files,
                    'test': [],
                    'active': False,
                    'installable': True,
                }),
            })
            # Copio la estructura basica al nuevo directorio.
            source = pkg_resources.resource_filename(__name__, os.path.join('data', 'template', version))
            target = os.path.join(self.path, package.name)
            logging.info("Copy template structure from: %s to %s" % ( source, target) )
            shutil.copytree(source, target,
                            ignore=shutil.ignore_patterns('*CLASS*',
                                                          '*PACKAGE_*'))

            # Rename python files from .py_ to .py.
            for root, dirs, files in os.walk(target):
                for f in files:
                    if f[-4:] == '.py_':
                        # Renombrar este archivo
                        os.rename(os.path.join(root, f), os.path.join(root, f[:-4]+'.py'))

            # Generate menu file
            source_code = os.path.join(source, 'view/PACKAGE_menuitem.xml')
            target_code = os.path.join(target, 'view/%s_menuitem.xml' % package.name)
            shutil.copy(source_code, target_code)
            self.update(tags, target_code)

            # Generate actions file
            source_code = os.path.join(source, 'view/PACKAGE_actions.xml')
            target_code = os.path.join(target, 'view/%s_actions.xml' % package.name)
            shutil.copy(source_code, target_code)
            self.update(tags, target_code)

            # Generate groups file
            source_code = os.path.join(source, 'security/PACKAGE_group.xml')
            target_code = os.path.join(target, 'security/%s_group.xml' % package.name)
            shutil.copy(source_code, target_code)
            self.update(tags, target_code)

            # Proceso el template basico sobre los archivos copiados.
            for root, dirs, files in os.walk(target):
                for f in files:
                    self.update(tags, os.path.join(root, f))

            # Por cada clase genero un archivo. El archivo lo agrego a la lista de importacion.
            for xmi_id, name in root_classes:
                # Prepare data
                cclass = self.model[xmi_id]
                if len(cclass.child_of) > 0:
                    generalization = cclass.child_of[0]
                    parent = generalization.parent
                    extend_parent = generalization.is_extend
                else:
                    parent = None
                    extend_parent = False
                ctag = cclass.tag
                tags.update({
                    'CLASS': cclass,
                    'CLASS_EXTEND_PARENT': extend_parent,
                    'CLASS_LABEL': cclass.tag.get('label', name),
                    'CLASS_MODULE': parent.package.name if extend_parent else cclass.package.name,
                    'CLASS_NAME': parent.name if extend_parent else name,
                    'CLASS_PARENT_MODULE': parent.package.name if parent is not None else None,
                    'CLASS_PARENT_NAME': parent.name if parent is not None else None,
                    'CLASS_DOCUMENTATION': ctag.get('documentation', None),
                    'CLASS_ATTRIBUTES': [ m for m in cclass.members if m.entityclass == 'cattribute' ],
                    'CLASS_ASSOCIATIONS': [ cclass.all_associations(ctype=uml.CClass, parents=False) ],
                    'MENU_PARENT': cclass.tag.get('menu_parent', None) or (
                        [ass.participant.tag['label']
                         for ass in cclass.associations
                         if type(ass.swap[0]) is uml.CUseCase and ass.swap[0].is_stereotype('menu')
                        ]+[None]
                    )[0],
                    'MENU_SEQUENCE': cclass.tag.get('menu_sequence', '100'),
                    'STEREOTYPES': [ s.name for s in cclass.stereotypes ],
                    'tree_types': lambda c: [ '' ] + (any(c.all_associations(ctype=uml.CUseCase, stereotypes=["editable"])) and [ '_edit' ] or []) + (any(c.all_associations(ctype=uml.CUseCase, stereotypes=["hierarchical"])) and [ '_hier' ] or []),
                    })

                # Generate class file
                source_code = os.path.join(source, 'CLASS.py_')
                target_code = os.path.join(target, '%s.py' % name)
                shutil.copy(source_code, target_code)
                self.update(tags, target_code)

                # Generate view file
                source_code = os.path.join(source, 'view/CLASS_view.xml')
                target_code = os.path.join(target, 'view/%s_view.xml' % name)
                shutil.copy(source_code, target_code)
                self.update(tags, target_code)

                # Generate properties file
                source_code = os.path.join(source, 'data/CLASS_properties.xml')
                target_code = os.path.join(target, 'data/%s_properties.xml' % name)
                shutil.copy(source_code, target_code)
                self.update(tags, target_code)

                # Generate track file
                source_code = os.path.join(source, 'data/CLASS_track.xml')
                target_code = os.path.join(target, 'data/%s_track.xml' % name)
                shutil.copy(source_code, target_code)
                self.update(tags, target_code)

                # Generate workflow file
                if len(list(cclass.iter_over_inhereted_attrs('statemachines'))[0:1]) > 0:
                    source_code = os.path.join(source, 'workflow/CLASS_workflow.xml')
                    target_code = os.path.join(target, 'workflow/%s_workflow.xml' % name)
                    shutil.copy(source_code, target_code)
                    self.update(tags, target_code)

            # Por cada wizard genero un archivo. El archivo lo agrego a la lista de importacion.
            for xmi_id, name in wizard_classes:
                # Prepare data
                cclass = self.model[xmi_id]
                if len(cclass.child_of) > 0:
                    generalization = cclass.child_of[0]
                    parent = generalization.parent
                    extend_parent = generalization.is_extend
                else:
                    parent = None
                    extend_parent = False
                ctag = cclass.tag
                tags.update({
                    'CLASS': cclass,
                    'CLASS_EXTEND_PARENT': extend_parent,
                    'CLASS_LABEL': cclass.tag.get('label', name),
                    'CLASS_MODULE': parent.package.name if extend_parent else cclass.package.name,
                    'CLASS_NAME': parent.name if extend_parent else name,
                    'CLASS_PARENT_MODULE': parent.package.name if parent is not None else None,
                    'CLASS_PARENT_NAME': parent.name if parent is not None else None,
                    'CLASS_DOCUMENTATION': ctag.get('documentation', None),
                    'CLASS_ATTRIBUTES': [ m for m in cclass.members if m.entityclass == 'cattribute' ],
                    'CLASS_ASSOCIATIONS': [ cclass.all_associations(ctype=uml.CClass, parents=False) ],
                    'MENU_PARENT': cclass.tag.get('menu_parent', None) or (
                        [ass.participant.tag['label']
                         for ass in cclass.associations
                         if type(ass.swap[0]) is uml.CUseCase and ass.swap[0].is_stereotype('menu')
                        ]+[None]
                    )[0],
                    'MENU_SEQUENCE': cclass.tag.get('menu_sequence', '100'),
                    'STEREOTYPES': [ s.name for s in cclass.stereotypes ],
                    'tree_types': lambda c: [ '' ] + (any(c.all_associations(ctype=uml.CUseCase, stereotypes=["editable"])) and [ '_edit' ] or []) + (any(c.all_associations(ctype=uml.CUseCase, stereotypes=["hierarchical"])) and [ '_hier' ] or []),
                    })

                # Generate class file
                source_code = os.path.join(source, 'wizard', 'CLASS.py_')
                target_code = os.path.join(target, 'wizard', '%s.py' % name)
                shutil.copy(source_code, target_code)
                self.update(tags, target_code)

                # Generate view file
                source_code = os.path.join(source, 'wizard', 'CLASS_view.xml')
                target_code = os.path.join(target, 'wizard', '%s_view.xml' % name)
                shutil.copy(source_code, target_code)
                self.update(tags, target_code)

                # Generate workflow file
                source_code = os.path.join(source, 'wizard', 'CLASS_workflow.xml')
                target_code = os.path.join(target, 'wizard', '%s_workflow.xml' % name)
                shutil.copy(source_code, target_code)
                self.update(tags, target_code)

        for pack in dependencies_map:
            circular = [ pack_b for pack_b in dependencies_map[pack]
                        if pack_b in dependencies_map and pack in dependencies_map[pack_b] ]
            if circular:
                raise RuntimeError, "Simple circular dependies found beetween %s and %s.\n"\
                        "Please check relations direction beetween packages, or create an inhereted class in some package." % (pack, ','.join(circular))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

