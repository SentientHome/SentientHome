
"""
        Ugly...

        work in progress, ment as proof of concept

        needs rewrite or cleanup
"""
__author__ = 'Peter Shipley <peter.shipley@gmail.com>'
__copyright__ = "Copyright (C) 2013 Peter Shipley"
__license__ = "BSD"


import time

import sys
# import os
# import traceback
import warnings
# import re
import base64
import socket
import select


import xml.etree.ElementTree as ET

from IsyEventData import EVENT_CTRL
import collections

try:
    import fcntl
except ImportError:
    fcntl = None

__all__ = ['ISYEvent']

class ISYEvent(object) :

    def __init__(self, addr=None, **kwargs):
        # print  "ISYEvent ", self.__class__.__name__

        self.debug = kwargs.get("debug", 0)
        self.connect_list = []
        self._shut_down = 0
        self.connected = False
        self.isy = kwargs.get("isy", None)
	self.level = kwargs.get("level", "1")

        self.process_func = kwargs.get("process_func", ISYEvent.print_event)
        self.process_func_arg = kwargs.get("process_func_arg", None)

        if self.process_func :
            assert isinstance(self.process_func, collections.Callable), \
                    "process_func Arg must me callable"

	addr = kwargs.get("addr", None)

        if addr :
	    userl = kwargs.get("userl", "admin")
	    userp = kwargs.get("userp", "admin")
	    authtuple = (  addr, userl, userp )
            self.connect_list.append(ISYEventConnection(self, authtuple) )


    def set_process_func(self, func, arg) :

        if func :
            self.process_func = func
            assert isinstance(self.process_func, collections.Callable), \
                    "process_func Arg must me callable"
        else:
            self.process_func = ISYEvent.print_event

        if arg :
            self.process_func_arg = arg



    def _finish(self)  :
        # print "Finishing... ", self.__class__.__name__
        for s in self.connect_list:
            s.disconnect()

        del self.connect_list[:]
        if self.isy :
            self.isy._isy_event = None
        # print "Finished... ", self.__class__.__name__

