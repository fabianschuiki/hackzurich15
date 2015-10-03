import hashlib
from drunkenbishop.Fingerprint import Fingerprint

def GetFPrintMail(mykey, myid, otherkey, otherid):
    
    mykey_hash_str = hashlib.sha256(mykey).hexdigest().upper()
    mykey_hash_list = [int(mykey_hash_str[i:i+8], 16) for i in range(0,len(mykey_hash_str), 8)]

    otherkey_hash_str = hashlib.sha256(otherkey).hexdigest().upper()
    otherkey_hash_list = [int(otherkey_hash_str[i:i+8], 16) for i in range(0,len(otherkey_hash_str), 8)]

    my_name = myid.split("@")[0]
    other_name = otherid.split('@')[0]

    mykey_bishop = str(Fingerprint(mykey_hash_list, my_name, "SHA256"))
    otherkey_bishop = str(Fingerprint(otherkey_hash_list, other_name, "SHA256"))

    mail_template =     "Hello %(my_name)s,\n" + \
                        "\n" + \
                        "Your e-mail conversation with %(other_id)s was encrypted via the awesome Axonaut e-mail " +\
                        "encryption service. To verify the identity of %(other_name)s, " + \
                        "compare the following fingerprints with your partner.\n" + \
                        "\n" + \
                        "If they don't match you might be a victim to an active attack!\n"

    mailtext = mail_template % {'my_name': my_name,'other_name': other_name, 'my_id': myid, 'other_id': otherid}
    # Append dat bishop

    mykey_lines = mykey_bishop.splitlines()
    otherkey_lines = otherkey_bishop.splitlines()

    if my_name<other_name:
        lines = zip(mykey_lines,otherkey_lines)
    else:
        lines = zip(otherkey_lines,mykey_lines)

    fingerprints = "\n"
    for l1, l2 in lines:
        fingerprints += (" %s   %s \n" % (l1, l2))

    mailtext += fingerprints

    return mailtext