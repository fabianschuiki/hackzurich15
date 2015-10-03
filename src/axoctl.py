#!/usr/bin/env python2

# ====
# HackZurich15
# AxoCtl
# by T. Richner, F. Schuiki, M. Eppenberger
# ====

from pyaxo import Axolotl
from contextlib import contextmanager
from sendmail import sendmimemail
from email.mime.text import MIMEText
import os
import binascii
import hashlib
import pickle
import sys


class AxoCtl(object):
    """
    Implements the Axolotl protocol for a milter for postfix.

    All mail objects are dictionaries:
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

    data_dir = "axonaut"

    def makeAxolotl(self, my_id):
        return Axolotl(my_id, dbname=self.db_path, dbpassphrase=None)

    @contextmanager
    def axo(self, my_id, other_id):
        """
        Access axolotl Database.

        From pyaxo repo.
        """
        # a = Axolotl(my_id, dbname=other_id+".db", dbpassphrase=self.dbpassphrase)
        a = self.makeAxolotl()
        try:
            a.loadState(my_id, other_id)
            yield a
            a.saveState()
        except:
            yield False
            pass

    def __init__(self):
        super(AxoCtl, self).__init__()

        self.db_path = self.data_dir + "/conversations.db"
        self.handshakes_dir = self.data_dir + "/handshakes"
        self.queues_dir = self.data_dir + "/queues"

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.handshakes_dir):
            os.makedirs(self.handshakes_dir)
        if not os.path.exists(self.queues_dir):
            os.makedirs(self.queues_dir)

    def send_mail(self, mail):
        print "would send mail %s" % mail

    def process_outbound(self, in_mail):
        """
        Function to encrypt an outgoing mail. Also makes a new key request if the partner key is not available.
        """

        # Look for a content type header that indicates what to do with this
        # message.
        content_type = None
        for k, v in in_mail["headers"]:
            if k.lower() == "content-type":
                content_type = v.lower()
        print "content_type = %s" % content_type
        sys.stdout.flush()
        my_id = in_mail["from"]
        other_id = in_mail["to"]
        print "From %s to %s " % (my_id, other_id)
        sys.stdout.flush()
        conv_hash = hashlib.sha1(my_id + ":" + other_id).hexdigest()
        hskey_path = self.handshakes_dir + "/" + conv_hash
        queue_path = self.queues_dir + "/" + conv_hash
        print "hashed around a bit"
        if content_type != "message/x-axonaut":
            # If this is a message that we are supposed to encode, see whether we
            # already have an established session. If we don't, we need to negotiate
            # keys with our peer first.

            i = 1;
            path = None
            while path == None or os.path.exists(path):
                path = "%s/%04i" % (queue_path, i)
                i = i + 1

            if not os.path.exists(hskey_path):
                a = self.makeAxolotl(my_id)
                print "holy cow, we need to establish a session first"
                # hs = pickle.load(open(hskey_path, "r"))
                # a.state         = hs["state"]
                # a.handshakePKey = hs["pub"]
                # a.handshakeKey  = hs["priv"]
                # print hs

                out_mail_body = "%s\n%s\n%s" % (
                    binascii.b2a_base64(a.state["DHIs"]).strip(),
                    binascii.b2a_base64(a.state["DHRs"]).strip(),
                    binascii.b2a_base64(a.handshakePKey).strip())
                # TODO: send mail and push this message into the queue.
                print "would send keyreq " + out_mail_body

                print "queueing message"
                if not os.path.exists(queue_path):
                    os.makedirs(queue_path)
                pickle.dump(in_mail, open(path, "w"))

                kreq_msg = MIMEText(out_mail_body)
                kreq_msg["From"] = my_id
                kreq_msg["To"] = other_id
                kreq_msg["Subject"] = "Axolotl Key Request"
                kreq_msg["Content-Type"] = "message/x-axonaut+keyreq"
                sendmimemail(kreq_msg)

                pickle.dump({
                    "state": a.state,
                    "pub": a.handshakePKey,
                    "priv": a.handshakeKey
                }, open(hskey_path, "w"))
            else:
                # TODO: try to load the Axolotl state from the database. If it
                # fails, push the message into the queue as well. If the state
                # exists, encrypt and magic shall ensue.
                # if axo.loadState(in_mail["from"], in_mail["to"]) == False:
                try:
                    a = self.makeAxolotl(my_id)
                    a.loadState()
                    print "Kung Fury approves of the existing session"

                    self.send_mail(in_mail)
                    if os.path.isdir(queue_path):
                        for d in os.listdir(queue_path):
                            self.send_mail(pickle.load(open(queue_path + "/" + d)))

                    a.saveState()

                except:
                    print "Kung Fury does not approve, still no session"
                    print "queueing message"
                    if not os.path.exists(queue_path):
                        os.makedirs(queue_path)
                    pickle.dump(in_mail, open(path, "w"))

    def process_inbound(self, in_mail):
        """
        Function to decrypt an incoming mail. Responds to a key request if necessary.
        """

        # Look for a content type header that indicates what to do with this
        # message.
        content_type = None
        for k, v in in_mail["headers"]:
            if k.lower() == "content-type":
                content_type = v.lower()

        print "content_type = %s" % content_type
        print "Got: %s" % in_mail
        sys.stdout.flush()

        my_id = in_mail["to"]
        other_id = in_mail["from"]

        hskey_path = self.handshakes_dir + "/" + hashlib.sha1(my_id + ":" + other_id).hexdigest()

        if content_type == "message/x-axonaut+keyrsp":
            a = self.makeAxolotl(my_id)
            hs = pickle.load(open(hskey_path, "r"))
            a.state = hs["state"]
            a.handshakePKey = hs["pub"]
            a.handshakeKey = hs["priv"]

            segments = in_mail["body"].split('\n')
            DHIs = segments[0]
            DHRs = segments[1]
            handshakePKey = segments[2]
            a.initState(other_id, DHIs, handshakePKey, DHRs, verify=False)

            # TODO: Flush the queue and encrypt all pending messages, like a sir

            a.saveState();

        elif content_type == "message/x-axonaut+keyreq":
            segments = in_mail["body"].split('\n')
            DHIs = segments[0]
            DHRs = segments[1]
            handshakePKey = segments[2]

            a = self.makeAxolotl(my_id)
            try:
                a.loadState()
                print "received keyreq even though conversation is already open"
            except:
                a.initState(other_id, DHIs, handshakePKey, DHRs, verify=False)

                out_mail_body = "%s\n%s\n%s" % (
                    binascii.b2a_base64(a.state["DHIs"]).strip(),
                    binascii.b2a_base64(a.state["DHRs"]).strip(),
                    binascii.b2a_base64(a.handshakePKey).strip())

                print "send keyrsp " + out_mail_body
                krsp_msg = MIMEText(out_mail_body)
                krsp_msg["From"] = my_id
                krsp_msg["To"] = other_id
                krsp_msg["Subject"] = "Axolotl Key Response"
                krsp_msg["Content-Type"] = "message/x-axonaut+keyrsp"
                sendmimemail(krsp_msg)
                a.saveState()

    return

    contenttype = in_mail["contenttype"]
    if contenttype.lower() == "message/x-axonaut":
        """
        Regular encrypted mail incoming

        Decrypt with available state and relay.
        """
        pass

    elif contenttype.lower() == "message/x-axonaut-keyreq":
        """
        Open own state.
        Respond with own DH part.
        Incorporate sendes state to own.
        """
        pass

    elif contenttype.lower() == "message/x-axonaut-keyrsp":
        """
        Should never happen.
        """
        pass

    else:
        """
        No axolotl mail received. something is wrong
        """
        pass
