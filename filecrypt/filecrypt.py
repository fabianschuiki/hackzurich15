#!/usr/bin/python
# from axolotl.util.keyhelper import KeyHelper
import sys
import pickle
import os.path
from axolotlstore import AxolotlStore
from axolotl.util.keyhelper import KeyHelper
import yowsup.layers.axolotl.store.sqlite

STATE_PATH = "axolotl.db"
STORE_PATH = "axolotl"

if len(sys.argv) < 2:
	sys.stderr.write("usage: %s reset\n" % sys.argv[0])
	exit(1)
cmd = sys.argv[1]
args = sys.argv[2:]

class AxolotlState:
	"""Axolotl state kept on record locally for communication"""
	countPreKeys = None
	identityKeyPair = None
	registrationId = None
	preKeys = None
	signedPreKey = None




# store = AxolotlStore("axolotl")



# state = None
# if os.path.exists(STATE_PATH) and cmd != "reset":
# 	state = pickle.load(open(STATE_PATH, "r"))
# else:
# 	print "creating state in %s" % STATE_PATH
# 	state = AxolotlState()
# 	state.countPreKeys    = 200
# 	identityKeyPair = KeyHelper.generateIdentityKeyPair()
# 	state.registrationId  = KeyHelper.generateRegistrationId()
# 	state.preKeys         = KeyHelper.generatePreKeys(KeyHelper.getRandomSequence(), state.countPreKeys)
# 	state.signedPreKey    = KeyHelper.generateSignedPreKey(state.identityKeyPair, KeyHelper.getRandomSequence(65536))

# 	# pickle.dump(state, open(STATE_PATH, "w"))

# if cmd == "reset":
# 	exit(0)

# print state.identityKeyPair
# print state.registrationId
# print state.preKeys
# print state.signedPreKey
