#!/usr/bin/env python2

# ====
# HackZurich15
# AxoCtl
# by T. Richner, F. Schuiki, M. Eppenberger
# ====

from pyaxo import Axolotl
from contextlib import contextmanager
from sendmail import sendmimemail, sendrawmail
from email.mime.text import MIMEText
import os
import binascii
import hashlib
import pickle
import sys
import shutil
import time

from log import new_logger
import logging


def ensure_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

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

    def __init__(self, logger=None):
        super(AxoCtl, self).__init__()

        self.db_path = self.data_dir + "/conversations.db"
        self.handshakes_dir = self.data_dir + "/handshakes"
        self.queues_dir = self.data_dir + "/queues"
        self.logger = new_logger('axonaut',logging.DEBUG) if logger == None else logger

        dirs = [self.data_dir,self.handshakes_dir,self.queues_dir];
        for d in dirs:
            ensure_dir(d)

    def encrypt_and_send_mail(self, mail, axolotl):
        self.logger.info("encrypting message %s" % mail["id"])

        # Assemble the message that we shall encrypt.
        msg = MIMEText(mail["body"])
        for k,v in mail["headers"]:
            msg[k] = v
        raw = msg.as_string()

        # Encrypt the message and wrap it up in a new envelope, then send it to
        # the recipient.
        encoded = binascii.b2a_base64(axolotl.encrypt(raw))
        menv = MIMEText(encoded)
        menv["From"]         = mail["from"]
        menv["To"]           = mail["to"]
        menv["Subject"]      = "Axolotl-encrypted Message"
        menv["Content-Type"] = "message/x-axonaut"
        sendmimemail(menv, mail["from"], mail["to"])


    def decrypt_and_send_mail(self, mail, axolotl):
        self.logger.info("decrypting message %s" % mail["id"])

        # Decrypt the message from the envelope and forward it.
        decoded = axolotl.decrypt(binascii.a2b_base64(mail["body"]))
        sendrawmail(decoded, mail["from"], mail["to"])


    # Called for every message that arrives at the server bound for an external
    # recipient.
    def process_outbound(self, in_mail):
        """
        Function to encrypt an outgoing mail. Also makes a new key request if the partner key is not available.
        """

        my_id = in_mail["from"]
        other_id = in_mail["to"]
        self.logger.info("outbound mail from %s to %s" % (my_id, other_id))

        content_type = None
        for k, v in in_mail["headers"]:
            kl = k.lower()
            if kl == "content-type":
                content_type = v.lower()
            if kl == "message-id":
                in_mail["id"] = v

        self.logger.debug("content_type = %s" % content_type)
        self.logger.debug("message_id = %s" % in_mail["id"])

        conv_hash = hashlib.sha1(my_id + ":" + other_id).hexdigest()
        handshake_path = self.handshakes_dir + "/" + conv_hash
        queue_path = self.queues_dir + "/" + conv_hash

        # Encrypt all messages that are not already encrypted.
        if content_type != "message/x-axonaut":

            # Figure out the next queue file name in case we need to keep the
            # message around for later delivery.
            i = 1;
            path = None
            while path == None or os.path.exists(path):
                path = "%s/%04i" % (queue_path, i)
                i = i + 1

            # Check whether we already have established a handshake. If this is
            # not the case, send a keyreq message to the recipient that contains
            # our half of the key exchange information. The message that was
            # originally intended for dispatch is stored in a queue for later
            # delivery as soon as the encryption keys have been negotiated.
            if not os.path.exists(handshake_path):
                self.logger.debug("sending keyreq to %s" % other_id)
                a = self.makeAxolotl(my_id)

                out_mail_body = "%s\n%s\n%s" % (
                    binascii.b2a_base64(a.state["DHIs"]).strip(),
                    binascii.b2a_base64(a.state["DHRs"]).strip(),
                    binascii.b2a_base64(a.handshakePKey).strip())

                self.logger.debug("queuing message %s" % in_mail["id"])
                if not os.path.exists(queue_path):
                    os.makedirs(queue_path)
                pickle.dump(in_mail, open(path, "w"))

                kreq_msg = MIMEText(out_mail_body)
                kreq_msg["From"] = my_id
                kreq_msg["To"] = other_id
                kreq_msg["Subject"] = "Axolotl Key Request"
                kreq_msg["Content-Type"] = "message/x-axonaut+keyreq"
                sendmimemail(kreq_msg, my_id, other_id)

                # The following is an ugly hack: pyaxo expects an Axolotl object
                # to be created and the keys negotiated before the object is
                # destroyed and the state saved to disk. This does not work in
                # our case, since we need to wait for a potentially long period
                # of time until we can finalize the handshake. Therefore we
                # serialize the Axolotl state and especially the handshake pre-
                # keys to disk, such that we may resume the handshake at a later
                # stage.
                pickle.dump({
                    "state": a.state,
                    "pub": a.handshakePKey,
                    "priv": a.handshakeKey
                }, open(handshake_path, "w"))

            else:
                # If we've come this far, the handshake has been initiated. That
                # is, at least the keyreq message has been sent to the peer. Two
                # things may now happen: Either the Axolotl conversation is
                # already initialized, in which case loadState() will succeed
                # and we may continue to encrypt our message. Or the state has
                # not yet been initialized, and an exception is thrown. In case
                # of the exception we store the message in the queue for later
                # encryption, as soon as the handshake terminates.
                try:
                    a = self.makeAxolotl(my_id)
                    a.loadState(my_id, other_id)
                    self.encrypt_and_send_mail(in_mail, a)
                    a.saveState()

                except:
                    self.logger.info("queuing message %s (key response pending)" % in_mail["id"])
                    if not os.path.exists(queue_path):
                        os.makedirs(queue_path)
                    pickle.dump(in_mail, open(path, "w"))


    # Called for every message arriving at the server that is bound for a local
    # recipient.
    def process_inbound(self, in_mail):
        """
        Function to decrypt an incoming mail. Responds to a key request if necessary.
        """

        my_id = in_mail["to"]
        other_id = in_mail["from"]
        self.logger.info("inbound mail from %s to %s" % (my_id, other_id))

        content_type = None
        for k, v in in_mail["headers"]:
            kl = k.lower()
            if kl == "content-type":
                content_type = v.lower()
            if kl == "message-id":
                in_mail["id"] = v

        self.logger.debug("content_type = %s" % content_type)
        self.logger.debug("message_id = %s" % in_mail["id"])

        conv_hash = hashlib.sha1(my_id + ":" + other_id).hexdigest()
        handshake_path = self.handshakes_dir + "/" + conv_hash
        queue_path = self.queues_dir + "/" + conv_hash

        # Encrypted messages targeted at a local user need to be decrypted
        # before they are relayed. The encryption status is indicated by a
        # special content type. Two cases are possible: Either the Axolotl
        # handshake has been completed, in which case loadState() succeeds and
        # the message may be decrypted normally. Or the handshake is in progress
        # or has not been started at all, in which case no decryption is
        # possible. In the latter case, we might want to inform the sender about
        # the situation.
        if content_type == "message/x-axonaut":
            try:
                a = self.makeAxolotl(my_id)
                a.loadState(my_id, other_id)
                self.decrypt_and_send_mail(in_mail, a)
                a.saveState()
            except Exception as e:
                self.logger.exception("unable to decrypt message: %s" % e)

                msg = MIMEMultipart()
                msg["Subject"] = "Message cannot be decrypted, return to sender"
                msg["From"]    = my_id
                msg["To"]      = other_id
                msg.preamble   = "The attached message was received by the sender, but cannot be decrypted. This indicates that no secure Axolotl conversation has been established beforehand."

                raw_msg = MIMEText(mail["body"])
                for k,v in mail["headers"]:
                    raw_msg[k] = v
                raw = raw_msg.as_string()

                mret = MIMEText(raw)
                mret["Content-Type"] = "message/rfc822"
                msg.attach(mret)
                sendmimemail(msg, my_id, other_id)
                # TODO: Send response that decryption is not possible due to
                # lack of established session.


        # If we receive a key response, we have initiated the key exchange and
        # may now finish it with the information provided by our peer. To ensure
        # secrecy, truncate the temporary pre-keys that were stored for the
        # handshake to zero.
        elif content_type == "message/x-axonaut+keyrsp":
            self.logger.debug("received keyrsp from %s" % other_id)

            a = self.makeAxolotl(my_id)
            hs = pickle.load(open(handshake_path, "r"))
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
            open(handshake_path, "w").truncate()


        # If we receive a key request, we are able to finalize the key exchange
        # and initialize the Axolotl state. In addition to that, we have to mark
        # this combination of sender/receiver as established by touching the
        # corresponding file in the handshakes directory.
        elif content_type == "message/x-axonaut+keyreq":
            try:
                segments = in_mail["body"].split('\n')
                DHIs = binascii.a2b_base64(segments[0].strip())
                DHRs = binascii.a2b_base64(segments[1].strip())
                handshakePKey = binascii.a2b_base64(segments[2].strip())
                self.logger.debug("received keyreq from %s" % other_id)
            except Exception as e:
                self.logger.exception("invalid keyreq received: %s" % e)
                return

            try:
                a = self.makeAxolotl(my_id)
                a.loadState(my_id, other_id)
                self.logger.warning("received keyreq event though already exchanged")
            except:
                a = self.makeAxolotl(my_id)
                a.initState(other_id, DHIs, handshakePKey, DHRs, verify=False)
                out_mail_body = "%s\n%s\n%s" % (
                    binascii.b2a_base64(a.state["DHIs"]).strip(),
                    binascii.b2a_base64(a.state["DHRs"]).strip() if a.state["DHRs"] != None else "none",
                    binascii.b2a_base64(a.handshakePKey).strip())

                self.logger.info("sending keyrsp to %s" % other_id)
                krsp_msg = MIMEText(out_mail_body)
                krsp_msg["From"] = my_id
                krsp_msg["To"] = other_id
                krsp_msg["Subject"] = "Axolotl Key Response"
                krsp_msg["Content-Type"] = "message/x-axonaut+keyrsp"
                sendmimemail(krsp_msg, my_id, other_id)
                a.saveState()

                os.mknod(handshake_path)

        return
