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

>>> package = CPackage('P', 'test')
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
C testclass []

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
C testclass [<CAttribute(xmi_id:'a', name:'A', size=None)>, <CAttribute(xmi_id:'b', name:'B', size=20)>, <COperation(xmi_id:'o', name:'A')>]
"""

from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import PickleType
from sqlalchemy import Sequence
from sqlalchemy.schema import Table
import re
import itertools
import time
import logging

Base = declarative_base()

re_valid_name = re.compile(r'^[0-9a-z_\.]+$')
re_clean_name = re.compile('\W|^(?=\d)')

def is_valid_name(s):
    """Check id a string a valid openerp name."""
    return type(s) is str and re_valid_name.match(s) is not None

def clean_name(s, replace='_'):
    s = 'untitle' if type(s) is not str else s
    return re_clean_name.sub(replace, s).lower()

_oerp_type = {
    'Boolean': 'boolean',
    'Integer': 'integer',
    'Float': 'float',
    'Char': 'char',
    'Text': 'text',
    'Date': 'date',
    'Datetime': 'datetime',
    'Binary': 'binary',
    'HTML': 'html',
}

def solvmul(v, t):
    mr = eval(v)
    if t in ['composite', 'aggregate' ]:
        if mr in [(0,1), (1,1), None]:
            return 'one'
        elif mr in [(0,-1), (1,-1)]:
            return 'many'
    else:
        if mr in [(0,1), (1,1)]:
            return 'one'
        elif mr in [(0,-1), (1,-1), None]:
            return 'many'
    return None

class CEntity(Base):
    """Abstract UML entity class.

    :param xmi_id: XMI identity of the entity.
    :param name: Entity name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'centity'

    id = Column(Integer, Sequence('entity_id_seq'), primary_key=True)
    xmi_id = Column(String, unique=True)
    name = Column(String)
    entityclass = Column('type', String(50))
    default_tagvalues = Column(PickleType)
    package_id = Column(Integer, ForeignKey('cpackage.id', use_alter=True, name='ent_package_id'))
    order = Column(Integer)

    tagvalues = relationship('CTaggedValue',
                             primaryjoin='CTaggedValue.owner_id==CEntity.id',
                             order_by='CTaggedValue.owner_id',
                             backref=backref('owner'))

    package = relationship('CPackage',
                            primaryjoin='CPackage.id==CEntity.package_id',
                            backref=backref('entities', order_by=id),
                            )


    __mapper_args__ = {
        'polymorphic_on': entityclass,
        'polymorphic_identity': 'centity'
    }

    __normalize_name__ = False

    @property
    def tag(self):
        tagvalues = self.default_tagvalues.copy()
        tagvalues.update(dict((i.tagdefinition.name, i.value) for i in self.tagvalues ))
        return tagvalues

    def oerp_id(self, sep='.'):
        if self.package == None:
            package = ''
            sep = ''
        else:
            package = self.package.name
        return '%s%s%s' % (package, sep, self.name)

    def is_stereotype(self, *stereotypes):
        if stereotypes in (tuple(), (None,)): return True
        st = [ st.name in stereotypes for st in self.stereotypes]
        return any(st)

    def not_is_stereotype(self, *stereotypes):
        if stereotypes in (tuple(), (None,)): return True
        st = [ st.name in stereotypes for st in self.stereotypes]
        return not any(st)

    def relateds(self, ctype=None):
        ctype = CEntity if ctype is None else ctype
        return [ ass.swap[0].participant for ass in self.associations if isinstance(ass.swap[0].participant, ctype) ]

    def prevs(self, ctype=None):
        ctype = CEntity if ctype is None else ctype
        return [ ass.swap[0].participant for ass in self.associations if not ass.swap[0].isNavigable and isinstance(ass.swap[0].participant, ctype) ]

    def nexts(self, ctype=None):
        ctype = CEntity if ctype is None else ctype
        return [ ass.swap[0].participant for ass in self.associations if ass.swap[0].isNavigable and isinstance(ass.swap[0].participant, ctype) ]

    def prev_leafs(self, ftype=None, ctype=None, i = 10, no_raise=False, remove_inherits=False):
        ftype = CEntity if ftype is None else ftype
        ctype = CEntity if ctype is None else ctype
        if i <= 0:
            if no_raise:
                return []
            else:
                raise RuntimeError, 'prev_leafs loop cant stop'
        if len(self.prevs(ctype)) > 0:
            r = list(itertools.chain(*[ entity.prev_leafs(ftype, ctype, i=i-1, no_raise=no_raise) for entity in self.prevs(ctype) ]))
            if len(r) > 1 and remove_inherits:
                r = [ p for p, c in itertools.product(r,r) if (p!=c and p.is_child_of(c.oerp_id())) ]
            return r
        elif isinstance(self, ftype):
            return [ self ]
        else:
            return []

    def next_leafs(self, ftype=None, ctype=None, i = 10):
        ftype = CEntity if ftype is None else ftype
        ctype = CEntity if ctype is None else ctype
        if i <= 0:
            raise RuntimeError, 'next_leafs loop cant stop'
        if len(self.prevs(ctype)) > 0:
            return itertools.chain(*[ entity.next_leafs(ftype, ctype, i-1) for entity in self.nexts(ctype) ])
        elif isinstance(self, ftype):
            return [ self ]
        else:
            return []

    def parent(self, package=None, pid=0):
        return self.parents(package=package)[pid]

    def parents(self, package=None, stereotypes=[], no_stereotypes=[], ignore=[]):
        f_package = lambda gen: gen.parent.package == package if package else True
        return [ gen.parent for gen in self.child_of
                if f_package(gen)
                   and gen.is_stereotype(*stereotypes)
                   and gen.not_is_stereotype(*no_stereotypes)
                   and gen.parent.oerp_id() not in ignore ]

    def childs(self, package=None, stereotypes=[], no_stereotypes=[], ignore=[]):
        f_package = lambda gen: gen.parent.package == package if package else True
        return [ gen.child for gen in self.parent_of
                if f_package(gen)
                   and gen.is_stereotype(*stereotypes)
                   and gen.not_is_stereotype(*no_stereotypes)
                   and gen.child.oerp_id() not in ignore ]

    def get_statemachines(self, *args, **dargs):
        return self.statemachines if self.statemachines else itertools.chain(*[ p.get_statemachines(*args, **dargs) for p in self.parents(*args, **dargs) ])

    def is_child_of(self, oerp_id):
        oerp_ids = [ '%s.%s' % (gen.parent.package.name, gen.parent.name) for gen in self.child_of ]
        return (oerp_id in oerp_ids) or max([ gen.parent.is_child_of(oerp_id) for gen in self.child_of ] + [False])

    def __init__(self, xmi_id, name, package=None, order=None, default_tagvalues={}):
        super(CEntity, self).__init__()
        if type(self).__normalize_name__ and name is None:
            logging.warning('Creating %s without name' % xmi_id)
        label = name or u'<no label>'
        if type(self).__normalize_name__ and not is_valid_name(name):
            label = unicode(name)
            name = clean_name(name)
            logging.warning('Invalid name \'%s\'. Converting to \'%s\' and assign the name to label tag' % (label, name))
        default_tagvalues.update({u'label': label.strip() })
        self.xmi_id = xmi_id
        self.name = name
        self.default_tagvalues = default_tagvalues.copy()
        self.package = package
        self.order = order

    def __repr__(self):
        return "<CEntity(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    def has_member(self, name, cclass = None):
        cclass = cclass or CMember
        for mem in self.members:
            if mem.name == name and type(mem) == cclass:
                return True
        for parent in self.parents():
            if parent.has_member(name, cclass):
                return True
        return False

    def get_inhereted_attr(self, attrs):
        r = getattr(self, attrs, None) 
        if r is not None:
            return r
        for parent in self.parents():
            return parent.get_inhereted_attrs(attrs)
        return None

    def iter_over_inhereted_attrs(self, attrs):
        for value in getattr(self, attrs, []):
            yield value
        for parent in self.parents():
            for item in parent.iter_over_inhereted_attrs(attrs):
                yield item

    def __getattr__(self, name):
        if 'is_' == name[:3]:
            return self.is_stereotype(name[3:])
        raise AttributeError

    def __getitem__(self, name):
        tag = self.tag
        if name in tag:
            return tag[name]
        raise KeyError

    def get(self, name, default=None):
        tag = self.tag
        if name in tag:
            return tag[name]
        else:
            return default

    def debug(self, name=None):
        print "D:", self.name
        if name is None or self.name==name:
            import pdb; pdb.set_trace()
        return True

