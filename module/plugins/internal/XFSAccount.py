# -*- coding: utf-8 -*-

import re

from urlparse import urljoin
from time import gmtime, mktime, strptime

from module.plugins.Account import Account
from module.plugins.internal.SimpleHoster import parseHtmlForm, set_cookies


class XFSAccount(Account):
    __name__    = "XFSAccount"
    __type__    = "account"
    __version__ = "0.23"

    __description__ = """XFileSharing account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    """
    Following patterns should be defined by each hoster:

      HOSTER_URL: (optional)
        example: HOSTER_URL = r'linestorage.com'

      PREMIUM_PATTERN: (optional) Checks if the account is premium
        example: PREMIUM_PATTERN = r'>Renew premium'
    """

    HOSTER_DOMAIN = None

    COOKIES = [(HOSTER_DOMAIN, "lang", "english")]  #: or list of tuples [(domain, name, value)]

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire:.*?(\d{1,2} [\w^_]+ \d{4})'

    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:.*?<b>\s*(?P<S>[\d.,]+|[Uu]nlimited)\s*(?:(?P<U>[\w^_]+)\s*)?</b>'
    TRAFFIC_LEFT_UNIT = "MB"  #: used only if no group <U> was found

    LOGIN_FAIL_PATTERN = r'>(Incorrect Login or Password|Error<)'


    def __init__(self, manager, accounts):  #@TODO: remove in 0.4.10
        self.init()
        return super(XFSAccount, self).__init__(manager, accounts)


    def init(self):
        # if not self.HOSTER_DOMAIN:
            # self.fail(_("Missing HOSTER_DOMAIN"))

        if not hasattr(self, "HOSTER_URL"):
            self.HOSTER_URL = "http://www.%s/" % self.HOSTER_DOMAIN.replace("www.", "", 1)


    def loadAccountInfo(self, user, req):
        html = req.load(self.HOSTER_URL, get={'op': "my_account"}, decode=True)

        validuntil = None
        trafficleft = None
        premium = None

        if hasattr(self, "PREMIUM_PATTERN"):
            premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%d %B %Y"))
            except Exception, e:
                self.logError(str(e))
            else:
                if validuntil > mktime(gmtime()):
                    premium = True
                else:
                    if premium is False:  #: registered account type (not premium)
                        validuntil = -1
                    premium = False

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            try:
                traffic = m.groupdict()
                if "nlimited" in traffic['S']:
                    trafficleft = -1
                    if premium is None:
                        premium = True
                else:
                    if 'U' in traffic:
                        unit = traffic['U']
                    elif isinstance(self.TRAFFIC_LEFT_UNIT, basestring):
                        unit = self.TRAFFIC_LEFT_UNIT
                    else:
                        unit = ""

                    trafficleft = self.parseTraffic(traffic['S'] + unit)

            except Exception, e:
                self.logDebug(str(e))

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium or False}


    def login(self, user, data, req):
        if isinstance(self.COOKIES, list):
            set_cookies(req.cj, self.COOKIES)

        url = urljoin(self.HOSTER_URL, "login.html")
        html = req.load(url, decode=True)

        action, inputs = parseHtmlForm('name="FL"', html)
        if not inputs:
            inputs = {'op': "login",
                      'redirect': self.HOSTER_URL}

        inputs.update({'login': user,
                       'password': data['password']})

        html = req.load(self.HOSTER_URL, post=inputs, decode=True)

        if re.search(self.LOGIN_FAIL_PATTERN, html):
            self.wrongPassword()
