#!/usr/bin/env python
from axoctl import *

ac = AxoCtl()
out_mail = ac.process_inbound({
	"to": "fschuiki@ethz.ch",
	"from": "ddoebeli@ethz.ch",
	"headers": [
		("Subject", "Exmatrikulation"),
		("Content-Type", "message/x-axonaut")
	],
	"body": "Shake that thing"
})

print out_mail