class CUseCase(CEntity):
    """CUseCase class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cusecase'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'cusecase'
    }

    __normalize_name__ = True

    def all_associations(self, stereotypes=[], no_stereotypes=[], parents=True, ctype=None, sort=True):
        if ctype is None: ctype = CClass
        r = list(itertools.chain([ (ass.swap[0], ass.order) for ass in self.associations
                             if type(ass.swap[0].participant) is ctype and (
                                 ( ass.swap[0].is_stereotype(*stereotypes) and ass.swap[0].not_is_stereotype(*no_stereotypes) ) or
                                 ( ass.swap[0].participant.is_stereotype(*stereotypes) and ass.swap[0].participant.not_is_stereotype(*no_stereotypes) )
                             ) ],
                            *[ gen.parent.all_associations(stereotypes, no_stereotypes, parents, ctype, sort=False) for gen in self.child_of if parents]))
        if sort:
            s = sorted(r,key=lambda k: k[1])
            return s and zip(*s)[0] or []
        else:
            return r

    def __repr__(self):
        return "<CUseCase(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CActor(CEntity):
    """CActor class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cactor'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'cactor'
    }

    __normalize_name__ = True

    def __repr__(self):
        return "<CActor(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CDataType(CEntity):
    """CDataType class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cdatatype'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'cdatatype'
    }

    def __repr__(self):
        return "<CDataType(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    @property 
    def oerp_type(self):
        return _oerp_type[self.name]

    def all_attributes(self, stereotypes=[], no_stereotypes=[], parents=True, ctype=None, sort=True):
        if ctype is None: ctype = CAttribute
        r = list(itertools.chain([ (m, m.order) for m in self.members
                             if type(m) is ctype and m.is_stereotype(*stereotypes) and m.not_is_stereotype(*no_stereotypes) ],
                            *[ gen.parent.all_attributes(stereotypes, no_stereotypes, parents, ctype, sort=False) for gen in self.child_of if parents]))
        if sort:
            s = sorted(r,key=lambda k: k[1])
            return s and zip(*s)[0] or []
        else:
            return r

    def all_associations(self, stereotypes=[], no_stereotypes=[], parents=True, ctype=None, sort=True):
        if ctype is None: ctype = CClass
        r = list(itertools.chain([ (ass.swap[0], ass.order) for ass in self.associations
                             if type(ass.swap[0].participant) is ctype and (
                                 ( ass.swap[0].is_stereotype(*stereotypes) and ass.swap[0].not_is_stereotype(*no_stereotypes) ) or
                                 ( ass.swap[0].participant.is_stereotype(*stereotypes) and ass.swap[0].participant.not_is_stereotype(*no_stereotypes) )
                             ) ],
                            *[ gen.parent.all_associations(stereotypes, no_stereotypes, parents, ctype, sort=False) for gen in self.child_of if parents]))
        if sort:
            s = sorted(r,key=lambda k: k[1])
            r = s and zip(*s)[0] or []
        return r

class CEnumerationLiteral(CEntity):
    """CEnumerationLiteral class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cenumerationliteral'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    enumeration_id = Column(Integer, ForeignKey('cenumeration.id'))

    __mapper_args__ = {'polymorphic_identity': 'cenumerationliteral'}

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

    id = Column(Integer, ForeignKey('cdatatype.id'), primary_key=True)

    literals = relationship('CEnumerationLiteral',
                             primaryjoin='CEnumerationLiteral.enumeration_id==CEnumeration.id',
                             order_by='CEnumerationLiteral.enumeration_id',
                             backref=backref('enumeration'))

    __mapper_args__ = {'polymorphic_identity': 'cenumeration'}

    __normalize_name__ = False

    def __init__(self, xmi_id, name, literals=[], order=None, package=None):
        super(CEnumeration, self).__init__(xmi_id, name, order=order, package=package) 
        self.literals = literals

    def __repr__(self):
        return "<CEnumeration(xmi_id:'%s', name:'%s', literals:%s)>" % (self.xmi_id, self.name, [i.name for i in self.literals])

    def all_literals(self):
        """Return literals for this enumeration, from parents to self."""
        for parent in self.child_of:
            for literal in parent.parent.all_literals():
                yield literal
        for literal in self.literals:
            yield literal

    @property 
    def oerp_type(self):
        return 'selection'

