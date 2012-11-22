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

class XMIParser:
    """Engine parser to XMI file (http://www.omg.org/technology/documents/modeling_spec_catalog.htm)

    Read a simple XMI file and compare the result with the expected output stored in .out file.

    >>> xmiObj = XMIParser()
    >>> xmiObj.parse("xmi2oerp/test/data/test_001.xmi")
    >>> out = open("xmi2oerp/test/data/test_001.out").read()
    >>> str(repr(xmiObj)) == out.strip()
    True

    Iterate for all entities xmi_ids

    >>> for xmi_id in xmiObj:
    ...     print xmi_id
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000866
    -84-17--56-5-43645a83:11466542d86:-8000:000000000000087C
    -84-17--56-5-43645a83:11466542d86:-8000:000000000000087D
    -84-17--56-5-43645a83:11466542d86:-8000:000000000000087E
    -84-17--56-5-43645a83:11466542d86:-8000:0000000000000880
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000867
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000868

    Iterate for all entities

    >>> for xmi_id in xmiObj:
    ...     print xmiObj[xmi_id]
    <CPackage(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000866', name:'Testing 1')>
    <CDataType(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:000000000000087C', name:'Integer')>
    <CDataType(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:000000000000087D', name:'UnlimitedInteger')>
    <CDataType(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:000000000000087E', name:'String')>
    <CEnumeration(xmi_id:'5', name:'Boolean', items:['TRUE', 'FALSE'])>
    <CClass(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000867', name:'Class 1')>
    <CAttribute(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000868', name:'attr1', size=None)>

    Read a more complex XMI file and compare the result with the expected output stored in .out file.

    >>> xmiObj = XMIParser()
    >>> xmiObj.parse("xmi2oerp/test/data/test_002.xmi")
    >>> out = open("xmi2oerp/test/data/test_002.out").read()
    >>> str(repr(xmiObj)) == out.strip()
    True

    Iterate for all Classes.

    >>> for xmi_id in xmiObj.iterclass(uml.CClass):
    ...     print xmiObj[xmi_id]
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010A5', name:'person')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010B1', name:'email')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010D8', name:'document')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010F7', name:'emaillist')>
    <CClass(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:0000000000001115', name:'estudios')>

    Iterate over members of "document"

    >>> for xmi_id in xmiObj.iterclass(uml.CMember,
    ...                                uml.CMember.member_of == xmiObj['127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010D8']):
    ...     print xmiObj[xmi_id]
    <CAttribute(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010D9', name:'number', size=None)>
    <CAttribute(xmi_id:'127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010E7', name:'tipo', size=None)>

    """

    def __init__(self):
        self.engine = create_engine('sqlite:///:memory:')
        uml.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.parsed_urls = []

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

    def parse(self, infile):
        """Load a XMI file.
        
        :param infile: Input to parse.
        :type infile: str for filene, or stream to direct process
        """
        store_url = False
        if type(infile) is str and not '<xml' in infile:
            if infile in self.parsed_urls:
                return True
            store_url = infile
            if not os.path.exists(infile):
                infile = self._c_load(infile)

        postprocessing_create = []
        postprocessing_append = []
        for event, elem in ET.iterparse(infile, events=('start', 'end')):
            kind = ('xmi.id'    in elem.attrib and 'description') or \
                   ('xmi.idref' in elem.attrib and 'reference') or \
                   ('href'      in elem.attrib and 'externalref')

            if (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Package'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cpackage = uml.CPackage(*params)
                self.session.add(cpackage)

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Class'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cclass = uml.CClass(*params)
                cpackage.classes.append(cclass)
                self.session.add(cclass)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Class'):
                cclass = None

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                params = [ elem.attrib[k] for k in  ['xmi.id', 'name'] ]
                cmember = uml.CDataType(*params)
                self.session.add(cmember)

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                url, xmi_id = elem.attrib['href'].split('#', 2)
                self.parse(url)
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

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                enumerationliterals = []

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}EnumerationLiteral'):
                enumerationliterals.append(elem.attrib['name'])

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
                
            else:
                if False:
                    # Turn on only for debug.
                    if not kind:
                        print >> sys.stderr, 'I:', elem.attrib.keys(), event, elem.tag
                    else:
                        print >> sys.stderr, 'I:', kind, event, elem.tag


        while postprocessing_create:
            theclass, params, querymask = postprocessing_create.pop(0)

            newparams = [ q and self.get(p, None) or p for p, q in zip(params, querymask) ]
            if None in [ m and p for p,m in zip(newparams, querymask) ]:
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
