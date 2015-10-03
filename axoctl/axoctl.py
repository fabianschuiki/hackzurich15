#!/usr/bin/env python2

# ====
# HackZurich15
# AxoCtl
# by T. Richner, F. Schuiki, M. Eppenberger
#

from pyaxo import Axolotl

class AxoCtl(object):
    """
    Implements the Axolotl protocol for a milter for postfix.

    all mail objects look are dicts:
    {
        "to": mail address of recipient
        "from": mail address of sender
        "subject": subject of the mail message
        "headers": dict of other headers for the message
        "body": body of the message
    }

    ToDo:
    - implement queues for thread safety.
    - implement local storage for storing mail during handshake phase
    """

    @contextmanager
    def axo(self, my_id, other_id):
        """
        Access axolotl Database.

        From pyaxo repo.
        """
        a = Axolotl(my_id, dbname=other_id, dbpassphrase=self.dbpassphrase)
        a.loadState(my_id, other_id)
        yield a
        a.saveState()

    def __init__(self, arg):
        super(AxoCtl, self).__init__()

        self.dbpassphrase = "0123456789101112131415"

    def E(self, inmail):
        """
        Function to encrypt an outgoing mail. Also makes a new key request if the partner key is not available.
        """
        contenttype = inmail["contenttype"]
        if contenttype.lower() == "message/x-axomail":
            """
            look up target user
            if exists: encrypt and send
            if not exists:
                send DH init
                put email in local storage
            """
            pass

        elif contenttype.lower() == "message/x-axomail-keyreq":
            """
            should not happen! Only decrypt should receive key requests.
            """
            pass

        elif contenttype.lower() == "message/x-axomail-keyrsp":
            """
            Key response received.
            Take email out of storage and start encrypting with the now established state.
            Send now encrypted mail.
            """
            pass

        else:
            """
            No axolotl mail received. something is wrong
            """
            pass

    def D(self, inmail):
        """
        Function to decrypt an incoming mail. Responds to a key request if necessary.
        """
        contenttype = inmail["contenttype"]
        if contenttype.lower() == "message/x-axomail":
            """
            Regular encrypted mail incoming

            Decrypt with available state and relay.
            """
            pass

        elif contenttype.lower() == "message/x-axomail-keyreq":
            """
            Open own state.
            Respond with own DH part.
            Incorporate sendes state to own.
            """
            pass

        elif contenttype.lower() == "message/x-axomail-keyrsp":
            """
            Should never happen.
            """
            pass

        else:
            """
            No axolotl mail received. something is wrong
            """
            pass