#    def __del__(self):
#       print "\n\n\n>>>>>>>>>__del__ ", \
#          self.__class__.__name__, "<<<<<<<<<<<<<\n\n\n"

    def _stop_event_loop(self) :
        # print self.__class__.__name__
        self._shut_down = 1

    # <?xml version="1.0" encoding="UTF-8"?><s:Envelope><s:Body>
    # <u:SetDebugLevel xmlns:u="urn:udi-com:service:X_Insteon_Lighting_Service:1">
    #<option>3</option></u:SetDebugLevel></s:Body></s:Envelope>
    def subscribe(self, **kwargs):
        """ subscribe to Isy device event stream

            this function adds an ISY device to the list of devices to
            receive events from

            named args:
		addr = IP address  or hostname of isydevice
		userl = isy admin login
		userp = isy admin password
		level = debug level
        """

	addr  = kwargs.get("addr", None)

        if self.debug & 0x01 :
            print("subscribe ", addr)

        if addr in self.connect_list :
	    # print "addr :", addr
	    print "connect_list :", self.connect_list
	    warnstr = str("Duplicate addr : {0}").format(addr)
            warnings.warn(warnstr, RuntimeWarning)
            return

	userl = kwargs.get("userl", "admin")
	userp = kwargs.get("userp", "admin")

	authtuple = (  addr, userl, userp )

        new_conn = ISYEventConnection(self, authtuple )

        # see if the other connections are connected
        # if so connect to avoid an error in select()
        if self.connected :
            new_conn.connect()

        self.connect_list.append(new_conn)

    def unsubscribe(self, addr):
        """ unsubscribe to Isy device event stream

            this function removes an ISY device to the list of devices to
            receive events from

            arg: IP address  or hostname of isydevice
        """
        remote_ip = socket.gethostbyname(addr)
        if not addr in self.connect_list :
            warnings.warn(
                "address {0}/{1} not subscribed".format(addr, remote_ip),
                RuntimeWarning)
            return
        isyconn = self.connect_list[self.connect_list.index(addr)]
        isyconn.disconnect()
        self.connect_list.remove(isyconn)
        del(isyconn)

    def _process_event(self, conn_obj) :
        """

            _process_event : takes XML from the events stream
                coverts to a dict and passed to process_func provided
        """
        #print "-"

        l = conn_obj.event_rf.readline()
        if len(l) == 0 :
            raise IOError("bad read form socket")
            # conn_obj._opensock(self.authtuple[0])
            # conn_obj._subscribe()
        # print "_process_event = ", l
        if (l[:5] != 'POST ') :
            print("Stream Sync Error")
            for x in range(10) :
                print(x, " ")
                l = conn_obj.event_rf.readline()
                if (l[:5] == 'POST ') :
                    break
            else :
                raise IOError("can not resync event stream")

        while 1 :
            l = conn_obj.event_rf.readline()
            if len(l) == 2 :
                break
            # print "HEADER : ", l
            if l[:15].upper() == "CONTENT-LENGTH:" :
                l.rstrip('\r\n')
                data_len = int(l.split(':')[1])

        # print "HEADER data_len ", data_len

        # data = conn_obj.event_rf.readread(data_len)
        data_remaining = data_len
        L = []
        while data_remaining :
            chunk = conn_obj.event_rf.read(data_remaining)
            if not chunk :
                break
            L.append(chunk)
            data_remaining -= len(chunk)
        data = ''.join(L)

        ddat = dict()

	# work around for encoding bugs
	# in eventinfo field
	if data.find('-->') >= 0 :
	    data = data.replace('-->', '--&gt;')

	if data.find('< ') >= 0 :
	    # print "< HACK"
	    data = data.replace('< ', '&lt; ')

	if data.find('<NULL>') :
	    data = data.replace('<NULL>', '&lt;NULL&gt;')

        # ev = ET.fromstring(data)
	try :
	    ev =  ET.fromstring(data)
	except ET.ParseError as e :
	    print "Etree ParseError "
	    print "data = ", data,
	    print "e.message = ", e.message
	    raise

        #print "_process_event ", data, "\n\n"


        ddat = self.et2d(ev)

        # print ddat
        #if ddat[control][0] == "_" :
        #       return
        # print ddat
        return(ddat, data)
        #return(ddat)


    def et2d(self, et) :
	""" Etree to Dict

            converts an ETree to a Dict Tree
            lists are created for duplicate tag

            arg: a ETree obj
            returns: a dict() obj

        """
	d = dict()
	children = list(et)
	if et.attrib :
	    for k, v in list(et.items()) :
		d[et.tag + "-" + k] =  v
	if children :
	    for child in children :
		if child.tag in d :
		    if type(d[child.tag]) != list :
			t = d[child.tag]
			d[child.tag] = [t]
		if list(child) or child.attrib :
		    if child.tag in d :
			d[child.tag].append(self.et2d(child))
		    else :
			d[child.tag] = self.et2d(child)
		else :
		    if child.tag in d :
			d[child.tag].append(child.text)
		    else :
			d[child.tag] = child.text
	return d


    @staticmethod
    def print_event(*arg):

        ddat = arg[0]
        # mydat = arg[1]
        exml = arg[2]

