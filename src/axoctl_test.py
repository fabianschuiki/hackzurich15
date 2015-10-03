#!/usr/bin/env python
from axoctl import *

ac = AxoCtl()
out_mail = ac.process_outbound({
	"to": "fschuiki@ethz.ch",
	"from": "ddoebeli@ethz.ch",
	"headers": [
		("Subject", "Exmatrikulation"),
		("Content-Type", "text/plain"),
		("Message-Id", "abaoij4te4utjsdrg8hs4e"),
	],
	"body": "Shake that thing"
})

print out_mail
