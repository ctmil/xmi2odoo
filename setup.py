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

from setuptools import setup

setup(name='xmi2oerp',
      version='1.0',
      description='XMI Conversor to OpenERP modules.',
      author='Cristian S. Rocha',
      author_email='cristian.rocha@moldeointeractive.com.ar',
      url='http://www.moldeointeractive.com.ar/',
      packages=['xmi2oerp'],
      scripts=['xmi2oerp/bin/xmi2oerp'],
      test_suite='xmi2oerp.test',
      install_requires=['Genshi'],
      dependency_links=[]
   )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