class CModel(CEntity):
    """Model class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cmodel'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'cmodel'}

    def __repr__(self):
        return "<CModel(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CPackage(CEntity):
    """Package class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cpackage'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    model_id = Column(Integer, ForeignKey('cmodel.id'))

    __mapper_args__ = {
        'polymorphic_identity': 'cpackage',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = True

    model = relationship('CModel',
                         primaryjoin=(model_id==CModel.id),
                         backref=backref('packages', order_by=id))

    def __init__(self, xmi_id, name, model=None, order=None, package=None):
        super(CPackage, self).__init__(xmi_id, name, order=order, package=package) 
        self.model = model

    def __repr__(self):
        return "<CPackage(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    def get_entities(self, cclass):
        return [ ent for ent in self.entities if type(ent) is cclass ]

class CClass(CDataType):
    """Class class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :param package: CPackage owner of the class.
    :type xmi_id: str
    :type name: str
    :type package: None or CPackage
    """

    __tablename__ = 'cclass'

    id = Column(Integer, ForeignKey('cdatatype.id'), primary_key=True)

    __mapper_args__ = {'polymorphic_identity': 'cclass'}

    __normalize_name__ = True

    def __init__(self, xmi_id, name, order=None, package=None):
        super(CClass, self).__init__(xmi_id, name, order=order, package=package)

    def __repr__(self):
        return "<CClass(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    def member_by_name(self, name):
        """ Return a member by name.  """
        for i in self.members:
            if i.name == name:
                return i
        return None

    def association_by_name(self, name):
        """ Return an association by name. """
        for i in self.associations:
            if i.swap[0].name == name:
                return i.swap[0]

    def is_extended(self, ignore=['ir.needaction_mixin','mail.thread']):
        extensions = [ gen.is_stereotype('extend') for gen in self.child_of if gen.parent.oerp_id() not in ignore ]
        return any(extensions)

    def oerp_id(self, sep='.', check_extend=True, return_parent=False, ignore=['ir.needaction_mixin','mail.thread']):
        child_of = [ gen for gen in self.child_of if gen.parent.oerp_id() not in ignore ]
        if len(child_of) > 0:
            generalization = child_of[0]
            parent = generalization.parent
            extend_parent = generalization.is_stereotype('extend')
            if check_extend and extend_parent:
                return sep.join([parent.package.name, parent.name])
            if return_parent:
                return sep.join([parent.package.name, parent.name])
        return sep.join([self.package.name, self.name])

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

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    member_of_id = Column(Integer, ForeignKey('cclass.id'))

    __mapper_args__ = {'polymorphic_identity': 'cmember'}

    member_of = relationship('CClass',
                             primaryjoin=(member_of_id==CClass.id),
                             backref=backref('members', order_by=id))

    def __init__(self, xmi_id, name, member_of=None, order=None, package=None):
        super(CMember, self).__init__(xmi_id, name, order=order, package=package) 
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

    id = Column(Integer, ForeignKey('cmember.id'), primary_key=True)
    datatype_id = Column(Integer, ForeignKey('cdatatype.id'))
    size = Column(Integer)

    __mapper_args__ = {'polymorphic_identity': 'cattribute'}

    datatype = relationship('CDataType',
                             backref=backref('attributes', order_by=id))

    def __init__(self, xmi_id, name, datatype, member_of=None, size=None, order=None, package=None):
        super(CAttribute, self).__init__(xmi_id, name, member_of=member_of, order=order, package=package) 
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

    id = Column(Integer, ForeignKey('cmember.id'), primary_key=True)

    __mapper_args__ = { 'polymorphic_identity': 'coperation' }

    def __repr__(self):
        return "<COperation(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CParameter(CEntity):
    """Operation parameter class

    :param xmi_id: XMI identity of the data type.
    :param name: Atribute name.
    :param datatype: Datatype of this parameter.
    :param kind: Define if this parameter if an input or output parameter.
    :param operation: Operation owner of this parameter.
    :type xmi_id: str
    :type name: str
    :type datatype: CDatatype
    :type kind: [ 'input', 'return' ]
    :type operation: COperation
    """
    
    __tablename__ = 'cparameter'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    datatype_id = Column(Integer, ForeignKey('cdatatype.id'))
    operation_id = Column(Integer, ForeignKey('coperation.id'))
    kind = Column(String)

    __mapper_args__ = { 'polymorphic_identity': 'cparameter' }

    datatype = relationship('CDataType',
                             primaryjoin=(datatype_id==CDataType.id),
                             backref=backref('parameters', order_by=id))
    operation = relationship('COperation',
                              primaryjoin=(operation_id==COperation.id),
                              backref=backref('parameters', order_by=id))

    def __init__(self, xmi_id, name, datatype, kind, operation=None, order=None, package=None):
        super(CParameter, self).__init__(xmi_id, name, order=order, package=package) 
        self.operation = operation
        self.datatype = datatype
        self.kind = kind

    def __repr__(self):
        return "<CParameter(xmi_id:'%s', name:'%s', kind='%s')>" % (self.xmi_id, self.name, self.kind)

class CTagDefinition(CEntity):
    """Tag definition class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'ctagdefinition'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = { 'polymorphic_identity': 'ctagdefiniton' }

    def __repr__(self):
        return "<CTagDefinition(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CTaggedValue(CEntity):
    """Tag definition class.

    :param xmi_id: XMI identity of the data type.
    :param tagdefinition: Tag definition.
    :param value: Value of the tag.
    :param owner: Owner of this value.
    :type xmi_id: str
    :type tag: CTagDefinition
    :type value: str
    :type owner: CEntity
    """

    __tablename__ = 'ctaggedvalue'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    value = Column(String)
    tagdefinition_id = Column(Integer, ForeignKey('ctagdefinition.id'))
    owner_id = Column(Integer, ForeignKey('centity.id'))

    __mapper_args__ = {
        'polymorphic_identity': 'ctaggedvalue',
        'inherit_condition': id == CEntity.id,
    }

    tagdefinition = relationship('CTagDefinition',
                             primaryjoin=(tagdefinition_id==CTagDefinition.id),
                             backref=backref('values', order_by=CTagDefinition.id))

    def __init__(self, xmi_id, tag, value, owner=None, order=None, package=None):
        super(CTaggedValue, self).__init__(xmi_id, None, order=order, package=package)
        self.tagdefinition = tag
        self.value = value
        self.owner = owner

    def __repr__(self):
        return "<CTaggedValue(xmi_id:'%s', tag:'%s', value:'%s')>" % (self.xmi_id, self.tagdefinition.name, self.value)

class CAssociation(CEntity):
    """Association class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :param ends: Association ends.
    :type xmi_id: str
    :type name: str
    :type ends: CAssociationEnd
    """

    __tablename__ = 'cassociation'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    ends = relationship('CAssociationEnd',
                        primaryjoin='CAssociationEnd.association_id==CAssociation.id',
                        order_by='CAssociationEnd.association_id',
                        backref=backref('association'))

    __mapper_args__ = { 'polymorphic_identity': 'cassociation' }

    def __init__(self, xmi_id, name, ends=[], order=None, package=None):
        super(CAssociation, self).__init__(xmi_id, name, order=order, package=package)
        self.ends = ends

    def __repr__(self):
        return "<CAssociation(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CAssociationEnd(CEntity):
    """AssociationEnd class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :param participant: UML Element participant.
    :param association: Owner association.
    :type xmi_id: str
    :type name: str
    :type participant: CEntity.
    :type association: CAssociation
    """

    __tablename__ = 'cassociationend'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    association_id = Column(Integer, ForeignKey('cassociation.id'))
    participant_id = Column(Integer, ForeignKey('centity.id'))
    isNavigable = Column(Boolean)
    aggregation = Column(String)
    multiplicityrange = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'cassociationend',
        'inherit_condition': id == CEntity.id,
    }

    participant = relationship('CEntity',
                             primaryjoin=(participant_id==CEntity.id),
                             backref=backref('associations', order_by=CEntity.id))

    def __init__(self, xmi_id, name, isNavigable=False, aggregation=None, participant=None, multiplicityrange=None, association=None, order=None, package=None):
        super(CAssociationEnd, self).__init__(xmi_id, name, order=order, package=package)
        self.isNavigable = isNavigable
        self.aggregation = aggregation
        self.participant = participant
        self.multiplicityrange = multiplicityrange
        self.association = association

    def __repr__(self):
        return "<CAssociationEnd(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    @property
    def swap(self):
        return [ e for e in self.association.ends if e.xmi_id != self.xmi_id ]

    @property
    def multiplicity(self):
        if 'related_to' in self.tag.keys():
            if not 'related_by' in self.tag.keys():
                raise RuntimeError, "Attribute %s.%s is a relation without path. Please set related_by tag." % (self.swap[0].participant.name, self.name)
            return 'related'
        my_mul = solvmul(self.multiplicityrange, self.aggregation)
        hi_mul = solvmul(self.swap[0].multiplicityrange, self.swap[0].aggregation)
        if my_mul is None or hi_mul is None:
            logging.warning("Multiplicity: Unsupported range %s, %s, %s, %s, %s, %s." (
                self.participant.name, self.name, my_situation,
                self.swap[0].participant.name, self.swap[0].name, his_situation
            ))
            import pdb; pdb.set_trace()
        else:
            r = '%s2%s' % (hi_mul, my_mul)
            return r

class CGeneralization(CEntity):
    """Generalization class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :param ends: Association ends.
    :type xmi_id: str
    :type name: str
    :type ends: CGeneralizationEnd
    """

    __tablename__ = 'cgeneralization'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    parent_id = Column(Integer, ForeignKey('centity.id'))
    child_id = Column(Integer, ForeignKey('centity.id'))

    parent = relationship('CEntity',
                          primaryjoin=(parent_id==CEntity.id),
                          backref=backref('parent_of', order_by=CEntity.id))
    child = relationship('CEntity',
                          primaryjoin=(child_id==CEntity.id),
                          backref=backref('child_of', order_by=CEntity.id))

    __mapper_args__ = {
        'polymorphic_identity': 'cgeneralization',
        'inherit_condition': id == CEntity.id,
    }

    def __init__(self, xmi_id, parent, child, order=None, package=None):
        super(CGeneralization, self).__init__(xmi_id, None, order=order, package=package)
        self.parent = parent
        self.child = child

    def __repr__(self):
        return "<CGeneralization(xmi_id:'%s', parent:'%s', child: '%s')>" % (self.xmi_id, self.parent.name, self.child.name)

stereotypes = Table(
    'stereotypes', Base.metadata,
    Column('centity_id', Integer, ForeignKey('centity.id')),
    Column('cstereotype_id', Integer, ForeignKey('cstereotype.id'))
    )

class CStereotype(CEntity):
    """Stereotype class.

    :param xmi_id: XMI identity of the data type.
    :param name: Data type name.
    :type xmi_id: str
    :type name: str
    """

    __tablename__ = 'cstereotype'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = { 'polymorphic_identity': 'cstereotype' }

    entities = relationship('CEntity', secondary=stereotypes, backref=backref('stereotypes'))

    def __init__(self, xmi_id, name, ends=[], order=None, package=None):
        super(CStereotype, self).__init__(xmi_id, name, order=order, package=package)

    def __repr__(self):
        return "<CStereotype(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CStateMachine(CEntity):
    """StateMachine class.

    :param xmi_id: XMI identity of the state machine.
    :param name: State machine name.
    """
    __tablename__ = 'cstatemachine'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    context_id = Column(Integer, ForeignKey('centity.id', use_alter=True, name='sm_context_id'))

    context = relationship('CEntity',
                           primaryjoin=context_id==CEntity.id,
                           backref=backref('statemachines'))

    __mapper_args__ = {
        'polymorphic_identity': 'cstatemachine',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = True

    def __init__(self, xmi_id, name, context, order=None, package=None):
        super(CStateMachine, self).__init__(xmi_id, name, order=order, package=package)
        self.context = context

    def __repr__(self):
        return "<CStateMachine(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    def list_states(self, ctype=None):
        ctype = ctype or CSimpleState
        for s in self.states:
            if type(s) is ctype:
                yield s

    def list_ordered_states(self, ctype=None):
        def take(S, D=[]):
            """
            Ordena estados en general, priorizando los por defecto.
            """
            if S == []:
                return D
            else:
                s = S.pop(0)
                N = sorted(s.next_states(stereotypes=['default']), key=lambda a: a.name)
                return take(N + filter(lambda ns: ns not in N + D,S),
                            filter(lambda ns: ns != s, D) + [s])

        return take(self.initial_states() + self.middle_states() + self.final_states())

    def initial_states(self):
        return [ s for s in self.list_states() if s.is_initial() ]

    def final_states(self):
        return [ s for s in self.list_states() if s.is_final() ]

    def middle_states(self):
        return [ s for s in self.list_states() if not s.is_final() and not s.is_initial() ]

    def stereotype_states(self, stereotype):
        return [ s for s in self.list_states() if s.is_stereotype(stereotype) ]

    def middle_transitions(self):
        for t in self.transitions:
            if type(t.state_from) is CSimpleState and type(t.state_to) is CSimpleState:
                yield t

    def list_triggers(self, stereotype=[]):
        for t in self.transitions:
            tt = t.trigger
            if tt is None or (stereotype is not None and not tt.is_stereotype(*stereotype)):
                continue
            yield tt

    def list_ordered_triggers(self):
        S = self.list_ordered_states()
        ST = sorted([ t for t in self.transitions if t.trigger is not None ], key=lambda t: S.index(t.state_to)*S.index(t.state_from))
        seen = set()
        seen_add = seen.add
        TT = [ x.trigger for x in reversed(ST) if x.trigger.name not in seen and not seen_add(x.trigger.name)]
        return [ t for t in reversed(TT) ]

class CBaseState(CEntity):
    """Simple State class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'cbasestate'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    statemachine_id = Column(Integer, ForeignKey('cstatemachine.id'))
    state_of_id = Column(Integer, ForeignKey('ccompositestate.id', use_alter=True, name='sm_state_composition_id'))

    statemachine = relationship('CStateMachine',
                             primaryjoin='CBaseState.statemachine_id==CStateMachine.id',
                             backref=backref('states'))
    state_of = relationship('CCompositeState',
                             primaryjoin='CBaseState.state_of_id==CCompositeState.id',
                             backref=backref('states'))

    __mapper_args__ = {
        'polymorphic_identity': 'cbasestate',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = True

    def __init__(self, xmi_id, name, statemachine, state_of=None, order=None, package=None):
        super(CBaseState, self).__init__(xmi_id, name, order=order, package=package)
        self.statemachine = statemachine
        self.state_of = state_of

    def __repr__(self):
        return "<CBaseState(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    def prev_states(self):
        for t in self.in_transitions:
            yield t.state_from

    def next_states(self):
        for t in self.out_transitions:
            yield t.state_to

    def is_initial(self):
        return max([ getattr(s, 'kind', '') == 'initial'
                    for s in self.prev_states() ] + [ False ])
    
    def is_final(self):
        return max([ type(s) is CFinalState
                    for s in self.next_states() ] + [ False ])

    def is_default(self):
        return any(t.is_stereotype('default') for t in self.transition_in)

    def prev_states(self, stereotypes=tuple()):
        for t in self.in_transitions:
            if t.is_stereotype(*stereotypes):
                yield t.state_from

    def next_states(self, stereotypes=tuple()):
        for t in self.out_transitions:
            if t.is_stereotype(*stereotypes):
                yield t.state_to

    def is_initial(self):
        return max([ getattr(s, 'kind', '') == 'initial'
                    for s in self.prev_states() ] + [ False ])
    
    def is_final(self):
        return max([ type(s) is CFinalState
                    for s in self.next_states() ] + [ False ])

    class BFS:
        def __init__(self, begin_states, final_states):
            self._revised = set(final_states)
            self._states = set(begin_states)
            self._final_states = set(final_states)
            self._final = False

        def __iter__(self):
            return self

        def next(self):
            if len(self._states) > 0:
                s = self._states.pop()
                self._revised.add(s)
                return s
            elif not self._final:
                states = set(itertools.chain(*[ s.next_states() for s in self._revised ])) - self._revised
                default_states = [ s for s in states
                                  if type(s) is CSimpleState and
                                    any(t.is_stereotype('default') for t in s.in_transitions)]
                default_states.sort(key=lambda a: s.name)
                nodefault_states = [ s for s in states
                                    if type(s) is CSimpleState and
                                     all(not t.is_stereotype('default') for t in s.in_transitions)]
                nodefault_states.sort(key=lambda a: s.name)
                self._states = default_states + nodefault_states
                if len(self._states) == 0:
                    self._final = True
                    self._states = self._final_states
                s = self._states.pop()
                self._revised.add(s)
                return s
            else:
                raise StopIteration

class CFinalState(CBaseState):
    """Final State class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'cfinalstate'

    id = Column(Integer, ForeignKey('cbasestate.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'cfinalstate',
        'inherit_condition': id == CBaseState.id,
    }

    __normalize_name__ = False

    def __init__(self, xmi_id, name, statemachine, state_of=None, order=None, package=None):
        super(CFinalState, self).__init__(xmi_id, name, statemachine, state_of=state_of, order=order, package=package)

    def __repr__(self):
        return "<CFinalState(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CSimpleState(CBaseState):
    """Simple State class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'csimplestate'

    id = Column(Integer, ForeignKey('cbasestate.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'csimplestate',
        'inherit_condition': id == CBaseState.id,
    }

    __normalize_name__ = True

    def __init__(self, xmi_id, name, statemachine, state_of=None, order=None, package=None):
        super(CSimpleState, self).__init__(xmi_id, name, statemachine, state_of=state_of, order=order, package=package)

    def __repr__(self):
        return "<CSimpleState(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CPseudostate(CBaseState):
    """Pseudo State class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'cpseudostate'

    id = Column(Integer, ForeignKey('cbasestate.id'), primary_key=True)
    kind = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'cpseudostate',
        'inherit_condition': id == CBaseState.id,
    }

    __normalize_name__ = False

    def __init__(self, xmi_id, name, kind, statemachine, state_of=None, order=None, package=None):
        super(CPseudostate, self).__init__(xmi_id, name, statemachine, state_of=state_of, order=order, package=package)
        self.kind = kind

    def __repr__(self):
        return "<CPseudostate(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CCompositeState(CBaseState):
    """Composite State class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'ccompositestate'

    id = Column(Integer, ForeignKey('cbasestate.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'ccompositestate',
        'inherit_condition': id == CBaseState.id,
    }

    __normalize_name__ = True

    def __init__(self, xmi_id, name, statemachine, state_of=None, order=None, package=None):
        super(CCompositeState, self).__init__(xmi_id, name, statemachine, state_of=state_of, order=order, package=package)

    def __repr__(self):
        return "<CCompositeState(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CExpression(CEntity):
    """Boolean Expression class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'cexpression'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'cexpression',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = True

    def __repr__(self):
        return "<CExpression(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CBooleanExpression(CExpression):
    """Boolean Expression class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    :param language: Language of the expression.
    :param body: Expression it self.
    """
    __tablename__ = 'cbooleanexpression'

    id = Column(Integer, ForeignKey('cexpression.id'), primary_key=True)
    language = Column(String)
    body = Column(Text)

    __mapper_args__ = {
        'polymorphic_identity': 'cbooleanexpression',
        'inherit_condition': id == CExpression.id,
    }

    __normalize_name__ = False

    def __init__(self, xmi_id, name, language, body, order=None, package=None):
        super(CBooleanExpression, self).__init__(xmi_id, name, order=order, package=package)
        self.language = language
        self.body = body

    def __repr__(self):
        return "<CBooleanExpression(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CGuard(CEntity):
    """Guard class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    :param expression: State type name.
    """
    __tablename__ = 'cguard'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    expression_id = Column(Integer, ForeignKey('cexpression.id'), primary_key=True)

    expression = relationship('CExpression',
                            primaryjoin=(expression_id==CExpression.id),
                            backref=backref('guards'))

    __mapper_args__ = {
        'polymorphic_identity': 'cguard',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = False

    def __init__(self, xmi_id, name, expression, order=None, package=None):
        super(CGuard, self).__init__(xmi_id, name, order=order, package=package)
        self.expression = expression

    def __repr__(self):
        return "<CGuard(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CAction(CEntity):
    """Action class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'caction'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'caction',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = True

    def __repr__(self):
        return "<CAction(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CCallAction(CAction):
    """Call action class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    :param operator: Operator.
    """
    __tablename__ = 'ccallaction'

    id = Column(Integer, ForeignKey('caction.id'), primary_key=True)
    operation_id = Column(Integer, ForeignKey('coperation.id'))

    operation = relationship('COperation',
                            primaryjoin=(operation_id==COperation.id),
                            backref=backref('related_actions'))

    __mapper_args__ = {
        'polymorphic_identity': 'ccallaction',
        'inherit_condition': id == CAction.id,
    }

    __normalize_name__ = False

    def __init__(self, xmi_id, name, operation, order=None, package=None):
        super(CCallAction, self).__init__(xmi_id, name, order=order, package=package)
        self.operation = operation

    def __repr__(self):
        return "<CCallAction(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CEvent(CEntity):
    """Event class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'cevent'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'cevent',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = True

    def __repr__(self):
        return "<CEvent(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

    def list_states_from(self, statemachine):
        for t in self.transitions:
            if t.statemachine == statemachine:
                yield t.state_from

    def list_states_to(self, statemachine):
        for t in self.transitions:
            if t.statemachine == statemachine:
                yield t.state_to

    def sm_transitions(self, statemachine):
        return [ t for t in self.transitions if t.statemachine == statemachine ]

    def any_transition_is_stereotype(self, statemachine, stereotype):
        for t in self.sm_transitions:
            if t.statemachine == statemachine and t.is_stereotype(stereotype):
                return True
        return False

class CCallEvent(CEvent):
    """Call event class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    :param operator: Operator.
    """
    __tablename__ = 'ccallevent'

    id = Column(Integer, ForeignKey('cevent.id'), primary_key=True)
    operation_id = Column(Integer, ForeignKey('coperation.id'))

    operation = relationship('COperation',
                            primaryjoin=(operation_id==COperation.id),
                            backref=backref('related_events'))

    __mapper_args__ = {
        'polymorphic_identity': 'ccallevent',
        'inherit_condition': id == CEvent.id,
    }

    __normalize_name__ = True

    def __init__(self, xmi_id, name, operation, order=None, package=None):
        super(CCallEvent, self).__init__(xmi_id, name, order=order, package=package)
        self.operation = operation

    def __repr__(self):
        return "<CCallEvent(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CSignal(CEntity):
    """Signal class.

    Asynchronous signal.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    """
    __tablename__ = 'csignal'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'csignal',
        'inherit_condition': id == CEntity.id,
    }

    __normalize_name__ = True

    def __repr__(self):
        return "<CSignal(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CSignalEvent(CEvent):
    """Signal event class.

    :param xmi_id: XMI identity of the data type.
    :param name: State type name.
    :param operator: Operator.
    """
    __tablename__ = 'csignalevent'

    id = Column(Integer, ForeignKey('cevent.id'), primary_key=True)
    signal_id = Column(Integer, ForeignKey('csignal.id'))

    signal = relationship('CSignal',
                            primaryjoin=(signal_id==CSignal.id),
                            backref=backref('called_by'))

    __mapper_args__ = {
        'polymorphic_identity': 'csignalevent',
        'inherit_condition': id == CEvent.id,
    }

    __normalize_name__ = True

    def __init__(self, xmi_id, name, signal, order=None, package=None):
        super(CSignalEvent, self).__init__(xmi_id, name, operation, order=order, package=package)
        self.signal = signal

    def __repr__(self):
        return "<CSignalEvent(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

class CTransition(CEntity):
    """Pseudo State class.

    :param xmi_id: XMI identity of the state.
    :param name: State name.
    :param state_from: Original state.
    :param state_to: Target state.
    """
    __tablename__ = 'ctransition'

    id = Column(Integer, ForeignKey('centity.id'), primary_key=True)
    statemachine_id = Column(Integer, ForeignKey('cstatemachine.id'))
    state_from_id = Column(Integer, ForeignKey('cbasestate.id'))
    state_to_id = Column(Integer, ForeignKey('cbasestate.id'))
    guard_id = Column(Integer, ForeignKey('cexpression.id'))
    effect_id = Column(Integer, ForeignKey('caction.id'))
    trigger_id = Column(Integer, ForeignKey('cevent.id'))

    statemachine = relationship('CStateMachine',
                             primaryjoin=statemachine_id==CStateMachine.id,
                             backref=backref('transitions'))
    state_from = relationship('CBaseState',
                              primaryjoin=(state_from_id==CBaseState.id),
                              backref=backref('out_transitions'))
    state_to = relationship('CBaseState',
                            primaryjoin=(state_to_id==CBaseState.id),
                            backref=backref('in_transitions'))

    guard = relationship('CExpression',
                            primaryjoin=(guard_id==CExpression.id),
                            backref=backref('transitions'))
    effect = relationship('CAction',
                            primaryjoin=(effect_id==CAction.id),
                            backref=backref('transitions'))
    trigger = relationship('CEvent',
                            primaryjoin=(trigger_id==CEvent.id),
                            backref=backref('transitions'))

    __mapper_args__ = { 'polymorphic_identity': 'ctransition' }

    __normalize_name__ = False

    def __init__(self, xmi_id, name, statemachine, state_from, state_to, guard=None, effect=None, trigger=None, order=None, package=None):
        super(CTransition, self).__init__(xmi_id, name, order=order, package=package)
        self.statemachine = statemachine
        self.state_from = state_from
        self.state_to = state_to
        self.guard = guard
        self.effect = effect
        self.trigger = trigger

    def __repr__(self):
        return "<CTransition(xmi_id:'%s', name:'%s')>" % (self.xmi_id, self.name)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
