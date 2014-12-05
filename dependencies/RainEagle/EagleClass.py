
__author__ = 'Peter Shipley <peter.shipley@gmail.com>'
__copyright__ = "Copyright (C) 2014 Peter Shipley"
__license__ = "BSD"
__version__ = "0.1.7"

import socket
import sys
import os
import time
import xml.etree.ElementTree as ET
import urllib
import urllib2
from math import floor
from urlparse import urlparse
import json
from warnings import warn
from distutils.version import LooseVersion

min_fw_ver = "2.0.21"


from pprint import pprint


# api_arg_format = { }

__all__ = ['Eagle', 'RainEagleResponseError', 'to_epoch_1970', 'to_epoch_2000']


class RainEagleResponseError(RuntimeError):
    """General exception for responce errors
        from Rainforest Automation EAGLE (RFA-Z109)
    """
    pass


def to_epoch_2000(t) :
    """ converts time stored as
        to unix's epoch of 1970
        offset in seconds from "Jan 1 00:00:00 2000"
    """
    if isinstance(t, time.struct_time) :
        t = time.mktime(t)
    return t - 946684800


def to_epoch_1970(t) :
    """ converts time stored as
        offset in seconds from "Jan 1 00:00:00 2000"
        to unix's epoch of 1970
    """
    if isinstance(t, (int, long, float)) :
        return t + 946684800
    if isinstance(t, str) and t.startswith('0x') :
        return 946684800 + int(t, 16)

def _et2d(et) :

    """ Etree to Dict

        converts an ETree to a Dict Tree
        lists are created for duplicate tag

        if there are multiple XML of the same name
        an list array is used
        attrib tags are converted to "tag_name" + "attrib_name"

        if an invalid arg is passed a empty dict is retrurned


        arg: ETree Element  obj

        returns: a dict obj
    """
    d = dict()
    if not isinstance(et, ET.Element) :
        return d
    children = list(et)
    if et.attrib :
        for k, v in list(et.items()) :
            d[et.tag + "-" + k] = v
    if children :
        for child in children :
            if child.tag in d :
                if type(d[child.tag]) != list :
                    t = d[child.tag]
                    d[child.tag] = [t]
            if list(child) or child.attrib :
                if child.tag in d :
                    d[child.tag].append(_et2d(child))
                else :
                    d[child.tag] = _et2d(child)
            else :
                if child.tag in d :
                    d[child.tag].append(child.text)
                else :
                    d[child.tag] = child.text
    return d


def _twos_comp(val, bits=32):
    """compute the 2's compliment of int value val"""
    if( (val&(1<<(bits-1))) != 0 ):
        val = val - (1<<bits)
    return val


def _tohex(n, width=8) :
    """
        convert arg to string with hex representation if possible

        use twos-complement for negitive 32bit numbers

        use int class to convert whatever is handed to us
    """
    if isinstance(n, str) and n.startswith('0x') :
        return(n)

    i = int(n)

    # add two for the "0x"
    width += 2

    if (i > 2147483647) or (i < -2147483648) :
        warn("_tohex : signed int to large (" + str(n) + ")\n",
                        RuntimeWarning, stacklevel=2)

    if i < 0 :
        i += 0x100000000

    return  "{:#0{width}x}".format(int(i), width=width)


