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

import xml.etree.ElementTree as ET

class XMIParser:
    def __init__(self):
        pass

    def parse(self, infile):
        """
        Load a XMI file.

        >>> xmiObj = XMIParser()
        >>> xmiObj.parse("xmi2oerp/test/data/test_001.xmi")
        """
        self.et = ET.parse(infile)
        self.root = self.et.getroot()
        for model in self.root.findall('XMI.content/{org.omg.xmi.namespace.UML}Model'):
            for ns in model.findall('{org.omg.xmi.namespace.UML}Namespace.ownedElement'):
                for package in ns.findall('{org.omg.xmi.namespace.UML}Package'):
                    for ns in package.findall('{org.omg.xmi.namespace.UML}Namespace.ownedElement'):
                        for cls in ns.findall('{org.omg.xmi.namespace.UML}Class'):
                            import pdb; pdb.set_trace()
                print i

        pass



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
