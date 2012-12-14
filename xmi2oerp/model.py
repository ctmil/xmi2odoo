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

from urllib2 import urlopen
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pkg_resources, os, sys
import uml

_lines_to_stop = []

class FileWrapper:
     def __init__(self, source, filename=None):
         self.source = source
         self.lineno = 0
         self.filename = filename
     def read(self, bytes):
         s = self.source.readline()
         self.lineno += 1
         return s

class NotResolved:
    pass

def asNotResolved(p):
    print p
    return NotResolved

class Model:
    """UML Model.
    
    Engine parser read XMI files (http://www.omg.org/technology/documents/modeling_spec_catalog.htm)

    Read a simple XMI file and compare the result with the expected output stored in .out file.

    >>> model = Model()
    >>> model.load("xmi2oerp/test/data/test_001.xmi")
    >>> out = open("xmi2oerp/test/data/test_001.out").read()
    >>> str(repr(model)) == out.strip()
    True

    Iterate for all entities xmi_ids

    >>> for xmi_id in model:
    ...     print xmi_id
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000866
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000867
    .:0000000000000821
    .:0000000000000822
    .:0000000000000823
    .:0000000000000824
    .:0000000000000825
    .:0000000000000826
    .:0000000000000827
    .:0000000000000828
    .:0000000000000829
    .:000000000000082A
    .:000000000000082B
    .:000000000000082C
    .:000000000000082D
    .:000000000000082E
    .:0000000000000830
    .:0000000000000833
    .:0000000000000834
    .:0000000000000835
    .:0000000000000836
    .:0000000000000837
    .:0000000000000838
    .:0000000000000839
    .:000000000000083A
    .:000000000000083B
    .:000000000000083C
    .:000000000000083D
    .:000000000000083E
    .:000000000000083F
    .:0000000000000840
    .:0000000000000842
    .:0000000000000843
    .:0000000000000844
    .:0000000000000845
    .:0000000000000846
    .:0000000000000847
    .:0000000000000848
    .:0000000000000849
    .:000000000000084A
    .:000000000000084B
    .:000000000000084C
    .:000000000000084D
    .:000000000000084E
    .:000000000000084F
    .:000000000000086A
    .:0000000000000874
    .:0000000000000875
    .:0000000000000876
    .:0000000000000877
    .:0000000000000878
    .:0000000000000879
    .:000000000000087C
    -84-17--56-5-43645a83:11466542d86:-8000:000000000000087C
    -84-17--56-5-43645a83:11466542d86:-8000:000000000000087D
    -84-17--56-5-43645a83:11466542d86:-8000:000000000000087E
    -84-17--56-5-43645a83:11466542d86:-8000:0000000000000880
    -84-17--56-5-43645a83:11466542d86:-8000:0000000000000881
    -84-17--56-5-43645a83:11466542d86:-8000:0000000000000882
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000868

    Iterate for all entities

    >>> for xmi_id in model:
    ...     print model[xmi_id]
    <CPackage(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000866', name:'Testing 1')>
    <CClass(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000867', name:'Class 1')>
    <CStereotype(xmi_id:'.:0000000000000821', name:'access')>
    <CStereotype(xmi_id:'.:0000000000000822', name:'friend')>
    <CStereotype(xmi_id:'.:0000000000000823', name:'import')>
    <CStereotype(xmi_id:'.:0000000000000824', name:'association')>
    <CStereotype(xmi_id:'.:0000000000000825', name:'global')>
    <CStereotype(xmi_id:'.:0000000000000826', name:'local')>
    <CStereotype(xmi_id:'.:0000000000000827', name:'parameter')>
    <CStereotype(xmi_id:'.:0000000000000828', name:'self')>
    <CStereotype(xmi_id:'.:0000000000000829', name:'become')>
    <CStereotype(xmi_id:'.:000000000000082A', name:'copy')>
    <CStereotype(xmi_id:'.:000000000000082B', name:'create')>
    <CStereotype(xmi_id:'.:000000000000082C', name:'call')>
    <CStereotype(xmi_id:'.:000000000000082D', name:'instantiate')>
    <CStereotype(xmi_id:'.:000000000000082E', name:'send')>
    <CStereotype(xmi_id:'.:0000000000000830', name:'destroy')>
    <CStereotype(xmi_id:'.:0000000000000833', name:'derive')>
    <CStereotype(xmi_id:'.:0000000000000834', name:'realize')>
    <CStereotype(xmi_id:'.:0000000000000835', name:'refine')>
    <CStereotype(xmi_id:'.:0000000000000836', name:'trace')>
    <CStereotype(xmi_id:'.:0000000000000837', name:'document')>
    <CStereotype(xmi_id:'.:0000000000000838', name:'executable')>
    <CStereotype(xmi_id:'.:0000000000000839', name:'file')>
    <CStereotype(xmi_id:'.:000000000000083A', name:'library')>
    <CStereotype(xmi_id:'.:000000000000083B', name:'table')>
    <CStereotype(xmi_id:'.:000000000000083C', name:'facade')>
    <CStereotype(xmi_id:'.:000000000000083D', name:'framework')>
    <CStereotype(xmi_id:'.:000000000000083E', name:'metamodel')>
    <CStereotype(xmi_id:'.:000000000000083F', name:'stub')>
    <CStereotype(xmi_id:'.:0000000000000840', name:'implementation')>
    <CStereotype(xmi_id:'.:0000000000000842', name:'type')>
    <CStereotype(xmi_id:'.:0000000000000843', name:'implicit')>
    <CStereotype(xmi_id:'.:0000000000000844', name:'invariant')>
    <CStereotype(xmi_id:'.:0000000000000845', name:'postcondition')>
    <CStereotype(xmi_id:'.:0000000000000846', name:'precondition')>
    <CStereotype(xmi_id:'.:0000000000000847', name:'metaclass')>
    <CStereotype(xmi_id:'.:0000000000000848', name:'powertype')>
    <CStereotype(xmi_id:'.:0000000000000849', name:'process')>
    <CStereotype(xmi_id:'.:000000000000084A', name:'thread')>
    <CStereotype(xmi_id:'.:000000000000084B', name:'utility')>
    <CStereotype(xmi_id:'.:000000000000084C', name:'requirement')>
    <CStereotype(xmi_id:'.:000000000000084D', name:'responsibility')>
    <CStereotype(xmi_id:'.:000000000000084E', name:'topLevel')>
    <CStereotype(xmi_id:'.:000000000000084F', name:'systemModel')>
    <CStereotype(xmi_id:'.:000000000000086A', name:'signalflow')>
    <CStereotype(xmi_id:'.:0000000000000874', name:'appliedProfile')>
    <CStereotype(xmi_id:'.:0000000000000875', name:'auxiliary')>
    <CStereotype(xmi_id:'.:0000000000000876', name:'modelLibrary')>
    <CStereotype(xmi_id:'.:0000000000000877', name:'profile')>
    <CStereotype(xmi_id:'.:0000000000000878', name:'source')>
    <CStereotype(xmi_id:'.:0000000000000879', name:'stateInvariant')>
    <CTagDefinition(xmi_id:'.:000000000000087C', name:'documentation')>
    <CDataType(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:000000000000087C', name:'Integer')>
    <CDataType(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:000000000000087D', name:'UnlimitedInteger')>
    <CDataType(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:000000000000087E', name:'String')>
    <CEnumeration(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:0000000000000880', name:'Boolean', literals:[u'TRUE', u'FALSE'])>
    <CEntity(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:0000000000000881', name:'TRUE')>
    <CEntity(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:0000000000000882', name:'FALSE')>
    <CAttribute(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000868', name:'attr1', size=None)>

    Read a more complex XMI file and compare the result with the expected output stored in .out file.

    >>> model = Model()
    >>> model.load("xmi2oerp/test/data/test_002.xmi")
    >>> out = open("xmi2oerp/test/data/test_002.out").read()
    >>> str(repr(model)) == out.strip()
    True

    Iterate for all Classes.

    >>> for xmi_id in model.iterclass(uml.CClass):
    ...     print model[xmi_id]
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010A5', name:'person')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010B1', name:'email')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010D8', name:'document')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010F7', name:'emaillist')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:0000000000001115', name:'estudios')>

    Iterate over members of "document"

    >>> for xmi_id in model.iterclass(uml.CMember,
    ...                                uml.CMember.member_of == model['127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010D8']):
    ...     print model[xmi_id]
    <CAttribute(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010D9', name:'number', size=None)>
    <CAttribute(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010E7', name:'tipo', size=None)>

    Take the Package and get properties.

    >>> package = model.iterclass(uml.CPackage).next()
    >>> model[package].tag['author']
    u'Cristian S. Rocha'

    >>> model[package].tag['documentation']
    u'Addon basico para almacenar personas.'

    >>> model['127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010A6'].tag
    {u'label': u'Name', u'size': u'64'}

    Take generalizations.

    >>> model = Model()
    >>> model.load("xmi2oerp/test/data/test_003.xmi")
    >>> gen = model.iterclass(uml.CGeneralization).next()
    >>> model[gen]
    <CGeneralization(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:0000000000000A0A', parent:'resource', child: 'car')>

    >>> parent = model[gen].parent
    >>> parent.parent_of
    [<CGeneralization(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:0000000000000A0A', parent:'resource', child: 'car')>, <CGeneralization(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:0000000000000A0B', parent:'resource', child: 'wheel')>]
    >>> parent.child_of
    []
    >>> child = model[gen].child
    >>> child.parent_of
    []
    >>> child.child_of
    [<CGeneralization(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:0000000000000A0A', parent:'resource', child: 'car')>]

    Take stereotypes
    >>> child.stereotypes
    [<CStereotype(xmi_id:'127-0-1-1--66344949:13b09938a14:-8000:00000000000011E5', name:'form')>, <CStereotype(xmi_id:'127-0-1-1--66344949:13b09938a14:-8000:00000000000011E6', name:'tree')>]
    
    >>> child.stereotypes[0].entities
    [<CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:00000000000009AB', name:'car')>, <CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:00000000000009DC', name:'partner')>, <CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:00000000000009EF', name:'wheel')>, <CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:0000000000000A09', name:'resource')>]

    >>> child.is_stereotype('form')
    True

    >>> child.is_stereotype('method')
    False
    """

    def __init__(self, url=None, debug=False):
        self.engine = create_engine('sqlite:///:memory:', echo=debug)
        uml.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.parsed_urls = []
        if url != None:
            self.load(url)

    def _c_load(self, url):
        if 'http://argouml.org/user-profiles/' in url:
            filename = url.split('/')[-1]
            querypaths = [ os.path.join(os.path.expanduser('~'), '.xmi2oerp', 'profiles', filename),
                           pkg_resources.resource_filename(__name__, os.path.join('data', filename)) ]
            try:
                to_read = [ os.path.exists(fn) for fn in querypaths ].index(True)
                iofile = open(querypaths[to_read])
            except:
                raise RuntimeError, 'File not found. Search paths: %s' % querypaths
        else:
            iofile = urlopen(url)
        return iofile

    def __contains__(self, xmi_id):
        """Return true if exists an UML Entity with this xmi_id.

        :param xmi_id: XMI Id to check existence.
        :type xmi_id: str
        """
        r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
        return len(r) == 1

    def __getitem__(self, xmi_id):
        """Return an UML Entity with xmi_id if exists. If not return xmi_id.

        :param xmi_id: XMI Id of the XML Entity.
        :type xmi_id: str
        """
        r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
        if len(r) != 1:
            raise KeyError
        else:
            return r[0]

    def get(self, xmi_id, default=None):
        """Return the UML Entity with xmi_id if exists else return default.

        :param xmi_id: XMI Id of the XML Entity.
        :param default: Default value to return if no Entity exists with xmi_id.
        :type xmi_id: str
        :type default: any
        """
        r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == str(xmi_id)))
        if len(r) == 0:
            return default
        elif len(r) == 1:
            return r[0]
        else:
            raise KeyError

    """
    def tagsdict(self, umlclass):
        if type(umlclass) is str:
            umlclass = self[umlclass]
        umlclass.tags
    """

    def iterclass(self, umlclass=uml.CEntity, filter=None):
        """Return a generator over a class of entity

        :param umlclass: Class over iterate.
        :param filter: Filter to select some of these entities.
        :type umlclass: Children of uml.CEntity or himself
        :type filter: Filter Relations
        """
        for k in self.session.query(umlclass).filter(filter):
            yield k.xmi_id

    def iterkeys(self):
        return self.iterclass(uml.CEntity)

    def __iter__(self):
        return self.iterkeys()

    def load(self, infile):
        """Load a XMI file.
        
        :param infile: Input to parse.
        :type infile: str for filene, or stream to direct process
        """

