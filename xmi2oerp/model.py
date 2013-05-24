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
import logging
import time
import md5

_lines_to_stop = eval(os.environ.get('STOP','[]'))

class FileWrapper:
     def __init__(self, source, filename=None):
         if not hasattr(source, 'readline'):
             if os.path.exists(source):
                 source = open(source)
             else:
                 import StringIO
                 source = StringIO.StringIO(source)
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
    logging.debug("asNotResolved: %s" % p)
    return NotResolved

def maskstr(mask, params):
    return [ m and type(v) is str for m,v in zip(mask,params) ]

class Model:
    """UML Model.
    
    Engine parser read XMI files (http://www.omg.org/technology/documents/modeling_spec_catalog.htm)

    Read a simple XMI file and compare the result with the expected output stored in .out file.

    >>> model = Model()
    >>> model.load("xmi2oerp/test/data/test_001.xmi")
    >>> out = open("xmi2oerp/test/data/test_001.out").read()
    >>> print repr(model)
    <CPackage(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000866', name:'testing1')>
      <CClass(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000867', name:'class1')>
        <COperation(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:000000000000086B', name:'func1')>
        <CAttribute(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000868', name:'attr1', size=None)>
          <CDataType(xmi_id:'-84-17--56-5-43645a83:11466542d86:-8000:000000000000087C', name:'Integer')>

    Iterate for all entities xmi_ids

    >>> for xmi_id in model:
    ...     print xmi_id
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000865
    .:000000000000087A
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
    127-0-1-1--9b39813:13af03f5b9c:-8000:000000000000086B
    127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000868

    Iterate for all entities

    >>> for xmi_id in model:
    ...     print model[xmi_id]
    <CModel(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000865', name:'untitle')>
    <CModel(xmi_id:'.:000000000000087A', name:'UML 1.4 Standard Elements')>
    <CPackage(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000866', name:'testing1')>
    <CClass(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:0000000000000867', name:'class1')>
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
    <COperation(xmi_id:'127-0-1-1--9b39813:13af03f5b9c:-8000:000000000000086B', name:'func1')>
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

    >>> t = model['127-0-1-1-2b464aa4:13b09d81b72:-8000:00000000000010A6'].tag.items()
    >>> t.sort()
    >>> t
    [(u'label', u'Name'), (u'size', u'64')]

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
    [<CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:00000000000009AB', name:'car')>, <CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:00000000000009DC', name:'partener')>, <CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:00000000000009EF', name:'wheel')>, <CClass(xmi_id:'127-0-1-1-3b1b98f2:13b2e2eda8f:-8000:0000000000000A09', name:'resource')>]

    >>> child.is_stereotype('form')
    True

    >>> child.is_stereotype('method')
    False
    """

    def __init__(self, url=None, debug=False, db=':memory:'):
        self.engine = create_engine('sqlite:///%s' % db, echo=debug)
        uml.Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.parsed_urls = []
        self._load_stack = []
        self._postprocessing_create = []
        self._postprocessing_append = []
        self._postprocessing_set = []
        self._infiles = []
        self._order = 0
        if url != None:
            self.load(url)

    def _c_load(self, url):
        querypaths = lambda filename: \
                [os.path.join(os.path.expanduser('~'), '.xmi2oerp', 'profiles', filename),
                 pkg_resources.resource_filename(__name__, os.path.join('data', filename)) ]
        if 'http://argouml.org/user-profiles/' in url:
            filename = url.split('/')[-1]
            try:
                to_read = [ os.path.exists(fn) for fn in querypaths(filename) ].index(True)
                iofile = open(querypaths(filename)[to_read])
            except:
                raise RuntimeError, 'File not found. Search paths: %s' % querypaths
        else:
            code = md5.md5(url)
            filename = code.hexdigest()
            to_read = [ os.path.exists(fn) for fn in querypaths(filename) ]
            if not any(to_read):
                # Descargo el archivo de la red
                if not os.path.exists(querypaths('')[0]):
                    os.makedirs(querypaths('')[0])
                srcProfile = urlopen(url)
                dstProfile = open(querypaths(filename)[0], 'w')
                dstProfile.write(srcProfile.read())
                dstProfile.close()
                srcProfile.close()
            # Verifico que exista el archivo nuevamente
            to_read = [ os.path.exists(fn) for fn in querypaths(filename) ]
            iofile = open(querypaths(filename)[to_read.index(True)])
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

    def _push_load_stack(self):
        self._load_stack.append((self._postprocessing_create,
                                 self._postprocessing_append,
                                 self._postprocessing_set))
        self._postprocessing_create = []
        self._postprocessing_append = []
        self._postprocessing_set = []

    def _pop_load_stack(self):
        self._postprocessing_create, self._postprocessing_append, self._postprocessing_set = self._load_stack.pop()

    def _create(self, eclass, elem, mask=(False, False), attribs=['xmi.id','name'], booleans=[], extra_params=[], order=None, package=None):
        if order is None:
            order = self._order
            self._order += 1
        else:
            import pdb; pdb.set_trace()
        if package is None:
            logging.warning("Object without package associated")
        params = [ elem.attrib.get(k, None) for k in attribs ]
        if None in params:
            logging.debug("Object has undefined attributes for %s: %s" % (attribs, params))
        params.extend(extra_params)
        for i in booleans:
            params[i] = params[i] in ['true','1','TRUE']
        typemap = maskstr(mask, params)
        if any(typemap):
            self._postprocessing_create.append((eclass, params, typemap, order, package))
            obj = params[0]
        else:
            obj = eclass(*params, order=order, package=package)
            self.session.add(obj)
        if obj is None:
            import pdb; pdb.set_trace()
        return obj

    def _do_postprocessing_create(self):
        postprocessing_create = self._postprocessing_create
        allobjs = set(params[0] for eclass, params, typemask, order, package in postprocessing_create) | \
                set(self.iterclass(uml.CEntity)) 
        needsolve = set()

        while postprocessing_create and len(needsolve - allobjs) == 0:
            eclass, params, typemask, order, package = postprocessing_create.pop(0)

            typemask = [ type(v) is str and q for v,q in zip(params, typemask) ]
            newparams = [ (q and self.get(p, NotResolved)) or p for p, q in zip(params, typemask) ]
            needsolve |= set( v for i,v in zip(newparams, params) if i is NotResolved )

            if NotResolved in [ m and p for p,m in zip(newparams, typemask) ]:
                postprocessing_create.append((eclass, params, typemask, order, package))
            else:
                if newparams[0] in needsolve:
                    needsolve.remove(newparams[0])
                newobj = eclass(*newparams, order=order, package=package)
                self.session.add(newobj)

        if len(needsolve - allobjs) != 0:
            import pdb; pdb.set_trace()
            raise RuntimeError('Postprocessing can\'t create: %s.' % ','.join(needsolve - allobjs))

    def _append_obj(self, owner, member, obj):
        if type(owner) is str or type(obj) is str:
            owner = getattr(owner, 'xmi_id', owner)
            obj = getattr(obj, 'xmi_id', obj)
            self._postprocessing_append.append((owner, member, obj))
        else:
            getattr(owner, member).append(obj)

    def _do_postprocessing_append(self):
        postprocessing_append = self._postprocessing_append
        for owner_xmi_id, member, xmi_id in postprocessing_append:
            ref = self[owner_xmi_id]
            getattr(ref, member).append(self[xmi_id])

    def _do_postprocessing_set(self):
        postprocessing_set = self._postprocessing_set
        for xmi_id, attr, value in postprocessing_set:
            if type(value) is list:
                ts = set( type(v) for v in value )
                if len(ts)>1 and str in ts:
                    value = [ v if type(v) is not str else self[v] for v in value ]
                ts = set( type(v) for v in value )
                if len(ts)>1 and str in ts:
                    raise RuntimeError, "Error resolving '%s'." % "','".join(value)
            setattr(self[xmi_id], attr, value)

    def _get_xref(self, elem):
        url, xmi_id = elem.attrib['href'].split('#', 1)
        self.load(url)
        r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
        if len(r) > 1:
            logging.warning('More than one entity with id: %s' % xmi_id)
        return xmi_id if len(r) == 0 else r[0]

    def _get_ref(self, elem):
        xmi_id = elem.attrib['xmi.idref']
        r = list(self.session.query(uml.CEntity).filter(uml.CEntity.xmi_id == xmi_id))
        if len(r) > 1:
            logging.warning('More than one entity with id: %s' % xmi_id)
        return xmi_id if len(r) == 0 else r[0]

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
        q = self.session.query(umlclass)
        if filter:
            q = q.filter(filter)
        for k in q:
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

        owner = []
        in_xmi = False

        infile = FileWrapper(infile, store_url)

        self._infiles.append(infile)