# Event Dat :
# {'control': 'DOF', 'node': '16 6C D2 7', 'eventInfo': None, 'Event-seqnum': '141', 'action': '0', 'Event-sid': 'uuid:40'}
# <?xml version="1.0"?><Event seqnum="141" sid="uuid:40"><control>DOF</control><action>0</action><node>16 6C D2 7</node><eventInfo></eventInfo></Event>
#
	ti = time.strftime('%X')
        try:
	    if ddat["control"] in ["_0", "_11", "_12", "_19" ] :
		pass

            elif ddat["control"] == "ERR" :
		print "{!s:<7} {!s:<4}\t{!s:<22}\t{!s}\t{!s}".format(
			ti, ddat['Event-seqnum'],
			"ERR",
			ddat['node'], ddat['action'])

		return


            elif ddat["control"] in ["DOF", "DON", "BMAN", "SMAN" ] :
		action=ddat["control"]
		status=ddat["node"]
		print "{!s:<7} {!s:<4}\t{!s}\t{!s}".format(
			ti, ddat['Event-seqnum'],  action, status)

            elif ddat["control"] in ["ST", "RR", "OL"] :
                ectrl = EVENT_CTRL.get(ddat["control"], ddat["control"])
                node = ddat["node"]

                evi = ddat["eventInfo"]
                # print ddat["Event-sid"]
                print("%-7s %-4s\t%-22s\t%-12s\t%s\t%s" % \
                    (ti, ddat["Event-seqnum"], \
                    ectrl, node, ddat["action"], evi))
		# print '_3 ', ddat["control"], ' : ', ddat

            elif  ddat["control"] == "_1" :
		# 'on': None, 'f': '140630 20:55:55', 's': '31', 'r': '140630 20:55:55', 'nr': None, 'id': '1E'}

		if ddat['action'] == '0' :
		    print "exml = ", exml
		    if "nsr" in  ddat["eventInfo"] :
			action = "Event Status"
			status ="id={!s} {!s}".format(ddat["eventInfo"]['id'], ddat["eventInfo"]['nsr'])
		    else :
			if 'on' in ddat["eventInfo"] :
			    ena = "enabled"
			else :
			    ena = "disabled"
			if 'rr' in ddat["eventInfo"] :
			    rr = "rr"
			else :
			    rr = "nr"
			action = "Event Status"
			status ="id={!s} {!s} {!s} run={!s} fin={!s} status={!s}".format(
			    ddat["eventInfo"]['id'],
			    ena, rr,
			    ddat["eventInfo"]['r'],
			    ddat["eventInfo"]['f'],
			    ddat["eventInfo"]['s'])

		if ddat['action'] == '1' :
		    action = "Get Status"
		    status = ""
		elif ddat['action'] == '2' :
		    action = "Key Change"
		    status = ddat['node']

		elif ddat['action'] == '3' :
		    action = "Info String"
		    status = "{!s}\t{!s} ".format(ddat['node'], ddat["eventInfo"])
		elif ddat['action'] == '4' :
		    action = "IR Learn Mode"
		    status = ""

		elif ddat['action'] == '5' :
		    action = "Schedule"
		    status = ddat['node']

		elif ddat['action'] == '6' :
		    action = "Var Stat"
		    status = "{!s} {!s}:{!s} {!s} {!s}".format(
			ddat['node'],
			ddat['eventInfo']['var']['var-type'],
			ddat['eventInfo']['var']['var-id'],
			ddat['eventInfo']['var']['val'],
			ddat['eventInfo']['var']['ts'] )
		elif ddat['action'] == '7' :
		    action = "Var Init"
		    status = "{!s} {!s}:{!s} {!s}".format(
			ddat['node'],
			ddat['eventInfo']['var']['var-type'],
			ddat['eventInfo']['var']['var-id'],
			ddat['eventInfo']['var']['init'])

		elif ddat['action'] == '8' :
		    action  = "Key"
		    status = ddat['eventInfo']
		else :
		    action = ddat['action'],
		    status = ddat['eventInfo']

		print "{!s:<7} {!s:<4}\t{!s:<22}\t{!s}\t{!s} ".format(
			ti, ddat['Event-seqnum'],
			"Trigger Event",
			action, status)

            elif  ddat["control"] == "_3" :
		if ddat['action'] == 'FD' :
		    action = 'new Folder node: '
		    status = str("{!s} = {!s}").format(ddat['node'],  ddat['eventInfo']['folder'])
		elif ddat['action'] == 'FR' :
		    action = 'del Folder node'
		    status = ddat['node']
		elif ddat['action'] == 'FN' :
		    action = 'rename Folder node'
		    status = ddat['node']
		elif ddat['action'] == 'CE' :
		    action = 'Clear Node Error'
		    status = ddat['node']
		elif ddat['action'] == 'NE' :
		    action = 'Node Error'
		    status = ddat['node']
		elif ddat['action'] == 'WH' :
		    action = "Pending Device Operation"
		    status =  ddat['node']
		elif ddat['action'] == 'WD' :
		    action = "Programming Device"
		    status =  ddat['node']
		elif ddat['action'] == 'SN' :
		    action = "Discovering Nodes"
		    status =  ""
		elif ddat['action'] == 'SC' :
		    action = "Discovering Nodes Complete"
		    status =  ""
		else :
		    action = ddat['action']
		    status = "{!s}\t{!s}".format(ddat['node'], ddat['eventInfo'])
		# "Node Change",
		print "{!s:<7} {!s:<4}\t{!s:<22}\t{!s}".format(
			ti, ddat['Event-seqnum'],
			action, status)

            elif  ddat["control"] == "_4" :
		status=""
		action=ddat['action']
		if ddat['action'] == '0' :
		    action = "Time Change"
		elif ddat['action'] == '1' :
		    action = "Time Conf Changed"
		elif ddat['action'] == '2' :
		    action = "NTP Setting Change"
		elif ddat['action'] == '3' :
		    action = "Notifications Settings Updated"
		elif ddat['action'] == '4' :
		    action = "NTP Communications Error"
		elif ddat['action'] == '5' :
		    action = "Batch Mode Updated"
		    status = ddat['eventInfo']['status']
		elif ddat['action'] == '6' :
		    action = "Battery Mode Programming Updated"
		    status = ddat['eventInfo']['status']
		else :
		    action = ddat['action']
		    status = ddat['eventInfo']

		print "{!s:<7} {!s:<4}\tSys Conf Updated\t{!s} : {!s}".format(
		ti, ddat['Event-seqnum'],  action, status)

            elif  ddat["control"] == "_5" :
		action=ddat['action']
		if ddat['action'] == '0' :
		    action = "Not Busy"
		elif ddat['action'] == '1' :
		    action = "Busy"
		elif ddat['action'] == '2' :
		    action = "Idle"
		elif ddat['action'] == '3' :
		    action = "Safe Mode"

		print "{!s:<7} {!s:<4}\tSys Status Updated\t{!s}".format(
		    ti, ddat['Event-seqnum'], action)


            elif  ddat["control"] == "_7" :
		if ddat['action'] == '1' :
		    action = "Update"
		elif ddat['action'] == '2.1' :
		    action = "Device Address Info"
		elif ddat['action'] == '2.2' :
		    action = "Device Address Warn"
		elif ddat['action'] == '2.3' :
		    action = "Device Address Error"
		else :
		    action = ddat['action']
		print "{!s:<7} {!s:<4}\tProgress Report\t{!s} : {!s}".format(ti,  ddat['Event-seqnum'], action, ddat["eventInfo"])

            elif  ddat["control"] == "_10" :
		action=ddat['action']
		status=ddat['eventInfo']

		if ddat['action'] == '1' :
		    action="Open ADR Error"
		    status=""
		if ddat['action'] == '2' :
		    action="Open ADR Status Update"
		    status=ddat['eventInfo']
		if ddat['action'] == '5' :
		    action="Flex Your Power Error"
		    status=""
		elif ddat['action'] == '6' :
		    action="Flex Your Power Status"
		    status=ddat['eventInfo']['active']

		print "{!s:<7} {!s:<4}\tOpenADR / Flex\t{!s}\t{!s}".format(
		    ti,  ddat['Event-seqnum'], action, status)


