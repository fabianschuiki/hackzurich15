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
import shutil
import time


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


    def log(self, msg):
        t = time.strftime("%H:%M:%S")
        sys.stdout.write("[%s] axoctl: %s\n" % (t, msg))
        sys.stdout.flush()

    def err(self, msg):
        t = time.strftime("%H:%M:%S")
        sys.stderr.write("[%s] axoctl: \033[31;1m*** error\033[0m %s\n" % (t, msg))
        sys.stderr.flush()


    def makeAxolotl(self, my_id):
        return Axolotl(my_id, dbname=self.db_path, dbpassphrase=None)

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


    def encrypt_and_send_mail(self, mail, axolotl):
        self.log("encrypting message %s" % mail["id"])

        # Assemble the message that we shall encrypt.
        msg = MIMEText(mail["body"])
        for k,v in mail["headers"]:
            msg[k] = v
        raw = msg.as_string()

        # Encrypt the message and wrap it up in a new envelope, then send it to
        # the recipient.
        encoded = binascii.b2a_base64(raw)
        menv = MIMEText(encoded)
        menv["From"]         = mail["from"]
        menv["To"]           = mail["to"]
        menv["Subject"]      = "Axolotl-encrypted Message"
        menv["Content-Type"] = "message/x-axonaut"
        sendmimemail(menv, mail["from"], mail["to"])


    def decrypt_and_send_mail(self, mail, axolotl):
        self.log("decrypting message %s" % mail["id"])

        # Decrypt the message from the envelope and forward it.
        decoded = binascii.a2b_base64(mail["body"])
        sendrawmail(decoded, mail["from"], mail["to"])


    def process_outbound(self, in_mail):
        """
        Function to encrypt an outgoing mail. Also makes a new key request if the partner key is not available.
        """

        my_id = in_mail["from"]
        other_id = in_mail["to"]
        self.log("outbound mail from %s to %s" % (my_id, other_id))

        # Look for a content type header that indicates what to do with this
        # message.
        content_type = None
        for k, v in in_mail["headers"]:
            kl = k.lower()
            if kl == "content-type":
                content_type = v.lower()
            if kl == "message-id":
                in_mail["id"] = v

        self.log("content_type = %s" % content_type)
        self.log("message_id = %s" % in_mail["id"])

        conv_hash = hashlib.sha1(my_id + ":" + other_id).hexdigest()
        hskey_path = self.handshakes_dir + "/" + conv_hash
        queue_path = self.queues_dir + "/" + conv_hash

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
                self.log("sending keyreq to %s" % other_id)
                a = self.makeAxolotl(my_id)
                # hs = pickle.load(open(hskey_path, "r"))
                # a.state         = hs["state"]
                # a.handshakePKey = hs["pub"]
                # a.handshakeKey  = hs["priv"]
                # print hs

                out_mail_body = "%s\n%s\n%s" % (
                    binascii.b2a_base64(a.state["DHIs"]).strip(),
                    binascii.b2a_base64(a.state["DHRs"]).strip(),
                    binascii.b2a_base64(a.handshakePKey).strip())
                print "would send keyreq " + out_mail_body

                self.log("queuing message %s" % in_mail["id"])
                if not os.path.exists(queue_path):
                    os.makedirs(queue_path)
                pickle.dump(in_mail, open(path, "w"))

                kreq_msg = MIMEText(out_mail_body)
                kreq_msg["From"] = my_id
                kreq_msg["To"] = other_id
                kreq_msg["Subject"] = "Axolotl Key Request"
                kreq_msg["Content-Type"] = "message/x-axonaut+keyreq"
                sendmimemail(kreq_msg, my_id, other_id)

                pickle.dump({
                    "state": a.state,
                    "pub": a.handshakePKey,
                    "priv": a.handshakeKey
                }, open(hskey_path, "w"))

            else:
                try:
                    a = self.makeAxolotl(my_id)
                    a.loadState(my_id, other_id)
                    self.encrypt_and_send_mail(in_mail, a)
                    a.saveState()

                except:
                    self.log("queuing message %s (key response pending)" % in_mail["id"])
                    if not os.path.exists(queue_path):
                        os.makedirs(queue_path)
                    pickle.dump(in_mail, open(path, "w"))


    def process_inbound(self, in_mail):
        """
        Function to decrypt an incoming mail. Responds to a key request if necessary.
        """

        my_id = in_mail["to"]
        other_id = in_mail["from"]
        self.log("inbound mail from %s to %s" % (my_id, other_id))

        # Look for a content type header that indicates what to do with this
        # message.
        content_type = None
        for k, v in in_mail["headers"]:
            kl = k.lower()
            if kl == "content-type":
                content_type = v.lower()
            if kl == "message-id":
                in_mail["id"] = v

        self.log("content_type = %s" % content_type)
        self.log("message_id = %s" % in_mail["id"])

        conv_hash = hashlib.sha1(my_id + ":" + other_id).hexdigest()
        hskey_path = self.handshakes_dir + "/" + conv_hash
        queue_path = self.queues_dir + "/" + conv_hash

        # Encrypted messages need to be decrypted.
        if content_type == "message/x-axonaut":
            try:
                a = self.makeAxolotl(my_id)
                a.loadState(my_id, other_id)
                self.decrypt_and_send_mail(in_mail, a)
                a.saveState()
            except Exception as e:
                self.err("unable to decrypt message: %s" % e)

                # TODO: Send response that decryption is not possible due to lack of
                # established session.

        elif content_type == "message/x-axonaut+keyrsp":
            self.log("received keyrsp from %s" % other_id)

            a = self.makeAxolotl(my_id)
            hs = pickle.load(open(hskey_path, "r"))
            a.state = hs["state"]
            a.handshakePKey = hs["pub"]
            a.handshakeKey = hs["priv"]

            segments = in_mail["body"].split('\n')
            DHIs = binascii.a2b_base64(segments[0].strip())
            DHRs = binascii.a2b_base64(segments[1].strip()) if segments[1].strip() != "none" else None
            handshakePKey = binascii.a2b_base64(segments[2].strip())
            a.initState(other_id, DHIs, handshakePKey, DHRs, verify=False)

            if os.path.isdir(queue_path):
                for d in os.listdir(queue_path):
                    msg = pickle.load(open(queue_path+"/"+d))
                    self.encrypt_and_send_mail(msg, a)
                shutil.rmtree(queue_path)

            a.saveState();

        elif content_type == "message/x-axonaut+keyreq":
            try:
                segments = in_mail["body"].split('\n')
                DHIs = binascii.a2b_base64(segments[0].strip())
                DHRs = binascii.a2b_base64(segments[1].strip())
                handshakePKey = binascii.a2b_base64(segments[2].strip())
                self.log("received keyreq from %s" % other_id)
            except Exception as e:
                self.err("invalid keyreq received: %s" % e)
                return

            a = self.makeAxolotl(my_id)
            try:
                a.loadState(my_id, other_id)
                self.err("received keyreq event though already exchanged")
            except:
                a.initState(other_id, DHIs, handshakePKey, DHRs, verify=False)
                out_mail_body = "%s\n%s\n%s" % (
                    binascii.b2a_base64(a.state["DHIs"]).strip(),
                    binascii.b2a_base64(a.state["DHRs"]).strip() if a.state["DHRs"] != None else "none",
                    binascii.b2a_base64(a.handshakePKey).strip())

                self.log("sending keyrsp to %s" % other_id)
                krsp_msg = MIMEText(out_mail_body)
                krsp_msg["From"] = my_id
                krsp_msg["To"] = other_id
                krsp_msg["Subject"] = "Axolotl Key Response"
                krsp_msg["Content-Type"] = "message/x-axonaut+keyrsp"
                sendmimemail(krsp_msg, my_id, other_id)
                a.saveState()

        return