#
class Eagle(object) :
    """
        Class for talking to Rainforest Automation EAGLE (RFA-Z109)

        args:
            debug       print debug messages if true
            addr        address of device
            port        port on device (default 5002)
            getmac      connect to device at start up and get macid (default true)
            timeout     TCP socket timeout

        Currently there is very little error handling ( if any at all )
    """
    def __init__(self, **kwargs):

        self.debug = kwargs.get("debug", 0)

        if self.debug :
            print self.__class__.__name__, __name__
        self.checkfw = kwargs.get("checkfirmware", True)
        self.addr = kwargs.get("addr", os.getenv('EAGLE_ADDR', None))
        self.port = kwargs.get("port", os.getenv('EAGLE_PORT', 5002))
        self.mac = kwargs.get("mac", None)
        self.timeout = kwargs.get("timeout", 10)

        self.soc = None
        self.macid = None

        if self.debug :
            print "Addr :  = ", self.addr
            print "timeout :  = ", self.timeout
            print "debug :  = ", self.debug


	if self.addr is None :
	    raise AssertionError("no hostname or IP given")

        # preload
        if self.mac is None :
            self.device_info = self.list_devices()
            if self.device_info is None :
                raise IOError("Error connecting")
            if self.debug :
                print "__init__ ",
                pprint(self.device_info)
            # self.macid = self.device_info['DeviceInfo']['DeviceMacId']
            if self.debug :
                print "Init DeviceMacId = ", self.macid

        if self.checkfw :
	    mysetting = self.get_setting_data()
	    dev_fw_ver = mysetting['device_fw_version']
	    if ( LooseVersion(dev_fw_ver) < LooseVersion(min_fw_ver) ) :
		warn_message = "Warning : device firmware " \
			+ "{0} < {1} please concideer " \
			+ "updating ".format(dev_fw_ver, min_fw_ver)
		warn( warn_message, RuntimeWarning, stacklevel=3)



# socket commands as class functions

    def list_devices(self):
        """
	    Send the LIST_DEVICES command
	    returns information about the EAGLE device

        """
        comm_responce = self._send_soc_comm("list_devices")
        if self.debug :
            print "comm_responce =", comm_responce
        if comm_responce is None:
            raise RainEagleResponseError("list_devices : Null reply")
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)
        if self.macid is None :
            self.macid = rv['DeviceInfo']['DeviceMacId']
        return rv

    # 3
    def get_device_data(self, macid=None) :
        """ Send the GET_DEVICE_DATA command to get a data dump """
        if macid is None :
            macid = self.macid
        comm_responce = self._send_soc_comm("get_device_data", MacId=macid)
        if comm_responce is None:
            raise RainEagleResponseError("get_device_data : Null reply")
        if self.debug :
	    print comm_responce
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)
        return rv

    # 10
    def get_instantaneous_demand(self, macid=None) :
        """ Send the GET_INSTANTANEOUS_DEMAND command
            get the real time demand from the meter

            args:
                MacId   16 hex digits, MAC addr of EAGLE ZigBee radio
        """
        if macid is None :
            macid = self.macid
        comm_responce = self._send_soc_comm("get_instantaneous_demand",
                MacId=macid)
        if comm_responce is None:
            raise RainEagleResponseError("get_instantaneous_demand : Null reply")
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)
        return rv

    # 11
    def get_demand_values(self, macid=None, interval="hour", frequency=None) :
        """ Send the GET_DEMAND_VALUES command
            get a series of instantaneous demand values

            args:
                MacId   16 hex digits, MAC addr of EAGLE ZigBee radio
                Interval        hour | day | week
                [Frequency]     int   seconds between samples
        """
        if macid is None :
            macid = self.macid
        if interval not in ['hour', 'day', 'week' ] :
            raise ValueError("get_demand_values interval must be 'hour', 'day' or 'week' ")
        kwargs = {"MacId": macid, "Interval": interval}
        if frequency :
            kwargs["Frequency"] = str(frequency)
        comm_responce = self._send_soc_comm("get_demand_values", **kwargs)
        if comm_responce is None:
            raise RainEagleResponseError("get_demand_values : Null reply")
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)
        return rv

    # 12
    def get_summation_values(self, macid=None, interval="day") :
        """ Send the GET_SUMMATION_VALUES command
            get a series of net summation values

            args:
                MacId   16 hex digits, MAC addr of EAGLE ZigBee radio
                Interval        day | week | month | year
        """
        if macid is None :
            macid = self.macid
        if interval not in ['day', 'week', 'month', 'year'] :
            raise ValueError("get_summation_values interval must be 'day', 'week', 'month' or 'year'")
        comm_responce = self._send_soc_comm("get_summation_values",
            MacId=macid, Interval=interval)
        if comm_responce is None:
            raise RainEagleResponseError("get_summation_values : Null reply")
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)
        return rv

    # 14
    def set_fast_poll(self, macid=None, frequency="0x04", duration="0xFF") :
        """ Send the SET_FAST_POLL command
            set the fast poll mode on the meter

            args:
                MacId   16 hex digits, MAC addr of EAGLE ZigBee radio
                Frequency       0x01 - 0xFF     Freq to poll meter, in seconds
                Duration        0x00 - 0x0F     Duration of fast poll mode, in minutes (max 15)
        """
        if macid is None :
            macid = self.macid
        frequency = _tohex(frequency, 2)
        duration = _tohex(duration, 2)

        comm_responce = self._send_soc_comm("get_instantaneous_demand",
            MacId=macid, Frequency=frequency, Duration=duration)
        if comm_responce is None:
            raise RainEagleResponseError("set_fast_poll : Null reply")
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)
        return rv

    # 15
    def get_fast_poll_status(self, macid=None) :
        """ Send the GET_FAST_POLL_STATUS command
            get the current status of fast poll mode.

            args:
                MacId   16 hex digits, MAC addr of EAGLE ZigBee radio
        """
        if macid is None :
            macid = self.macid
        comm_responce = self._send_soc_comm("get_fast_poll_status", MacId=macid)
        if comm_responce is None:
            return None
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)

        return rv

    # 17
    def get_history_data(self, macid=None, starttime="0x00000000", endtime=None, frequency=None) :
        """ Send the GET_HISTORY_DATA command
            get a series of summation values over an interval of time
            ( socket command api )

            args:
                MacId   16 hex digits, MAC addr of EAGLE ZigBee radio
                StartTime       the start of the history interval (default oldest sample)
                EndTime         the end of the history interval (default current time)
                Frequency       Requested number of seconds between samples.
        """
        if macid is None :
            macid = self.macid
        kwargs = {"MacId": macid}
        kwargs["StartTime"] = _tohex(starttime, 8)
        if endtime :
            kwargs["EndTime"] = _tohex(endtime, 8)
        if frequency :
            kwargs["Frequency"] = _tohex(endtime, 4)
        comm_responce = self._send_soc_comm("get_history_data", **kwargs)
        if comm_responce is None :
            raise RainEagleResponseError("get_history_data : Null reply")
        etree = ET.fromstring('<S>' + comm_responce + '</S>')
        rv = _et2d(etree)
        return rv

