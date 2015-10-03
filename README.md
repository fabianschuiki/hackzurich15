# HackZurich 2015
*Marco Eppenberger, Thomas Richner, Fabian Schuiki; ETH Zurich.*

## VirtualMachines:


url Alice: maxo0.cloudapp.net or 40.113.20.240<br>
url Bob: maxo1.cloudapp.net or 40.113.91.78<br>
url Relay: maxorelay.cloudapp.net or 40.78.159.248<br>

bn: azureuser<br>
pw: B77d795d<br>

mailaddresses:<br>
maxo0: alice@maxo0.cloudapp.net<br>
maxo1: bob@maxo1.cloudapp.net<br>

relay:

## Link collection

- pymilter: https://pythonhosted.org/milter/
- pymilter doc: https://pythonhosted.org/pymilter/namespaceMilter.html

- axolotl ratchet in Go: https://github.com/janimo/textsecure
- axolotl ratchet: https://github.com/trevp/axolotl/wiki
- Open Whisper Systems blog post: https://whispersystems.org/blog/advanced-ratcheting/
- Pond, similar stuff: https://github.com/agl/pond

## Setup

- `pip install pyaxo`
- create `HOST` file in `src/`
- configure postfix for milter, add `smtpd_milters = inet:localhost:5000` to `/etc/postfix/main.cf`