# -- Parsing
        logging.info('Parsing file %s.' % getattr(infile, 'filename', infile))

        self._push_load_stack()

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

            if event == 'start' and kind == 'description':
                logging.debug('Processing <%s xmi.id="%s" name="%s"/>' % (elem.tag, elem.attrib['xmi.id'], elem.attrib.get('name')))

            if event == 'start' and 'xmi.id' in elem.attrib:
                owner.append(elem.attrib['xmi.id'])

            if event == 'end' and 'xmi.id' in elem.attrib:
                owner.remove(elem.attrib['xmi.id'])

# Model
            if (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Model'):
                if stop: import pdb; pdb.set_trace()
                cmodel = self._create(uml.CModel, elem)

# Package
            if (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Package'):
                if stop: import pdb; pdb.set_trace()
                cpackage = self._create(uml.CPackage, elem, extra_params=[cmodel])

            if (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Package'):
                if stop: import pdb; pdb.set_trace()
                cpackage = None

# UseCase
            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}UseCase'):
                if stop: import pdb; pdb.set_trace()
                cusecase = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}UseCase'):
                if stop: import pdb; pdb.set_trace()
                cusecase = self._create(uml.CUseCase, elem)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}UseCase'):
                if stop: import pdb; pdb.set_trace()
                cusecase = None

