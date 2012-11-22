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
"""Classes to describe UML entities in relational database.

.. moduleauthor: Cristian S. Rocha

Create the database session to test UML entities.

>>> from sqlalchemy import create_engine
>>> engine = create_engine('sqlite:///:memory:')
>>> Base.metadata.create_all(engine)
>>> from sqlalchemy.orm import sessionmaker
>>> Session = sessionmaker(bind=engine)
>>> session = Session()

Generate two main datatypes, Integer and String.

>>> type_integer = CDataType('int', 'Integer')
>>> session.add(type_integer)
>>> type_string = CDataType('str', 'String')
>>> session.add(type_string)

Create the main package

>>> package = CPackage('P', 'Test')
>>> session.add(package)

Append a class with two attributes to the package

>>> theclass = CClass('C', 'TestClass', package)
>>> session.add(theclass)
>>> attrib_a = CAttribute('a', 'A', type_integer, member_of=theclass)
>>> session.add(attrib_a)
>>> attrib_b = CAttribute('b', 'B', type_string, member_of=theclass, size=20)
>>> session.add(attrib_b)
>>> session.commit()

Check stored attributes.

>>> for instance in session.query(CAttribute).order_by(CAttribute.id):
...    print instance.xmi_id, instance.name, instance.datatype.xmi_id, instance.member_of.xmi_id
a A int C
b B str C

Check stored datatypes with related attributes.

>>> for instance in session.query(CDataType).order_by(CDataType.id):
...    print instance.xmi_id, instance.name, instance.attributes
int Integer [<CAttribute(xmi_id:'a', name:'A', size=None)>]
str String [<CAttribute(xmi_id:'b', name:'B', size=20)>]

Append an operation with an output to the class.

>>> function_a = COperation('o', 'A')
>>> function_a.parameters = [ CParameter('return', 'return', type_integer, 0, 'return') ]
>>> session.add(function_a)
>>> session.commit()

Other way to append a member to the class

>>> theclass.members.append(function_a)
>>> session.commit()

Check stored operations.

>>> for instance in session.query(COperation).order_by(COperation.id):
...    print instance.xmi_id, instance.name, instance.parameters, instance.member_of.xmi_id
o A [<CParameter(xmi_id:'return', name:'return', kind='return')>] C

Check stored classes.

>>> for instance in session.query(CClass).order_by(CClass.id):
...    print instance.xmi_id, instance.name, instance.members
C TestClass [<CAttribute(xmi_id:'a', name:'A', size=None)>, <CAttribute(xmi_id:'b', name:'B', size=20)>, <COperation(xmi_id:'o', name:'A')>]
"""

from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import PickleType
from sqlalchemy import Sequence

Base = declarative_base()

class CEntity(Base):
    """Abstract UML entity class.

    :param xmi_id: XMI identity of the entity.
    :param name: Entity name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'umlentity'

    id = Column(Integer, Sequence('entity_id_seq'), primary_key=True)
    xmi_id = Column(String, unique=True)
    name = Column(String)
    umlentity= Column('type', String(50))

    __mapper_args__ = {'polymorphic_on': umlentity}

    def __init__(self, xmi_id, name):
        super(CEntity, self).__init__()
        self.xmi_id = xmi_id
        self.name = name

    def __repr__(self):
        return "<CEntity(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CDataType(CEntity):
    """CDataType class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cdatatype'
    __mapper_args__ = {'polymorphic_identity': 'cdatatype'}

    id = Column(Integer, ForeignKey('umlentity.id'), primary_key=True)

    def __repr__(self):
        return "<CDataType(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CEnumeration(CDataType):
    """CEnumeration class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :param items: List of enumerable items.
    :type xmi_id: str
    :type name: str
    :type items: list
    """

    __tablename__ = 'cenumeration'
    __mapper_args__ = {'polymorphic_identity': 'cenumeration'}

    id = Column(Integer, ForeignKey('cdatatype.id'), primary_key=True)
    items = Column(PickleType)

    def __init__(self, xmi_id, name, items=[]):
        super(CEnumeration, self).__init__(xmi_id, name) 
        self.items = items

    def __repr__(self):
        return "<CEnumeration(xmi_id:'%s', name:'%s', items:%s)>" % (self.id, self.name, self.items)

