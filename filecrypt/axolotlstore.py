import os

class AxolotlStore:
	"""LOL"""

	def __init__(self, path):
		self.path = path
		if not os.path.exists(path):
			os.makedirs(path)

	def setIdentityKeyPair(self, ikp):
		pickle.dump([ikp.getPublicKey().serialize(), ikp.getPrivateKey().serialize()], open(self.path+"/identity_key_pair", "w"))

	def getIdentityKeyPair(self):
		lst = pickle.load(open(self.path+"/identity_key_pair", "r"))
		return None