# Actor
            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Actor'):
                if stop: import pdb; pdb.set_trace()
                cactor = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Actor'):
                if stop: import pdb; pdb.set_trace()
                cactor = self._create(uml.CActor, elem)
                self._append_obj(cpackage, 'entities', cactor)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Actor'):
                if stop: import pdb; pdb.set_trace()
                cactor = None

# Class
            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Class'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Class'):
                if stop: import pdb; pdb.set_trace()
                if cclass is not None:
                    r = 'Class %s is inside the class %s.' % (elem.attrib['name'], cclass)
                    raise RuntimeError, r
                cclass = self._create(uml.CClass, elem)
                self._append_obj(cpackage, 'entities', cclass)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Class'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = cclass
                cclass = None

# DataType
            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = self._create(uml.CDataType, elem)

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = self._get_xref(elem)

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}DataType'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = self._get_ref(elem)

# Members: Enumeration
            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                enumerationliterals = []

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}EnumerationLiteral'):
                if stop: import pdb; pdb.set_trace()
                enumerationliterals.append(self._create(uml.CEnumerationLiteral, elem))

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = self._create(uml.CEnumeration, elem, mask=(False, False, False),
                                         attribs=['xmi.id','name'], extra_params=[enumerationliterals])

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}Enumeration'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = self._get_xref(elem)

# Members: Attribute

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Attribute'):
                if stop: import pdb; pdb.set_trace()
                cdatatype = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Attribute'):
                if stop: import pdb; pdb.set_trace()
                if cclass is None or cdatatype is None:
                    raise RuntimeError, "The attribute %s.%s has not type." % (cclass if type(cclass) is str else cclass.name, elem.attrib['name']) 
                cattribute = self._create(uml.CAttribute, elem, mask=(False, False, True, True), extra_params=[cdatatype, cclass])

