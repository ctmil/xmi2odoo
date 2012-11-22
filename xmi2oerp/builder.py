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

from xmi2oerp import uml
from xmi2oerp.model import Model

class Builder:
    """Builder engine for addons.

    >>> model = Model("xmi2oerp/test/data/test_002.xmi")
    >>> builder = Builder('/tmp/addons', model)
    """

    def __init__(self, path, parser):
        self.path = path
        self.parser = parser

    def build(self):
        # Por cada paquete generar un directorio de addon.
        # Copio la estructura basica al nuevo directorio.
        # Por cada clase genero un archivo. El archivo lo agrego a la lista de importacion.
        # Proceso el template basico sobre los archivos copiados.
        pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