# http commands as class functions

    def get_device_list(self) :
        """
	    Send the LIST_DEVICES command
	    returns information about the EAGLE device

        """
        comm_responce = self._send_http_comm("get_device_list")
        return json.loads(comm_responce)

    def get_uploaders(self) :
        """
            gets list of uploaders for Web UI

            On Success returns dict with the values (example):
                'uploader[0]':          'none'
                'uploader[1]':          'bidgely'
                'uploader_name[0]':     'None'
                'uploader_name[1]':     'Bidgely Inc.'

        """
        comm_responce = self._send_http_comm("get_uploaders")
        return json.loads(comm_responce)

    def get_uploader(self) :
        """
            gets current uploaders config

            On Success returns dict with the values (example):
                "uploader_timestamp" :  "1394503703"
                "uploader_provider" :   "bidgely"
                "uploader_protocol" :   "https"
                "uploader_hostname" :   "api.bidgely.com"
                "uploader_url" :        "/v1/users/44441b47-1b9a-4a65-8e8c-0efefe05bb88/homes/1/gateways/1"
                "uploader_port" :       "0"
                "uploader_auth_code" :  "44441b47-1b9a-4a65-8e8c-0efefe05bb88"
                "uploader_email" :      ""
                "uploader_user_id" :    ""
                "uploader_password" :   ""
                "uploader_enabled" :    "Y"

            See also set_cloud() to set current uploader cloud config
        """
        comm_responce = self._send_http_comm("get_uploader")
        return json.loads(comm_responce)


    def set_message_read(self) :
        """
            On Success returns dict with the values :
                'remote_management_status' :    'success'

        """
        comm_responce = self._send_http_comm("set_message_read")
        return json.loads(comm_responce)

    def confirm_message(self, id) :
        """
        """
        id = _tohex(id)
        comm_responce = self._send_http_comm("confirm_message", Id=id)
        return json.loads(comm_responce)

    def get_message(self) :
        """
            On Success returns dict with the values (example):
                "meter_status" :        "Connected"
                "message_timestamp" :   "946684800"
                "message_text" :        ""
                "message_confirmed" :   "N"
                "message_confirm_required" :    "N"
                "message_id" :  "0"
                "message_queue" :       "active"
                "message_priority" :    ""
                "message_read" :        "Y"

        """
        comm_responce = self._send_http_comm("get_message")
        return json.loads(comm_responce)

    def get_usage_data(self) :
        """
            Get current demand usage summation

            On Success returns dict with the values (example):
                'demand' :               '0.4980'
                'demand_timestamp' :     '1394505386'
                'demand_units' :         'kW'
                'message_confirm_required' :     'N'
                'message_confirmed' :    'N'
                'message_id' :           '0'
                'message_priority' :     ''
                'message_queue' :        active'
                'message_read' :         'Y'
                'message_text' :         ''
                'message_timestamp' :    '946684800'
                'meter_status' :         'Connected'
                'price' :                '0.1400'
                'price_label' :          'Set by User'
                'price_units' :          '$'
                'summation_delivered' :  '2667.867'
                'summation_received' :   '37.283'
                'summation_units' :      'kWh'
                'usage_timestamp' :      '1394505386'

        """
        comm_responce = self._send_http_comm("get_usage_data")
        return json.loads(comm_responce)


    def get_historical_data(self, period="day") :
        """
            get a series of summation values over an interval of time
            ( http command api )

            args:
                period          day|week|month|year

            On Success returns dict with the values (example):
                'data_period'            'day'
                'data_size'              '14'
                'timestamp[0]'           '1394422200'
                'timestamp[1]'           '1394425800'
                'timestamp[2]'           '1394429400'
                'timestamp[3]'           '1394433000'
                'timestamp[4]'           '1394436600'
                'timestamp[5]'           '1394440200'
                'timestamp[6]'           '1394443800'
                'timestamp[7]'           '1394447400'
                'timestamp[8]'           '1394451000'
                'timestamp[9]'           '1394454600'
                'timestamp[10]'          '1394458200'
                'timestamp[11]'          '1394461800'
                'timestamp[12]'          '1394465400'
                'timestamp[13]'          '1394469000'
                'value[0]'               '0.429'
                'value[1]'               '0.426'
                'value[2]'               '0.422'
                'value[3]'               '0.627'
                'value[4]'               '0.735'
                'value[5]'               '0.193'
                'value[6]'               '0.026'
                'value[7]'               '-0.985'
                'value[8]'               '-1.491'
                'value[9]'               '-2.196'
                'value[11]'              '-1.868'
                'value[12]'              '-1.330'
                'value[13]'              '-0.870'

        """
        if period not in ['day', 'week', 'month', 'year'] :
            raise ValueError("get_historical_data : period must be one of day|week|month|year")
        comm_responce = self._send_http_comm("get_historical_data", Period=period)
        return json.loads(comm_responce)


    def get_setting_data(self) :
        """
            get settings data

            On Success returns dict with value containing setting
            relating to price, uploader, network & device

        """
        comm_responce = self._send_http_comm("get_setting_data")
        return json.loads(comm_responce)

    def get_device_config(self) :
        """
            get remote management status

            On Success returns dict with value 'Y' or 'N' :
               'config_ssh_enabled':    'Y'
               'config_vpn_enabled':    'Y'

        """
        comm_responce = self._send_http_comm("get_device_config")
        return json.loads(comm_responce)

    def get_gateway_info(self) :
        """
            gets network status

            On Success returns dict with the values (example):
                'gateway_cloud_id':             '00:09:69'
                'gateway_internet_status':      'connected'
                'gateway_ip_addr':              '10.11.12.13'
                'gateway_mac_id':               'D8:D5:B9:00:90:24'

        """
        comm_responce = self._send_http_comm("get_gateway_info")
        return json.loads(comm_responce)

    def get_timezone(self) :
        """
            get current timezone configuration

            On Success returns dict with the value :
               'timezone_localTime':    '1394527011'
               'timezone_olsonName':    'UTC/GMT'
               'timezone_status':       '2'
               'timezone_utcOffset':    'UTC'
               'timezone_utcTime':      '1394527011'
               'timezone_status':       'success'

        """
        comm_responce = self._send_http_comm("get_timezone")
        return json.loads(comm_responce)

    def get_time_source(self, macid=None) :
        """
            get time source for device

            On Success returns dict with value 'internet' or 'meter' :
               'time_source':           'internet'
        """
        comm_responce = self._send_http_comm("get_time_source")
        return json.loads(comm_responce)

    def get_remote_management(self) :
        return self.get_device_config(self)

    def set_remote_management(self, macid=None, status="on") :
        """ set_remote_management
            enabling ssh & vpn

            args:
                status          on|off

            On Success returns dict with value :
                'remote_management_status':     'success'

        """
        if status not in ['on', 'off'] :
            raise ValueError("set_remote_management status must be 'on' or 'off'")
        comm_responce = self._send_http_comm("set_remote_management", Status=status)
        return json.loads(comm_responce)


    def set_time_source(self, macid=None, source=None) :
        """ set_time_source
            set time source

            args:
                source          meter|internet

            On Success returns dict with value :
                'set_time_source_status':       u'success'

            On Error returns dict with value :
                'set_time_source_status':       'invalid source name'
        """
        if source not in ['meter', 'internet'] :
            raise ValueError("set_time_source Source must be 'meter' or 'internet'")
        comm_responce = self._send_http_comm("set_time_source", Source=source)
        return json.loads(comm_responce)

    def get_price(self) :
        """
            get price for kWh

            On Success returns (example):
                price':         '0.1300'
                price_label':   'Set by User' or '--'
                price_timestamp': '1394524458'
                price_units':   '$'

            returns empty dict on Error
        """
        comm_responce = self._send_http_comm("get_price")
        return json.loads(comm_responce)

    def set_price(self, price) :
        """
            Set price manualy

            args:
                price           Price/kWh

            On Success returns dict with value :
                'set_price_status':     'success'

        """
        if isinstance(price, str) and price.startswith('$') :
            price = float(price.lstrip('$'))

        if not isinstance(price, (int, long, float)) :
            raise ValueError("set_price price arg must me a int, long or float")
        if (price <= 0):
            raise ValueError("set_price price arg greater then 0")

        trailing_digits     = 0
        multiplier          = 1
        while (((price * multiplier) != (floor(price * multiplier))) and (trailing_digits < 7)) :
            trailing_digits += 1
            multiplier *= 10

        price_adj = "{:#x}".format(int(price * multiplier))
        tdigits = "{:#x}".format(trailing_digits)

        comm_responce = self._send_http_comm("set_price",
                        Price=price_adj, TrailingDigits=tdigits)
        return json.loads(comm_responce)


    def set_price_auto(self) :
        """
            Set Price from Meter

            On Success returns dict with value :
                'set_price_status':     'success'
        """
        comm_responce = self._send_http_comm("set_price",
                    Price="0xFFFFFFFF",
                    TrailingDigits="0x00")
        return json.loads(comm_responce)