# Members: Operation

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Operation'):
                if stop: import pdb; pdb.set_trace()
                coperation = self._create(uml.COperation, elem)
                self._append_obj(cclass, 'members', coperation)

# Parameters

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Parameter'):
                if stop: import pdb; pdb.set_trace()
                if 'coperation' in locals():
                    cparameter = self._create(uml.CParameter, elem,
                                              mask=(False, False, False, False, True),
                                              attribs=['xmi.id', 'name'],
                                              extra_params=[None, None, coperation])
                else:
                    """
                    Could be a TemplateParameter
                    """
                    pass

# Tags

            elif (kind, event, elem.tag) == ('plain', 'start', '{org.omg.xmi.namespace.UML}TaggedValue.dataValue'):
                if stop: import pdb; pdb.set_trace()
                tagvalue = elem.text or ''

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}TaggedValue.dataValue'):
                if stop: import pdb; pdb.set_trace()
                tagvalue = max(tagvalue, elem.text)

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                if stop: import pdb; pdb.set_trace()
                ctagdefinition = self._create(uml.CTagDefinition, elem)

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                if stop: import pdb; pdb.set_trace()
                tagdefinition = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}TagDefinition'):
                if stop: import pdb; pdb.set_trace()
                tagdefinition = self._get_xref(elem)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}TaggedValue'):
                if stop: import pdb; pdb.set_trace()
                tagvalue = max(tagvalue, elem.text or '')
                if len(owner) > 1:
                    ctaggedvalue = self._create(uml.CTaggedValue, elem,
                                                mask=(False, True, False, True), attribs=['xmi.id'],
                                                extra_params=[tagdefinition, tagvalue.strip() , owner[-1]])
                del tagvalue

# Associations

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}AssociationEnd'):
                if stop: import pdb; pdb.set_trace()
                multiplicityrange = None
                cdatatype = None
                cusecase = None
                cactor = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}MultiplicityRange'):
                if stop: import pdb; pdb.set_trace()
                multiplicityrange = (int(elem.attrib['lower']), int(elem.attrib['upper']))

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}AssociationEnd'):
                if stop: import pdb; pdb.set_trace()
                cassociationend = self._create(uml.CAssociationEnd, elem,
                                               mask=(False, False, False, False, True, False, True),
                                               attribs=['xmi.id', 'name', 'isNavigable', 'aggregation' ],
                                               booleans=[2],
                                               extra_params=[cdatatype or cusecase or cactor,
                                                             repr(multiplicityrange),
                                                             cassociation])
                multiplicityrange = None

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Association'):
                if stop: import pdb; pdb.set_trace()
                cassociation = self._create(uml.CAssociation, elem)
                cdatatype = None
                cusecase = None
                cactor = None
                cassociationend = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Association'):
                pass

# Generalization

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Generalization'):
                if stop: import pdb; pdb.set_trace()
                child = None
                parent = None
                cdatatype = None
                cactor = None

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Generalization.child'):
                if stop: import pdb; pdb.set_trace()
                child = cdatatype or cactor

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Generalization.parent'):
                if stop: import pdb; pdb.set_trace()
                parent = cdatatype or cactor

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Generalization'):
                if stop: import pdb; pdb.set_trace()
                logging.debug("GEN %s %s" % ( parent, child ))
                cgeneralization = self._create(uml.CGeneralization, elem,
                                               mask=(False, True, True),
                                               attribs=['xmi.id'],
                                               extra_params=[parent, child])
                child = None
                parent = None
                cdatatype = None
                cactor = None

# Stereotypes

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}Stereotype'):
                if stop: import pdb; pdb.set_trace()
                if len(owner) > 0:
                    self._append_obj(owner[-1], 'stereotypes', self._get_ref(elem))

            elif (kind, event, elem.tag) == ('externalref', 'start', '{org.omg.xmi.namespace.UML}Stereotype'):
                if stop: import pdb; pdb.set_trace()
                if len(owner) > 0:
                    self._append_obj(owner[-1], 'stereotypes', self._get_xref(elem))

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Stereotype'):
                if stop: import pdb; pdb.set_trace()
                stereotype = self._create(uml.CStereotype, elem)

