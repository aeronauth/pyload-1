# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OneFichierCom(SimpleHoster):
    __name__    = "OneFichierCom"
    __type__    = "hoster"
    __version__ = "0.66"

    __pattern__ = r'https?://(?P<ID>\w+)\.(?P<HOST>(1fichier|d(es)?fichiers|pjointe)\.(com|fr|net|org)|(cjoint|mesfichiers|piecejointe|oi)\.(org|net)|tenvoi\.(com|org|net)|dl4free\.com|alterupload\.com|megadl\.fr)'

    __description__ = """1fichier.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("the-razer", "daniel_ AT gmx DOT net"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("imclem", None),
                       ("stickell", "l.stickell@yahoo.it"),
                       ("Elrick69", "elrick69[AT]rocketmail[DOT]com")]


    NAME_PATTERN = r'>FileName :</td>\s*<td.*>(?P<N>.+?)<'
    SIZE_PATTERN = r'>Size :</td>\s*<td.*>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'File not found !\s*<'

    URL_REPLACEMENTS = [(__pattern__, r'http://\g<ID>.\g<HOST>/en/')]

    WAIT_PATTERN = r'>You must wait (\d+)'


    def setup(self):
        self.multiDL = self.premium
        self.resumeDownload = True


    def handleFree(self):
        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            wait_time = int(m.group(1))
            self.logInfo(_("You have to wait been each free download"), _("Retrying in %d minutes") % wait_time)
            self.wait(wait_time * 60, True)
            self.retry()

        url, inputs = self.parseHtmlForm('action="http://1fichier.com/\?%s' % self.info['ID'])
        if not url:
            self.error(_("Download link not found"))

        # Check for protection
        if "pass" in inputs:
            inputs['pass'] = self.getPassword()
        inputs['submit'] = "Download"

        self.download(url, post=inputs)

        # Check download
        self.checkDownloadedFile()


    def handlePremium(self):
        url, inputs = self.parseHtmlForm('action="http://1fichier.com/\?%s' % self.info['ID'])
        if not url:
            self.error(_("Download link not found"))

        # Check for protection
        if "pass" in inputs:
            inputs['pass'] = self.getPassword()
        inputs['submit'] = "Download"

        self.download(url, post=inputs)

        # Check download
        self.checkDownloadedFile()


    def checkDownloadedFile(self):
        check = self.checkDownload({'wait': self.WAIT_PATTERN})
        if check == "wait":
            wait_time = int(self.lastcheck.group(1)) * 60
            self.wait(wait_time, True)
            self.retry()


getInfo = create_getInfo(OneFichierCom)