#    def set_multiplier_divisor(self, multiplier=1, divisor=1) :
#       """
#           set multiplier and divisor manualy
#       """
#       multiplier = _tohex(multiplier, 8)
#       divisor = _tohex(divisor, 8)
#        comm_responce = self._send_http_comm("set_multiplier_divisor", Multiplier=multiplier, Divisor=divisor)
#        return json.loads(comm_responce)

    def factory_reset(self) :
        """
            Factory Reset
        """
        comm_responce = self._send_http_comm("factory_reset")
        return json.loads(comm_responce)


#    def disconnect_meter(self) :
#       """
#           disconnect from Smart Meter
#       """
#       comm_responce = self._send_http_comm("disconnect_meter")
#       return json.loads(comm_responce)


    def cloud_reset(self) :
        """
            cloud_reset : Clear Cloud Configuration

        """
        comm_responce = self._send_http_comm("cloud_reset")
        return json.loads(comm_responce)


    def set_cloud(self, url, authcode="", email="") :
        """
            set cloud Url

            args:
                url           Url for uploader
                authcode
                email

            See also get_uploader() to retrieve current uploader cloud config
        """
        if url.__len__() > 200 :
            raise ValueError("Max URL length is 200 characters long.\n")

        urlp = urlparse(url)

        if urlp.port :
            port = "{:#04x}".format(urlp.port)
        else :
            port = "0x00"

        hostname = urlp.hostname

        if urlp.scheme :
            protocol = urlp.scheme
        else :
            protocol = "http"

        url = urlp.path

        if urlp.username :
            userid = urlp.username
        else :
            userid = ""

        if urlp.password :
            password = urlp.password
        else :
            password = ""

        comm_responce = self._send_http_comm("set_cloud",
                    Provider="manual",
                    Protocol=protocol, HostName=hostname,
                    Url=url, Port=port,
                    AuthCode=authcode, Email=email,
                    UserId=userid, Password=password)

        return json.loads(comm_responce)