# State machine 
            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}StateMachine'):
                if stop: import pdb; pdb.set_trace()
                ccompositestates = []
                cstatemachine = elem
                cdatatype = None

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}StateMachine.context'):
                if stop: import pdb; pdb.set_trace()
                if cdatatype is None:
                    logger.warning('StateMachine <%s> has not any context defined. Will not processed.' % elem.attrib['xmi.id'])
                    cstatemachine = None
                else:
                    cstatemachine = self._create(uml.CStateMachine, cstatemachine,
                                                 mask=(False, False, True),
                                                 attribs=['xmi.id', 'name'],
                                                 extra_params=[cdatatype])

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}CompositeState'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    cstate = self._create(uml.CCompositeState, elem, 
                                          mask=(False, False, True, True),
                                          attribs=['xmi.id', 'name'],
                                          extra_params=[cstatemachine,
                                          ccompositestates[-1] if len(ccompositestates)>0 else None] )
                    ccompositestates.append(cstate)
                else:
                    logging.warning('CompositeState %s without statemachine' % elem.attrib['xmi.id'])

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}CompositeState'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    ccompositestates.pop()
                    cstate = ccompositestates[-1] if len(ccompositestates) > 0 else None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}SimpleState'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    cstate = self._create(uml.CSimpleState, elem,
                                          mask=(False, False, True, True),
                                          attribs=['xmi.id', 'name'],
                                          extra_params=[cstatemachine,
                                          ccompositestates[-1] if len(ccompositestates)>0 else None] )
                else:
                    logging.warning('SimpleState %s without statemachine' % elem.attrib['xmi.id'])

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Pseudostate'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    cstate = self._create(uml.CPseudostate, elem,
                                          mask=(False, False, False, True, True),
                                          attribs=['xmi.id', 'name', 'kind'],
                                          extra_params=[cstatemachine,
                                          ccompositestates[-1] if len(ccompositestates)>0 else None] )
                else:
                    logging.warning('Pseudostate %s without statemachine' % elem.attrib['xmi.id'])

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}FinalState'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    cstate = self._create(uml.CFinalState, elem,
                                          mask=(False, False, True, True),
                                          attribs=['xmi.id', 'name'],
                                          extra_params=[cstatemachine,
                                          ccompositestates[-1] if len(ccompositestates)>0 else None] )
                else:
                    logging.warning('FinalState %s without statemachine' % elem.attrib['xmi.id'])

            elif (kind, event, elem.tag) in [
                    ('reference', 'start', '{org.omg.xmi.namespace.UML}CompositeState'), 
                    ('reference', 'start', '{org.omg.xmi.namespace.UML}SimpleState'), 
                    ('reference', 'start', '{org.omg.xmi.namespace.UML}Pseudostate'), 
                    ('reference', 'start', '{org.omg.xmi.namespace.UML}FinalState')
            ]:
                if cstatemachine != None:
                    cstate = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Transition'):
                if stop: import pdb; pdb.set_trace()
                source = None
                target = None
                guard = None
                effect = None
                trigger = None

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Transition.source'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    source = cstate

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Transition.target'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    target = cstate

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Transition.guard'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    guard = cexpression

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Transition.effect'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    effect = caction

            elif (kind, event, elem.tag) == ('plain', 'end', '{org.omg.xmi.namespace.UML}Transition.trigger'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    trigger = cevent

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}Transition'):
                ctransition = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}Transition'):
                if stop: import pdb; pdb.set_trace()
                if cstatemachine != None:
                    ctransition = self._create(uml.CTransition, elem,
                                               mask=(False, False, True, True, True, True, True, True),
                                               extra_params=[cstatemachine,
                                                             source,
                                                             target,
                                                             guard,
                                                             effect,
                                                             trigger])