# -- Loading

        store_url = False
        if type(infile) is file:
            store_url = infile.name
        if type(infile) is str and not '<xml' in infile:
            if infile in self.parsed_urls:
                return True
            store_url = infile
            if not os.path.exists(infile):
                infile = self._c_load(infile)

        postprocessing_create = []
        postprocessing_append = []
        postprocessing_set = []
        owner = []
        in_xmi = False

        infile = FileWrapper(infile, store_url)

# -- Parsing

        try:

          cclass = None
          stop = False

          for event, elem in ET.iterparse(infile, events=('start', 'end')):

            if infile.lineno in _lines_to_stop:
                stop = True

# Ignore tags outside XMI description.
            if not in_xmi and elem.tag == 'XMI' and event == 'start':
                in_xmi = True
            if in_xmi     and elem.tag == 'XMI' and event == 'end':
                in_xmi = False
                break # In ArgoUML prevents errors if you load .uml files.
            if not in_xmi:
                continue

# Setup comaparison variables
            kind = ('xmi.id'    in elem.attrib and 'description') or \
                   ('xmi.idref' in elem.attrib and 'reference') or \
                   ('href'      in elem.attrib and 'externalref') or \
                    'plain'

            if event == 'start' and 'xmi.id' in elem.attrib:
                owner.append(elem.attrib['xmi.id'])

            if event == 'end' and 'xmi.id' in elem.attrib:
                owner.remove(elem.attrib['xmi.id'])

