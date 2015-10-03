#!/usr/bin/python2.7

""" Mail Filter (milter) to hook into an smtp server """

# ====
# HackZurich15
# AxoMilter
# by T. Richner, F. Schuiki, M. Eppenberger
# ====

# Very Doc: https://stuffivelearned.org/doku.php?id=programming:python:python-libmilter
import libmilter as lm
import sys
from axoctl import AxoCtl
import traceback

from log import new_logger
import logging

HOST = "example.com"

CT_AXOMAIL = "message/x-axonaut"
RQ_AXOMAIL = "[AXONAUT]"


# Create our milter class with the forking mixin and the regular milter
# protocol base classes
class AxoMilter(lm.ThreadMixin, lm.MilterProtocol):
    """
    Implements a milter (mail filter) to support transparent
    first MTA to last MTA encryption. This uses the axolotl security protocol,
    which has nice security properties such as:
    - Perfect Forward Secrecy (PFS)
    - plausible deniability
    - confidentiality, (authenticity/integrity)
    """

    def __init__(self, opts=0, protos=0):
        # We must init our parents here
        lm.MilterProtocol.__init__(self, opts, protos)
        lm.ThreadMixin.__init__(self)
        # You can initialize more stuff here
        self.m_header = []
        self.m_body = ""
        self.m_from = ""
        self.m_to = ""
        self.is_axotype = False
        self.rq_axo = False
        logger.info(" ---- >8 ---- ")

    @lm.noReply
    def connect(self, hostname, family, ip, port, cmdDict):
        logger.debug('Connect from %s:%d (%s) with family: %s' % (ip, port,
                                                                  hostname, family))
        return lm.CONTINUE

    @lm.noReply
    def helo(self, heloname):
        logger.info('HELO: %s' % heloname)
        return lm.CONTINUE

    @lm.noReply
    def mailFrom(self, frAddr, cmdDict):
        logger.info('FROM: %s' % frAddr)
        self.m_from = frAddr
        return lm.CONTINUE

    @lm.noReply
    def rcpt(self, recip, cmdDict):
        logger.info('RCPT: %s' % recip)
        self.m_to = recip
        return lm.CONTINUE

    @lm.noReply
    def header(self, key, val, cmdDict):
        logger.debug('%s: %s' % (key, val))

        # save dat headers
        self.m_header.append((key, val))

        if key.lower() == "content-type" and val.startswith(CT_AXOMAIL):
            self.is_axotype = True

        if key.lower() == "subject" and val.startswith(RQ_AXOMAIL):
            self.rq_axo = True

        return lm.CONTINUE

    @lm.noReply
    def eoh(self, cmdDict):
        logger.debug('EOH')
        return lm.CONTINUE

    def data(self, cmdDict):
        logger.debug('DATA')
        return lm.CONTINUE

    @lm.noReply
    def body(self, chunk, cmdDict):
        logger.debug('Body chunk: %d' % len(chunk))
        # save stuff in memory :)
        self.m_body += chunk;
        return lm.CONTINUE

    def eob(self, cmdDict):
        logger.debug('EOB')
        mail = {'from': self.m_from, 'to': self.m_to, 'headers': self.m_header, 'body': self.m_body}
        action = lm.DISCARD
        # Mux mail, what is the appropriate action?
        if is_local(self.m_from, self.m_to):
            logger.info("LOCAL")
            action = lm.CONTINUE
        elif is_inbound(self.m_from, self.m_to):
            logger.info("INBOUND")
            if self.is_axotype:
                logger.info("AXONAUT - decrypting")
                # decrypt if axolotl
                try:
                    AxoCtl(logger).process_inbound(mail)
                except Exception as e:
                    print("Error: %s" % e)
                    traceback.print_exc()
                action = lm.DISCARD

            else:
                logger.info("LEGACY MAIL - forwarding")
                action = lm.CONTINUE  # legacy mails?
        elif is_outbound(self.m_from, self.m_to):
            logger.info("OUTBOUND")
            if self.is_axotype:
                logger.info("AXONAUT - nice, job already done, forward")
                action = lm.CONTINUE
            elif self.rq_axo:
                logger.info("AXONAUT - axorq -> encrypt!")
                # Encrypt dat shit!
                AxoCtl(logger).process_outbound(mail)
                # axoctl.process_outbound(mail)
                action = lm.DISCARD
            else:
                logger.info("AXONAUT - norq, encrypt it anyway")
                # Encrypt it with less euphoria
                # axoctl.process_outbound(mail)
                AxoCtl(logger).process_outbound(mail)
                action = lm.DISCARD
        else:
            logger.error("WHAT A TERRIBLE FAILURE :'(")
            logger.error("Did you set up the HOST file correctly?")

        # self.setReply('554' , '5.7.1' , 'Rejected because I said so')
        return action

    def close(self):
        logger.debug('Close called. QID: %s' % self._qid)


# Reads the HOST file, necessary to figure out if a mail is in- or outbound
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
    logger.debug("Reading HOST file.")
    HOST = host()
    # We can set our milter opts here
    opts = lm.SMFIF_CHGFROM | lm.SMFIF_ADDRCPT | lm.SMFIF_QUARANTINE | lm.SMFIF_ADDHDRS | lm.SMFIF_CHGBODY

    # We initialize the factory we want to use (you can choose from an
    # AsyncFactory, ForkFactory or ThreadFactory.  You must use the
    # appropriate mixin classes for your milter for Thread and Fork)
    logger.debug("Setting up ForkFactory")
    f = lm.ThreadFactory('inet:127.0.0.1:5000', AxoMilter, opts)

    def sigHandler(num, frame):
        logger.info("Good bye!")
        f.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigHandler)
    try:
        # run it
        logger.debug("Magic Milter ready to go.")
        sys.stdout.flush()
        f.run()
    except Exception, e:
        f.close()
        logger.exception("Whut just happenend?!? o.O")
        traceback.print_tb(sys.exc_traceback)
        sys.exit(3)


logger = new_logger('milter', logging.DEBUG)

if __name__ == '__main__':
    main()