# Support functions

    def _connect(self) :
        self.soc = socket.create_connection(
                (self.addr, self.port), self.timeout)

    def _disconnect(self):
        try :
            if self.soc :
                self.soc.close()
                self.soc = False
        except IOError :
            pass

    def _send_http_comm(self, cmd, **kwargs):

	if self.debug :
	    print "\n\n_send_http_comm : ", cmd

        commstr = "<LocalCommand>\n"
        commstr += "<Name>{0!s}</Name>\n".format(cmd)
        commstr += "<MacId>{0!s}</MacId>\n".format(self.macid)
        for k, v in kwargs.items() :
            commstr += "<{0}>{1!s}</{0}>\n".format(k, v)
        commstr += "</LocalCommand>\n"

	if self.debug :
	    print(commstr)

        url = "http://{0}/cgi-bin/cgi_manager".format(self.addr)

        req = urllib2.Request(url, commstr)
        response = urllib2.urlopen(req)
        the_page = response.read()

        return the_page



    def _send_soc_comm(self, cmd, **kwargs):

        if cmd == "set_fast_poll" :
            command_tag = "RavenCommand"
        else :
            command_tag = "LocalCommand"


        commstr = "<{0}>\n ".format(command_tag)
        commstr += "<Name>{0!s}</Name>\n".format(cmd)
        for k, v in kwargs.items() :
            commstr += "<{0}>{1!s}</{0}>\n".format(k, v)
        commstr += "</{0}>\n".format(command_tag)
        replystr = ""
        # buf_list = []

        try:
            self._connect()

            # if cmd == "get_history_data" :
        #       self.soc.settimeout(45)
            self.soc.sendall(commstr)
            if self.debug :
                print "commstr : \n", commstr

            # time.sleep(1)

            while 1 :
                buf = self.soc.recv(1000)
                if not buf:
                    break
                replystr += buf
                #buf_list.append(buf)
            # replystr = ''.join(buf_list)

        except Exception:
            print("Unexpected error:", sys.exc_info()[0])
            print "Error replystr = ", replystr
            replystr = None
        finally:
            self._disconnect()
            if self.debug > 1 :
                print "_send_soc_comm replystr :\n", replystr
            return replystr


# Do nothing
# (syntax check)
#
if __name__ == "__main__":
    import __main__
    print(__main__.__file__)

    print("syntax ok")
    exit(0)