# Package

            if (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Package'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cpackage = uml.CPackage(*params)
                self.session.add(cpackage)

# Class

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Class'):
                if stop: import pdb; pdb.set_trace()
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                cdatatype = xmi_id if len(r) == 0 else r[0]

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Class'):
                if stop: import pdb; pdb.set_trace()
                if cclass is not None:
                    r = 'Class %s is inside the class %s.' % (elem.attrib['name'], cclass)
                    raise RuntimeError, r
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cclass = uml.CClass(*params)
                cpackage.classes.append(cclass)
                self.session.add(cclass)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Class'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = cclass
                cclass = None

# DataType

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cdatatype = uml.CDataType(*params)
                self.session.add(cdatatype)

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                if stop: import pdb; pdb.set_trace()
                url, xmi_id = elem.attrib['href'].split('#', 1)
                self.load(url)
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                cdatatype = xmi_id if len(r) == 0 else r[0]

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                if stop: import pdb; pdb.set_trace()
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                cdatatype = xmi_id if len(r) == 0 else r[0]

# Members: Enumeration

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                enumerationliterals = []

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}EnumerationLiteral'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                enumerationliterals.append(uml.CEnumerationLiteral(*params))
                self.session.add(enumerationliterals[-1])

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                params.append(enumerationliterals)
                cdatatype = uml.CEnumeration(*params)
                self.session.add(cdatatype)

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                cdatatype = xmi_id if len(r) == 0 else r[0]

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                url, xmi_id = elem.attrib['href'].split('#', 1)
                self.load(url)
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                cdatatype = xmi_id if len(r) == 0 else r[0]

