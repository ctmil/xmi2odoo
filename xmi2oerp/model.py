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

    def iterclass(self, umlclass, filter=None):
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
        if type(infile) is str and not '<xml' in infile:
            if infile in self.parsed_urls:
                return True
            store_url = infile
            if not os.path.exists(infile):
                infile = self._c_load(infile)

        postprocessing_create = []
        postprocessing_append = []
        owner = []

# -- Parsing

        for event, elem in ET.iterparse(infile, events=('start', 'end')):
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
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cpackage = uml.CPackage(*params)
                self.session.add(cpackage)

# Class

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Class'):
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    cclass = xmi_id
                else:
                    cclass = r[0]

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Class'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cclass = uml.CClass(*params)
                cpackage.classes.append(cclass)
                self.session.add(cclass)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Class'):
                cclass = None

# DataType

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cmember = uml.CDataType(*params)
                self.session.add(cmember)

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                url, xmi_id = elem.attrib['href'].split('#', 1)
                self.load(url)
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    cdatatype = xmi_id
                else:
                    cdatatype = r[0]

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    cdatatype = xmi_id
                else:
                    cdatatype = r[0]

# Members: Enumeration

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                enumerationliterals = []

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}EnumerationLiteral'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                enumerationliterals.append(uml.CEnumerationLiteral(*params))
                self.session.add(enumerationliterals[-1])

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Enumeration'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                params.append(enumerationliterals)
                cmember = uml.CEnumeration(*params)
                self.session.add(cmember)

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    cdatatype = xmi_id
                else:
                    cdatatype = r[0]

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                url, xmi_id = elem.attrib['href'].split('#', 1)
                self.load(url)
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    cdatatype = xmi_id
                else:
                    cdatatype = r[0]

# Members: Attribute

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Attribute'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                params.append(cdatatype)
                if type(cdatatype) is str:
                    postprocessing_create.append((uml.CAttribute, params, (False, False, True)))
                    postprocessing_append.append((cclass.members, params[0]))
                else:
                    cattribute = uml.CAttribute(*params)
                    self.session.add(cattribute)
                    cclass.members.append(cattribute)

# Tags

            elif (kind, event, elem.tag) == ('plain', 'start', '{org.omg.xmi.namespace.UML}TaggedValue.dataValue'):
                tagvalue = elem.text if elem.text is not None else ''

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                ctagdefinition = uml.CTagDefinition(*params)
                self.session.add(ctagdefinition)

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                xmi_id = elem.attrib['xmi.idref']
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    tagdefinition = xmi_id
                else:
                    tagdefinition = r[0]

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                url, xmi_id = elem.attrib['href'].split('#', 1)
                self.load(url)
                r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
                if len(r) == 0:
                    tagdefinition = xmi_id
                else:
                    tagdefinition = r[0]

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}TaggedValue'):
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
                multiplicityrange = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}MultiplicityRange'):
                multiplicityrange = (int(elem.attrib['lower']), int(elem.attrib['upper']))

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}AssociationEnd'):
                params = [ elem.attrib.get(k, None) for k in  ['xmi.id', 'name', 'isNavigable', 'aggregation' ] ]
                params[2] = (params[2] == 'true')
                params.append(cclass)
                params.append(repr(multiplicityrange))
                cassociationend = uml.CAssociationEnd(*params)
                cassociation.ends.append(cassociationend)
                self.session.add(cassociationend)
                multiplicityrange = None

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Association'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cassociation = uml.CAssociation(*params)
                self.session.add(cassociation)

# Generalization

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Generalization.child'):
                child = cclass
                del cclass

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Generalization.parent'):
                parent = cclass
                del cclass

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Generalization'):
                params = [ elem.attrib[k] for k in  ['xmi.id'] ]
                params.append(parent)
                params.append(child)
                cgeneralization = uml.CGeneralization(*params)
                self.session.add(cgeneralization)
                del cgeneralization

# Unknown tags 

            else:
                if False:
                    # Turn on only for debug.
                    if not kind:
                        print >> sys.stderr, 'I:', elem.attrib.keys(), event, elem.tag
                    else:
                        print >> sys.stderr, 'I:', kind, event, elem.tag

# -- Postprocessing

        class NotResolved:
            pass

        while postprocessing_create:
            theclass, params, querymask = postprocessing_create.pop(0)

            querymask = [ type(v) is str and q for v,q in zip(params, querymask) ]
            newparams = [ (q and self.get(p, NotResolved)) or p for p, q in zip(params, querymask) ]

            if NotResolved in [ m and p for p,m in zip(newparams, querymask) ]:
                postprocessing_create.append((theclass, params, querymask))
            else:
                newobj = theclass(*newparams)
                self.session.add(newobj)


        for relation, xmi_id in postprocessing_append:
            relation.append(self[xmi_id])

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
