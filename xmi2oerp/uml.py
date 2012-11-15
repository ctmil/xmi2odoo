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
"""
 = Classes to describe UML entities in relational database.

>>> from sqlalchemy import create_engine
>>> engine = create_engine('sqlite:///:memory:')
>>> Base.metadata.create_all(engine)
>>> from sqlalchemy.orm import sessionmaker
>>> Session = sessionmaker(bind=engine)
>>> session = Session()
>>> type_integer = CType('int', 'Integer')
>>> session.add(type_integer)
>>> type_string = CType('str', 'String')
>>> session.add(type_string)
>>> attrib_a = CAttribute('a', 'A', type_integer)
>>> session.add(attrib_a)
>>> attrib_b = CAttribute('b', 'B', type_string, 20)
>>> session.add(attrib_b)
>>> session.commit()
>>> for instance in session.query(CType).order_by(CType.id):
...    print instance.id, instance.name, instance.attributes
int Integer [<CAttribute(id:'a', name:'A', size=None)>]
str String [<CAttribute(id:'b', name:'B', size=20)>]
>>> for instance in session.query(CAttribute).order_by(CAttribute.id):
...    print instance.id, instance.name, instance.ctype.id
a A int
b B str

>>> function_a = CFunction('a', 'A')
>>> function_a.parameters = [ CParameter('return', 'return', type_integer, 'return') ]
>>> session.add(function_a)
>>> session.commit()
>>> for instance in session.query(CFunction).order_by(CFunction.id):
...    print instance.id, instance.name, instance.parameters
a A [<CParameter(id:'return', name:'return', kind='return')>]


"""

from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CType(Base):
    """
    = CType class
    """
    __tablename__ = 'ctype'

    id = Column(String, primary_key=True)
    name = Column(String)

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<CType(id:'%s', name:'%s')>" % (self.id, self.name)

class CPackage(Base):
    """
    = Package class
    """
    __tablename__ = 'cpackage'

    id = Column(String, primary_key=True)
    name = Column(String)

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<CPackage(id:'%s', name:'%s')>" % (self.id, self.name)

class CClass(Base):
    """
    = Class class
    """
    __tablename__ = 'cclass'

    id = Column(String, primary_key=True)
    name = Column(String)
    cpackage_id = Column(String, ForeignKey('cpackage.id'))

    cpackage = relationship('CPackage', backref=backref('classes', order_by=id))

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<CClass(id:'%s', name:'%s')>" % (self.id, self.name)

class CAttribute(Base):
    """
    = Attribute class
    """
    __tablename__ = 'cattribute'

    id = Column(String, primary_key=True)
    name = Column(String)
    ctype_id = Column(String, ForeignKey('ctype.id'))
    cclass_id = Column(String, ForeignKey('cclass.id'))
    size = Column(Integer)

    ctype = relationship('CType', backref=backref('attributes', order_by=id))
    cclass = relationship('CClass', backref=backref('attributes', order_by=id))

    def __init__(self, id, name, ctype, size=None):
        self.id = id
        self.name = name
        self.ctype = ctype
        self.size = size

    def __repr__(self):
        return "<CAttribute(id:'%s', name:'%s', size=%s)>" % (self.id, self.name, self.size)

class CParameter(Base):
    """
    = Function parameter class
    """
    __tablename__ = 'cparameter'

    id = Column(String, primary_key=True)
    name = Column(String)
    ctype_id = Column(String, ForeignKey('ctype.id'))
    cfunction_id = Column(String, ForeignKey('cfunction.id'))
    order = Column(Integer)
    kind = Column(String)

    ctype = relationship('CType', backref=backref('parameters', order_by=id))
    cfunction = relationship('CFunction', backref=backref('functions', order_by=id))

    def __init__(self, id, name, ctype, kind):
        self.id = id
        self.name = name
        self.ctype = ctype
        self.kind = kind

    def __repr__(self):
        return "<CParameter(id:'%s', name:'%s', kind='%s')>" % (self.id, self.name, self.kind)

class CFunction(Base):
    """
    = Function class
    """
    __tablename__ = 'cfunction'

    id = Column(String, primary_key=True)
    name = Column(String)
    cclass_id = Column(String, ForeignKey('cclass.id'))

    cclass = relationship('CClass', backref=backref('functions', order_by=id))

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<CFunction(id:'%s', name:'%s')>" % (self.id, self.name)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