# Effect 

#   Call Action

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}CallAction'):
                if stop: import pdb; pdb.set_trace()
                caction = self._get_ref(elem)

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}CallAction'):
                if stop: import pdb; pdb.set_trace()
                coperation = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}CallAction'):
                if stop: import pdb; pdb.set_trace()
                caction = self._create(uml.CCallAction, elem,
                                          mask=(False, False, True),
                                          attribs=['xmi.id', 'name'],
                                          extra_params=[coperation])


# Events 

#   Call

            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}CallEvent'):
                if stop: import pdb; pdb.set_trace()
                cevent = elem.attrib['xmi.idref']

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}CallEvent'):
                if stop: import pdb; pdb.set_trace()
                coperation = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}CallEvent'):
                if stop: import pdb; pdb.set_trace()
                cevent = self._create(uml.CCallEvent, elem,
                                          mask=(False, False, True),
                                          attribs=['xmi.id', 'name'],
                                          extra_params=[coperation])

#   Signal
            elif (kind, event, elem.tag) == ('reference', 'start', '{org.omg.xmi.namespace.UML}SignalEvent'):
                if stop: import pdb; pdb.set_trace()
                cevent = elem.attrib['xmi.idref']

            elif (kind, event, elem.tag) == ('description', 'start', '{org.omg.xmi.namespace.UML}SignalEvent'):
                if stop: import pdb; pdb.set_trace()
                csignal = None

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}SignalEvent'):
                if stop: import pdb; pdb.set_trace()
                cevent = self._create(uml.CCallEvent, elem,
                                          mask=(False, False, True),
                                          attribs=['xmi.id', 'name'],
                                          extra_params=[csignal])

# Expression

#   Boolean

            elif (kind, event, elem.tag) == ('description', 'end', '{org.omg.xmi.namespace.UML}BooleanExpression'):
                if stop: import pdb; pdb.set_trace()
                cexpression = self._create(uml.CBooleanExpression, elem,
                                           mask=(False, False, False, False),
                                           attribs=['xmi.id', 'name', 'language', 'body'])

# Unknown tags 

            else:
                if not kind:
                    logging.debug('Ignoring %s' % repr((elem.attrib.keys(), event, elem.tag)))
                else:
                    logging.debug('Ignoring %s' % repr((kind, event, elem.tag)))
                if stop:
                    import pdb; pdb.set_trace()
                    pass

        except Exception, m:
            r =  "Parsing error in line %i of file %s.\n" % (infile.lineno, infile.filename)
            if 'elem' in globals():
                r += "\t<Tag: %s, ID: %s> -\n" % (elem.tag, kind == 'description' and elem.attrib['xmi.id'] or '')
            r += "\tError: %s\n" % m
            r += "\tLine: %s\n" % sys.exc_traceback.tb_lineno
            r += "\tBreadcrumbs: %s\n" % ';'.join([ getattr(self.get(xmi_id, xmi_id),'name', xmi_id) for xmi_id in owner ])
            import traceback
            import StringIO
            sout = StringIO.StringIO()
            traceback.print_exc(file=sout)
            logging.error(sout.getvalue())
            raise RuntimeError, r

# -- Postprocessing
        self._do_postprocessing_create()
        self._do_postprocessing_append()
        self._do_postprocessing_set()

        self.session.commit()

        self._pop_load_stack()

        if store_url:
            self.parsed_urls.append(store_url)

        logging.debug('Stop processing %s.' % getattr(infile, 'filename', infile))

    def __repr__(self):
        s = []
        for p in self.session.query(uml.CPackage):
            s.append(repr(p))
            for c in p.entities:
                s.append('  %s' % (repr(c),))
                for a in c.members:
                    s.append('    %s' % (repr(a),))
                    if hasattr(a, 'datatype'):
                        s.append('      %s' % (repr(a.datatype)))
        return '\n'.join(s)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