#            elif  ddat["control"] == "_12" :
#		pass
#            elif  ddat["control"] == "_1" and ddat["action"] in ["6", "7", "3"] :
#               print ddat["control"], " : ", ddat
#               print arg

	    else :
		    print "Event Dat : \n\t", ddat, "\n\t", exml
		    pass

            #print ddat
            # print data
        except Exception as e:
            print("Unexpected error:", sys.exc_info()[0])
            print(e)
            print(ddat)
	    raise
            # print data
        finally:
            pass


    def event_iter(self, ignorelist=None, poll_interval=0.5) :
        """Loop thought events

            reads events packets and passes them to processor

        """

        self.connected = True
        for s in self.connect_list:
            s.connect()

        while not self._shut_down  :
            if len(self.connect_list) == 0 :
                break
            try:
                r, _, e = select.select(self.connect_list, [], [], poll_interval)
                for rl in r :
                    d, _ = self._process_event(rl)
                    if ignorelist :
                        if d["control"] in ignorelist :
                            continue
                    yield d
            except socket.error :
                print("socket error({0}): {1}".format(e.errno, e.strerror))
                self.reconnect()
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
                self.reconnect()
            except KeyboardInterrupt :
                return
            #except Exception :
                #print("Unexpected Error:", sys.exc_info()[0])
                #traceback.print_stack()
                #print repr(traceback.extract_stack())
                #print repr(traceback.format_stack())
            finally:
                pass

        if self._shut_down :
            self._finish()


    def reconnect(self) :
        self.connected = True
        for isy_conn in self.connect_list:
            isy_conn.reconnect()

    def events_loop(self, **kargs) :
        """Loop thought events

            reads events packets and passes them to processor

        """
        ignorelist = kargs.get("ignorelist", None)
        poll_interval = kargs.get("poll_interval", 0.5)

        if self.debug & 0x01 :
            print("events_loop ", self.__class__.__name__)

        self.connected = True
        for isystream in self.connect_list:
            isystream.connect()


        while not self._shut_down  :
            try:
                r, _, e = select.select(self.connect_list, [], [], poll_interval)
                for rs in r :
                    d, x = self._process_event(rs)
                    # print "d :", type(d)
                    if ignorelist :
                        if d["control"] in ignorelist :
                            continue
                    self.process_func(d, self.process_func_arg, x)
                    # self.process_func(d, x)
            except socket.error as e:
                print("socket error({0}): {1}".format(e.errno, e.strerror))
                self.reconnect()
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
                self.reconnect()
#           except Exception :
#               print "Unexpected error:", sys.exc_info()[0]
            finally:
                pass

        if self._shut_down :
            self._finish()

