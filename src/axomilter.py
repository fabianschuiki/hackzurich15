#!/usr/bin/python2.7

# Very Doc: https://stuffivelearned.org/doku.php?id=programming:python:python-libmilter

import sys
import os
import argparse
import libmilter as lm
import sys, time

import StringIO

HOST = "example.com"

CT_AXOMAIL = "message/x-axonaut"


# Create our milter class with the forking mixin and the regular milter
# protocol base classes
class AxoMilter(lm.ForkMixin, lm.MilterProtocol):
    def __init__(self, opts=0, protos=0):
        # We must init our parents here
        lm.MilterProtocol.__init__(self, opts, protos)
        lm.ForkMixin.__init__(self)
        # You can initialize more stuff here
        self.m_header = []
        self.m_body = ""
        self.m_from = ""
        self.m_to = ""
        self.is_axotype = False

    def log(self, msg):
        t = time.strftime('%H:%M:%S')
        print '[%s] %s' % (t, msg)
        sys.stdout.flush()

    @lm.noReply
    def connect(self, hostname, family, ip, port, cmdDict):
        self.log('Connect from %s:%d (%s) with family: %s' % (ip, port,
                                                              hostname, family))
        return lm.CONTINUE

    @lm.noReply
    def helo(self, heloname):
        self.log('HELO: %s' % heloname)
        return lm.CONTINUE

    @lm.noReply
    def mailFrom(self, frAddr, cmdDict):
        self.log('MAIL: %s' % frAddr)
        self.m_from = frAddr
        return lm.CONTINUE

    @lm.noReply
    def rcpt(self, recip, cmdDict):
        self.log('RCPT: %s' % recip)
        self.m_to = recip
        return lm.CONTINUE

    @lm.noReply
    def header(self, key, val, cmdDict):
        self.log('%s: %s' % (key, val))

        # save dat headers
        self.m_header.append((key, val))

        if key.lower() == "content-type" and val.startswith(CT_AXOMAIL):
            self.is_axotype = True

        return lm.CONTINUE

    @lm.noReply
    def eoh(self, cmdDict):
        self.log('EOH')
        return lm.CONTINUE

    def data(self, cmdDict):
        self.log('DATA')
        return lm.CONTINUE

    @lm.noReply
    def body(self, chunk, cmdDict):
        self.log('Body chunk: %d' % len(chunk))
        # save stuff in memory :)
        self.m_body += chunk;
        return lm.CONTINUE

    def eob(self, cmdDict):
        self.log('EOB')
        mail = {'from': self.m_from, 'to': self.m_header, 'headers': self.m_header, 'body': self.m_body}
        action = lm.DISCARD
        if is_local(self.m_from, self.m_to):
            self.log("LOCAL")
            action = lm.CONTINUE
        elif is_inbound(self.m_from, self.m_to):
            self.log("INBOUND")
            if self.is_axotype:
                self.log("AXONAUT - decrypting")
                # decrypt if axolotl
                # plainmail = axoctl.process_inbound(mail)
                self.replBody(plainmail['body'])
                action = lm.CONTINUE

            else:
                self.log("LEGACY MAIL - forwarding")
                action = lm.CONTINUE  # legacy mails?
        elif is_outbound(self.m_from, self.m_to):
            self.log("OUTBOUND")
            if self.is_axotype:
                self.log("AXONAUT - nice, job already done, forward")
                action = lm.CONTINUE
            else:
                self.log("AXONAUT - encrypt")
                # Encrypt dat shit!
                # cyphermail = axoctl.process_outbound(mail)
                action = lm.DISCARD
        else:
            self.log("WHAT A TERRIBLE FAILURE :'(")

        # self.setReply('554' , '5.7.1' , 'Rejected because I said so')
        return action

    def close(self):
        self.log('Close called. QID: %s' % self._qid)


def host():
    with open('HOST', 'r') as content_file:
        hostname = content_file.read().strip()
    return hostname


def extract_host(mail):
    return mail.rsplit('@', 1)[1]


def is_local(m_from, m_to):
    fhost = extract_host(m_from)
    thost = extract_host(m_to)
    return (fhost == HOST) and (thost == HOST)


def is_inbound(m_from, m_to):
    fhost = extract_host(m_from)
    thost = extract_host(m_to)
    return (not (fhost == HOST)) and (thost == HOST)


def is_outbound(m_from, m_to):
    fhost = extract_host(m_from)
    thost = extract_host(m_to)
    return (fhost == HOST) and (not (thost == HOST))


def main():
    import signal, traceback
    global HOST

    HOST = host()
    # We can set our milter opts here
    opts = lm.SMFIF_CHGFROM | lm.SMFIF_ADDRCPT | lm.SMFIF_QUARANTINE | lm.SMFIF_ADDHDRS | lm.SMFIF_CHGBODY

    # We initialize the factory we want to use (you can choose from an
    # AsyncFactory, ForkFactory or ThreadFactory.  You must use the
    # appropriate mixin classes for your milter for Thread and Fork)
    f = lm.ForkFactory('inet:127.0.0.1:5000', AxoMilter, opts)

    def sigHandler(num, frame):
        print "Good bye!"
        f.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigHandler)
    try:
        # run it
        f.run()
    except Exception, e:
        f.close()
        print >> sys.stderr, 'EXCEPTION OCCURED: %s' % e
        traceback.print_tb(sys.exc_traceback)
        sys.exit(3)


if __name__ == '__main__':
    main()
