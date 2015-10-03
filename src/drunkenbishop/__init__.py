import hashlib
from drunkenbishop.Fingerprint import Fingerprint

def GetFPrintMail(mykey, myid, otherkey, otherid):
    
    mykey_hash_str = hashlib.sha256(mykey).hexdigest().upper()
    mykey_hash_list = [int(mykey_hash_str[i:i+8], 16) for i in range(0,len(mykey_hash_str), 8)]

    otherkey_hash_str = hashlib.sha256(otherkey).hexdigest().upper()
    otherkey_hash_list = [int(otherkey_hash_str[i:i+8], 16) for i in range(0,len(otherkey_hash_str), 8)]

    mykey_bishop = str(Fingerprint(mykey_hash_list, myid.split("@")[0], "SHA256"))
    otherkey_bishop = str(Fingerprint(otherkey_hash_list, otherid.split("@")[0], "SHA256"))


    mailtext = """Hello %s
    Your e-mail conversation with %s was encrypted via the Axonaut e-mail
    encryption service. To guarantee the security of your messages, compare
    the following hashes with your partner %s through a secure second
    channel. If the keys do not match, it is likely that your are victim of
    a Man-in-the-Middle attack.

    Hash of your key:
    %s

    Hash of your partners key
    %s""" % (myid, otherid, otherid, mykey_bishop, otherkey_bishop)

    return mailtext