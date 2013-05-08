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

from xmi2oerp.uml import *
from xmi2oerp.model import *
import logging

def count(l):
    diff = dict( (a.name, len([b.name for b in c.attributes if b.name == a.name])) for a in c.attributes )
    diff = dict( (name, count) for (name, count) in diff.items() if count > 1 )

class Validator():
    def __init__(self, model):
        self.model = model

    def check_duplicated_attributes(self):
        r = True
        for c in self.model.session.query(CClass):
            all_attributes = c.all_attributes()
            uni_attributes = set(all_attributes)
            if len(all_attributes) != len(uni_attributes):
                import pdb; pdb.set_trace()
                logging.error('Class %s (xmi_id=%s) have reapeated attributes: %s' % (c.name, c.xmi_id, diff.keys()))
                r = False

        return r

    def check_duplicated_associations(self):
        r = True
        for c in self.model.session.query(CClass):
            all_associations = [ a.name for a in c.all_associations() if a.name is not None ]
            uni_associations = set(all_associations)
            if len(all_associations) != len(uni_associations):
                import pdb; pdb.set_trace()
                logging.error('Class %s (xmi_id=%s) have reapeated associations: %s' % (c.name, c.xmi_id, diff.keys()))
                r = False

        return r

    def check_state_machines(self):
        r = True
        for sm in self.model.session.query(CStateMachine):
            # Must have name
            if sm.name is None:
                logging.error('Statemachine xmi_id=%s must have name' % (sm.xmi_id))
                r = False

            # Must have context
            if sm.context is None:
                logging.error('Statemachine %s (xmi_id=%s) must have context' % (sm.name, sm.xmi_id))
                r = False

            # Must have initial states
            if len(sm.initial_states()) != 1:
                logging.error('Statemachine %s (xmi_id=%s) must have an initial state' % (sm.name, sm.xmi_id))
                r = False

            # Must have initial final
            if len(sm.final_states()) == 0:
                logging.error('Statemachine %s (xmi_id=%s) must have final states' % (sm.name, sm.xmi_id))
                r = False

        return r


    def run(self):
        r = True
        r &= self.check_state_machines()
        r &= self.check_duplicated_associations()
        r &= self.check_duplicated_attributes()
        return r

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