# Members: Attribute

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Attribute'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Attribute'):
                if stop: import pdb; pdb.set_trace()
                if cclass is None or cdatatype is None:
                    import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                params.append(cdatatype)
                if type(cdatatype) is str or type(cclass) is str:
                    postprocessing_create.append((uml.CAttribute, params, (False, False, True)))
                    postprocessing_append.append((cclass if type(cclass) is str else cclass.xmi_id, 'members', params[0]))
                else:
                    cattribute = uml.CAttribute(*params)
                    self.session.add(cattribute)
                    cclass.members.append(cattribute)

# Members: Operation

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Operation'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                mask = (False, False, type(cdatatype) is str)
                
                if True in mask or type(cclass) is str:
                    postprocessing_create.append((uml.COperation, params, mask))
                    postprocessing_append.append((cclass if type(cclass) is str else cclass.xmi_id, 'members', params[0]))
                else:
                    coperation = uml.COperation(*params)
                    self.session.add(coperation)
                    cclass.members.append(coperation)

# Parameters

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Parameter'):
                if stop: import pdb; pdb.set_trace()
                if 'coperation' in globals():
                    params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                    params.append(None)
                    params.append(None)
                    params.append(None)
                    params.append(coperation)
                    mask = (False, False, False, False, False, False)
                    
                    if True in mask:
                        postprocessing_create.append((uml.CParameter, params, mask))
                    else:
                        cparameter = uml.CParameter(*params)
                        self.session.add(cparameter)
                else:
                    """
                    Could be a TemplateParameter
                    """
                    pass