class ISYEventConnection(object):

    def __init__(self, isyevent, authtuple ) :
        self.event_rf = None
        self.event_wf = None
        self.event_sock = None
        self.parent = isyevent
        self.error = 0
        self.debug = isyevent.debug

	# print "authtuple : ", type(authtuple), authtuple
	self.authtuple = authtuple

    def __hash__(self):
        return str.__hash__(self.authtuple[0])

    def __repr__(self):
	return "<ISYEventConnection %s at 0x%x>" % (self.authtuple[0], id(self))

    def __str__(self):
        return self.authtuple[0]

    def __del__(self):
        self.disconnect()
        #print "\n\n\n>>>>>>>>>__del__ ", self.__class__.__name__, "<<<<<<<<<<<<<\n\n\n"

    def __eq__(self, other):
        if isinstance(other, str) :
            return self.authtuple[0] == other
        if not hasattr(other, "authtuple") :
            return False
        return self.authtuple == other.authtuple

    def fileno(self):
        """ Interface required by select().  """
        return self.event_sock.fileno()

    def reconnect(self):
        # print "--reconnect to self.authtuple[0]--"
        self.error += 1
        self.disconnect()
        self.connect()

    def disconnect(self):
        try :
            if self.event_rf :
                self.event_rf.close()
                self.event_rf = False
        except IOError :
            pass

        try :
            if self.event_wf :
                self.event_wf.close()
                self.event_wf = False
        except IOError :
            pass

        try :
            if self.event_sock :
                self.event_sock.close()
                self.event_sock = False
        except IOError :
            pass

    def connect(self):
        if self.debug & 0x01 :
            print("connect ", self.__class__.__name__)
        self._opensock()
        self._subscribe()

    def _opensock(self):

        if self.debug & 0x01 :
            print("_opensock ", self.authtuple[0])

        # self.event_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = (self.authtuple[0], 80)
        self.event_sock = socket.create_connection(server_address, 10)

        #sn =  sock.getsockname()
        #self.myip = sn[0]
        #print "P ", self.myip

        #self.myurl = "http://{0}:{1}/".format(sn[0], self.server_address[1])
        #print "myurl ", self.myurl

        if fcntl is not None and hasattr(fcntl, 'FD_CLOEXEC'):
            flags = fcntl.fcntl(self.event_sock.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.event_sock.fileno(), fcntl.F_SETFD, flags)

        self.event_rf = self.event_sock.makefile("rb")
        self.event_wf = self.event_sock.makefile("wb")

        return self.event_sock

    def _subscribe(self):

        if self.debug & 0x01 :
            print("_subscribe : ", self.__class__.__name__)

#        if ( not isinstance(self.event_wf, socket)
#                or not isinstance(self.event_rf, socket)) :
#            raise RuntimeError(
#		    "{!s} called with invalid socket".format(self.__class__.__name__))

        # <ns0:Unsubscribe><SID>uuid:168</SID><flag></flag></ns0:Unsubscribe>
        post_body = "<s:Envelope><s:Body>" \
            "<u:Subscribe xmlns:u=\"urn:udicom:service:X_Insteon_Lighting_Service:1\">" \
            + "<reportURL>REUSE_SOCKET</reportURL>" \
            + "<duration>infinite</duration>" \
            "</u:Subscribe></s:Body></s:Envelope>"
            # "\r\n\r\n"

	base64pass = base64.encodestring('%s:%s' % (self.authtuple[1], self.authtuple[2]))[:-1]
        post_head = "POST /services HTTP/1.1\r\n" \
            + "Host: {0}:80\r\n".format(self.authtuple[0]) \
            + "Authorization: Basic {0}\r\n".format(base64pass) \
            + "Content-Length: {0}\r\n".format(len(post_body)) \
            + "Content-Type: text/xml; charset=\"utf-8\"\r\n" \
            + "\r\n\r\n"


        post = post_head + post_body

        self.event_wf.write(post)
        self.event_wf.flush()

        l = self.event_rf.readline()
        if (l[:5] != 'HTTP/') :
            raise ValueError(l)

        if (l.split(' ')[1] != "200") :
            raise ValueError(l)

        while 1 :
            l = self.event_rf.readline()
            if len(l) == 2 :
                break
            if l[:15] == "Content-Length:" :
                l.rstrip('\r\n')
                data_len = int(l.split(':')[1])


        reply = self.event_rf.read(data_len)
        if self.debug & 0x01 :
            print("_subscribe reply = '", reply, "'")


#
# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)

    print("syntax ok")
    exit(0)