class CPackage(CEntity):
    """Package class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cpackage'
    __mapper_args__ = {'polymorphic_identity': 'cpackage'}

    id = Column(Integer, ForeignKey('umlentity.id'), primary_key=True)

    def __repr__(self):
        return "<CPackage(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CClass(CEntity):
    """Class class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :param package: CPackage owner of the class.
    :type xmi_id: str
    :type name: str
    :type package: None or CPackage
    """

    __tablename__ = 'cclass'
    __mapper_args__ = {'polymorphic_identity': 'cclass'}

    id = Column(Integer, ForeignKey('umlentity.id'), primary_key=True)
    package_id = Column(Integer, ForeignKey('cpackage.id'))

    package = relationship('CPackage',
                            primaryjoin=(package_id==CPackage.id),
                            backref=backref('classes', order_by=id))

    def __init__(self, xmi_id, name, package=None):
        super(CClass, self).__init__(xmi_id, name) 
        self.package = package

    def __repr__(self):
        return "<CClass(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CMember(CEntity):
    """Member of a class class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :param member_of: CClass instance.
    :type xmi_id: str
    :type name: str
    :type member_of: None or CClass
    """

    __tablename__ = 'cmember'
    __mapper_args__ = {'polymorphic_identity': 'cmember'}

    id = Column(Integer, ForeignKey('umlentity.id'), primary_key=True)
    member_of_id = Column(Integer, ForeignKey('cclass.id'))

    member_of = relationship('CClass',
                             primaryjoin=(member_of_id==CClass.id),
                             backref=backref('members', order_by=id))

    def __init__(self, xmi_id, name, member_of=None):
        super(CMember, self).__init__(xmi_id, name) 
        self.member_of = member_of

    def __repr__(self):
        return "<CMember(xmi_id:'%s', name:'%s', member_of: '%s')>" % (self.xmi_id, self.name, self.member_of.name)

class CAttribute(CMember):
    """Attribute class.

    :param xmi_id: XMI identity of the data type.
    :param name: Atribute name.
    :param datatype: Data type of this attribute.
    :param member_of: Class owner of this attribute.
    :param size: Size of the data type if necessary (Char, List, etc.).
    :type xmi_id: str
    :type name: str
    :type datatype: CDataType
    :type member_of: None or CClass
    :type size: None or int
    """

    __tablename__ = 'cattribute'
    __mapper_args__ = {'polymorphic_identity': 'cattribute'}

    id = Column(Integer, ForeignKey('cmember.id'), primary_key=True)
    datatype_id = Column(Integer, ForeignKey('cdatatype.id'))
    size = Column(Integer)

    datatype = relationship('CDataType',
                             backref=backref('attributes', order_by=id))

    def __init__(self, xmi_id, name, datatype, member_of=None, size=None):
        super(CAttribute, self).__init__(xmi_id, name, member_of) 
        self.datatype = datatype
        self.size = size

    def __repr__(self):
        return "<CAttribute(xmi_id:'%s', name:'%s', size=%s)>" % (self.xmi_id, self.name, self.size)

class COperation(CMember):
    """Operation class.

    :param xmi_id: XMI identity of the data type.
    :param name: Atribute name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'coperation'
    __mapper_args__ = {'polymorphic_identity': 'coperation'}

    id = Column(Integer, ForeignKey('cmember.id'), primary_key=True)

    def __repr__(self):
        return "<COperation(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CParameter(CEntity):
    """Operation parameter class

    :param xmi_id: XMI identity of the data type.
    :param name: Atribute name.
    :param datatype: Datatype of this parameter.
    :param order: Order of this parameter.
    :param kind: Define if this parameter if an input or output parameter.
    :param operation: Operation owner of this parameter.
    :type xmi_id: str
    :type name: str
    :type datatype: CDatatype
    :type order: int
    :type kind: [ 'input', 'return' ]
    :type operation: COperation
    """
    
    __tablename__ = 'cparameter'
    __mapper_args__ = {'polymorphic_identity': 'cparameter'}

    id = Column(Integer, ForeignKey('umlentity.id'), primary_key=True)
    datatype_id = Column(Integer, ForeignKey('cdatatype.id'))
    operation_id = Column(Integer, ForeignKey('coperation.id'))
    order = Column(Integer)
    kind = Column(String)

    datatype = relationship('CDataType',
                             primaryjoin=(datatype_id==CDataType.id),
                             backref=backref('parameters', order_by=id))
    operation = relationship('COperation',
                              primaryjoin=(operation_id==COperation.id),
                              backref=backref('operations', order_by=id))

    def __init__(self, xmi_id, name, datatype, order, kind, operation=None):
        super(CParameter, self).__init__(xmi_id, name) 
        self.operation = operation
        self.datatype = datatype
        self.order = order
        self.kind = kind

    def __repr__(self):
        return "<CParameter(xmi_id:'%s', name:'%s', kind='%s')>" % (self.xmi_id, self.name, self.kind)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