# Tags

            elif (kind, event, elem.tag) == ('plain', 'start', '{org.omg.xmi.namespace.UML}TaggedValue.dataValue'):
                if stop: import pdb; pdb.set_trace()
                tagvalue = elem.text if elem.text is not None else ''

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                ctagdefinition = uml.CTagDefinition(*params)
                self.session.add(ctagdefinition)

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                if stop: import pdb; pdb.set_trace()
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                tagdefinition = xmi_id if len(r) == 0 else r[0]

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                if stop: import pdb; pdb.set_trace()
                url, xmi_id = elem.attrib['href'].split('#', 1)
                self.load(url)
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                tagdefinition = xmi_id if len(r) == 0 else r[0]

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}TaggedValue'):
                if stop: import pdb; pdb.set_trace()
                if len(owner) > 1:
                    params = [ elem.attrib[k] for k in  ['xmi.id'] ]
                    params.append(tagdefinition)
                    params.append(tagvalue.strip())
                    params.append(self.get(owner[-1], owner[-1]))
                    if type(tagdefinition) is str or type(params[-1]) is str:
                        postprocessing_create.append((uml.CTaggedValue, params, (False, True, False, True)))
                    else:
                        ctaggedvalue = uml.CTaggedValue(*params)
                        self.session.add(ctaggedvalue)

# Associations

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}AssociationEnd'):
                if stop: import pdb; pdb.set_trace()
                multiplicityrange = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}MultiplicityRange'):
                if stop: import pdb; pdb.set_trace()
                multiplicityrange = (int(elem.attrib['lower']), int(elem.attrib['upper']))

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}AssociationEnd'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib.get(k, None) for k in  ['xmi.id', 'name', 'isNavigable', 'aggregation' ] ]
                params[2] = (params[2] == 'true')
                params.append(cdatatype)
                params.append(repr(multiplicityrange))
                params.append(cassociation)
                mask = (False, False, False, False, type(cdatatype) is str, False, type(cassociation))
                if True in mask:
                    postprocessing_create.append((uml.CAssociationEnd, params, mask))
                else:
                    cassociationend = uml.CAssociationEnd(*params)
                    self.session.add(cassociationend)

                multiplicityrange = None

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Association'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cassociation = uml.CAssociation(*params)
                self.session.add(cassociation)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Association'):
                pass

# Generalization

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Generalization.child'):
                if stop: import pdb; pdb.set_trace()
                child = cdatatype

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Generalization.parent'):
                if stop: import pdb; pdb.set_trace()
                parent = cdatatype

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Generalization'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id'] ]
                params.append(parent)
                params.append(child)
                if type(parent) is str or type(child) is str:
                    postprocessing_create.append((uml.CGeneralization, params, (False, type(parent) is str, type(parent) is str)))
                else:
                    cgeneralization = uml.CGeneralization(*params)
                    self.session.add(cgeneralization)

