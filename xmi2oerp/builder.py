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
from xmi2oerp import uml
from xmi2oerp.model import Model
from genshi.template import NewTextTemplate
from datetime import date
from pprint import PrettyPrinter

class Builder:
    """Builder engine for addons.

    >>> model = Model("xmi2oerp/test/data/test_003.xmi")
    >>> import tempfile; tmpdir = tempfile.mkdtemp()
    >>> builder = Builder(tmpdir, model)
    >>> builder.build()
    >>> shutil.rmtree(tmpdir)
    """

    def __init__(self, path, model):
        self.path = path
        self.model = model
        self.variables = None
        self.pp = PrettyPrinter(indent=4)

    def update(self, tags, filename):
        with open(filename) as stmpl:
            tmpl = NewTextTemplate(stmpl.read())
        stream = tmpl.generate(**tags)
        with open(filename, 'w') as out:
            out.write(stream.render())
        pass

    def build(self):
        # Por cada paquete generar un directorio de addon.
        for k in self.model.iterclass(uml.CPackage):
            # Configuro las variables y tags para este paquete
            package = self.model[k]
            ptag = package.tag
            root_classes = [ (c.xmi_id, c.name) for c in package.classes ]
            wizard_classes = [] # [ (c.xmi_id, c.name) for c in package.classes ]
            report_classes = [] # [ (c.xmi_id, c.name) for c in package.classes ]
            tags = {
                'YEAR': str(date.today().year),
                'MODULE_NAME': package.name,
                'MODULE_SHORT_DESCRIPTION': ptag.get('documentation','\n').split('\n')[0],
                'MODULE_DESCRIPTION': ptag.get('documentation', 'No documented'),
                'MODULE_AUTHOR': ptag.get('author', 'No author.'),
                'MODULE_AUTHOR_EMAIL': ptag.get('email','No email'),
                'MODULE_VERSION': ptag.get('version', 'No version'),
                'MODULE_CATEGORY': ptag.get('category', ''),
                'MODULE_WEBSITE': ptag.get('website', ''),
                'MODULE_LICENSE': ptag.get('license', 'AGPL-3'),
                'MODULE_DEPENDS': ptag.get('depends', ''),
                'ROOT_IMPORT': '\n'.join([ "import %s" % n for k, n in root_classes ]),
                'WIZARD_IMPORT': '\n'.join([ "import %s" % n for k, n in wizard_classes ]),
                'REPORT_IMPORT': '\n'.join([ "import %s" % n for k, n in report_classes ]),
            }
            tags.update({
                'LICENSE_HEADER': str(NewTextTemplate(
                    pkg_resources.resource_stream(__name__,
                                                  os.path.join('data',
                                                               'licenses',
                                                               filter(lambda c: c.isalpha() or c.isdigit(), tags['MODULE_LICENSE'].lower())+'-header.txt')
                                                 ).read()).generate(**tags)),
                'MODULE_DICTIONARY': self.pp.pformat({
                    'name': tags['MODULE_SHORT_DESCRIPTION'],
                    'version': tags['MODULE_VERSION'],
                    'author': tags['MODULE_AUTHOR'],
                    'category': tags['MODULE_CATEGORY'],
                    'website': tags['MODULE_WEBSITE'],
                    'license': tags['MODULE_LICENSE'],
                    'description': tags['MODULE_DESCRIPTION'],
                    'depends': [ s.strip() for s in tags['MODULE_DEPENDS'].split(',') if s != '' ],
                    'init_xml': [],
                    'demo_xml': [],
                    'update_xml': [],
                    'test': [],
                    'active': False,
                    'installable': True,
                }),
            })
            # Copio la estructura basica al nuevo directorio.
            source = pkg_resources.resource_filename(__name__, os.path.join('data', 'template'))
            target = os.path.join(self.path, package.name)
            print >> sys.stderr, "Copy template structure from: ", source, "to", target
            shutil.copytree(source, target,
                            ignore=shutil.ignore_patterns('*CLASS.py*', '*CLASS_view.xml*'))

            # Proceso el template basico sobre los archivos copiados.
            for root, dirs, files in os.walk(target):
                for f in files:
                    self.update(tags, os.path.join(root, f))

            # Por cada clase genero un archivo. El archivo lo agrego a la lista de importacion.
            for xmi_id, name in root_classes:
                cclass = self.model[xmi_id]
                if len(self.model[xmi_id].child_of) > 0:
                    parent = self.model[xmi_id].child_of[0].parent
                else:
                    parent = None
                ctag = cclass.tag
                source_code = os.path.join(source, 'CLASS.py')
                target_code = os.path.join(target, '%s.py' % name)
                shutil.copy(source_code, target_code)
                tags.update({
                    'CLASS_NAME': name,
                    'CLASS_PARENT': parent.name if parent is not None else None,
                    'CLASS_PARENT_MODULE': parent.package.name if parent is not None else None,
                    'CLASS_DOCUMENTATION': ctag.get('documentation', ''),
                    'CLASS_ATTRIBUTES': [ m for m in cclass.members if m.entityclass == 'cattribute' ],
                    'CLASS_ASSOCIATIONS': [ m.swap[0] for m in cclass.associations ],
                    })
                self.update(tags, target_code)

        import pdb; pdb.set_trace()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

