#!/usr/bin/env python2

# ====
# HackZurich15
# AxoCtl
# by T. Richner, F. Schuiki, M. Eppenberger
# ====

from pyaxo import Axolotl
from contextlib import contextmanager
import os
import binascii
import hashlib
import pickle


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
		a = makeAxolotl()
		a.loadState(my_id, other_id)
		yield a
		a.saveState()


	def __init__(self):
		super(AxoCtl, self).__init__()

		self.db_path = self.data_dir+"/conversations.db"
		self.handshakes_dir = self.data_dir+"/handshakes"

		if not os.path.exists(self.data_dir):
			os.makedirs(self.data_dir)
		if not os.path.exists(self.handshakes_dir):
			os.makedirs(self.handshakes_dir)


	def E(self, inmail):
		"""
		Function to encrypt an outgoing mail. Also makes a new key request if the partner key is not available.
		"""
		contenttype = inmail["content-type"]
		if contenttype.lower() == "message/x-axonaut":
			"""
			look up target user
			if exists: encrypt and send
			if not exists:
				send DH init
				put email in local storage
			"""
			pass

		elif contenttype.lower() == "message/x-axonaut-keyreq":
			"""
			should not happen! Only decrypt should receive key requests.
			"""
			pass

		elif contenttype.lower() == "message/x-axonaut-keyrsp":
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



	def process_inbound(self, in_mail):
		"""
		Function to decrypt an incoming mail. Responds to a key request if necessary.
		"""

		# Look for a content type header that indicates what to do with this
		# message.
		content_type = None
		for k,v in in_mail["headers"]:
			if k.lower() == "content-type":
				content_type = v.lower()
		print "content_type = %s" % content_type

		# If this is a message that we are supposed to encode, see whether we
		# already have an established session. If we don't, we need to negotiate
		# keys with our peer first.
		my_id = in_mail["from"]
		other_id = in_mail["to"]
		hskey_path = self.handshakes_dir+"/"+hashlib.sha1(my_id+":"+other_id).hexdigest()

		a = self.makeAxolotl(my_id)
		print a.loadState(my_id, other_id)

		if not os.path.exists(self.db_path):
			print "holy cow, we need to establish a session first"
			if not os.path.exists(hskey_path):
				# hs = pickle.load(open(hskey_path, "r"))
				# a.state         = hs["state"]
				# a.handshakePKey = hs["pub"]
				# a.handshakeKey  = hs["priv"]
				# print hs

				out_mail_body = "%s\n%s\n%s" % (
					binascii.b2a_base64(a.state["DHIs"]).strip(),
					binascii.b2a_base64(a.state["DHRs"]).strip(),
					binascii.b2a_base64(a.handshakePKey).strip())

				pickle.dump({
					"state": a.state,
					"pub":   a.handshakePKey,
					"priv":  a.handshakeKey
				}, open(hskey_path, "w"))
		else:
			# if axo.loadState(in_mail["from"], in_mail["to"]) == False:
			print "Kung Fury approves of the existing session"
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