# Stereotypes

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Stereotype'):
                if stop: import pdb; pdb.set_trace()
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    stereotypes.append(xmi_id)
                else:
                    stereotypes.append(r[0])

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}Stereotype'):
                if stop: import pdb; pdb.set_trace()
                url, xmi_id = elem.attrib['href'].split('#', 1)
                self.load(url)
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    stereotypes.append(xmi_id)
                else:
                    stereotypes.append(r[0])

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Stereotype'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                stereotype = uml.CStereotype(*params)
                self.session.add(stereotype)

            elif (kind, event, elem.tag) == ('plain', 'start', '{org.omg.xmi.namespace.UML}ModelElement.stereotype'):
                if stop: import pdb; pdb.set_trace()
                stereotypes = []

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}ModelElement.stereotype'):
                if stop: import pdb; pdb.set_trace()
                element = self.get(owner[-1], owner[-1])
                if type(element) is str:
                    postprocessing_set.append((element, 'stereotypes', stereotypes))
                else:
                    element.stereotypes = stereotypes

# State machine 

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}SimpleState'):
                if stop: import pdb; pdb.set_trace()
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                simplestate = uml.CSimpleState(*params)
                self.session.add(simplestate)

# Unknown tags 

            else:
                if stop:
                    if not kind:
                        print >> sys.stderr, 'I:', elem.attrib.keys(), event, elem.tag
                    else:
                        print >> sys.stderr, 'I:', kind, event, elem.tag
                    import pdb; pdb.set_trace()

        except Exception, m:
            r =  "Parsing error in line %i of file %s.\n" % (infile.lineno, infile.filename)
            r += "\t<Tag: %s, ID: %s> -\n" % (elem.tag, kind == 'description' and elem.attrib['xmi.id'] or '')
            r += "\tError: %s" % m
            raise RuntimeError, r

# -- Postprocessing

        allobjs = set(params[0] for theclass, params, querymask in postprocessing_create) | \
                set(self.iterclass(uml.CPackage)) | \
                set(self.iterclass(uml.CClass)) | \
                set(self.iterclass(uml.CDataType)) | \
                set(self.iterclass(uml.CEnumeration)) | \
                set(self.iterclass(uml.CAttribute)) | \
                set(self.iterclass(uml.COperation)) | \
                set(self.iterclass(uml.CParameter)) | \
                set(self.iterclass(uml.CTagDefinition)) | \
                set(self.iterclass(uml.CTaggedValue)) | \
                set(self.iterclass(uml.CAssociationEnd)) | \
                set(self.iterclass(uml.CAssociation)) | \
                set(self.iterclass(uml.CGeneralization)) | \
                set(self.iterclass(uml.CStereotype)) 

        needsolve = set()
        while postprocessing_create and len(needsolve - allobjs) == 0:
            theclass, params, querymask = postprocessing_create.pop(0)

            querymask = [ type(v) is str and q for v,q in zip(params, querymask) ]
            newparams = [ (q and self.get(p, NotResolved)) or p for p, q in zip(params, querymask) ]
            needsolve |= set( v for i,v in zip(newparams, params) if i is NotResolved )

            if NotResolved in [ m and p for p,m in zip(newparams, querymask) ]:
                postprocessing_create.append((theclass, params, querymask))
            else:
                if newparams[0] in needsolve:
                    needsolve.remove(newparams[0])
                newobj = theclass(*newparams)
                self.session.add(newobj)

        if len(needsolve - allobjs) != 0:
            raise RuntimeError('Cant create %s from file %s.' % (','.join(needsolve - allobjs), infile.filename))

        for owner_xmi_id, member, xmi_id in postprocessing_append:
            getattr(self[owner_xmi_id],member).append(self[xmi_id])

        for xmi_id, attr, value in postprocessing_set:
            if type(value) is list:
                ts = set( type(v) for v in value )
                if len(ts)>1 and str in ts:
                    value = [ v if type(v) is not str else self[v] for v in value ]
                ts = set( type(v) for v in value )
                if len(ts)>1 and str in ts:
                    raise RuntimeError, "Error resolving '%s'." % "','".join(value)
            setattr(self[xmi_id], attr, value)

        self.session.commit()

        if store_url:
            self.parsed_urls.append(store_url)

    def __repr__(self):
        s = []
        for p in self.session.query(uml.CPackage):
            s.append(repr(p))
            for c in p.classes:
                s.append('  %s' % (repr(c),))
                for a in c.members:
                    s.append('    %s' % (repr(a),))
                    try:
                        s.append('      %s' % (repr(a.datatype)))
                    except:
                        print "ouche!"
                        pass
        return '\n'.join(s)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
