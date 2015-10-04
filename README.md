# Not-So-Bad Privacy for E-Mail

We present a means of encrypting e-mail traffic in a manner transparent to the user, providing perfect forward secrecy, as well as plausible deniability and confidentiality. The burden of encrypting and decrypting traffic is pushed onto the first and last MTA (message transfer agent), which must be trusted entities. Being implemented as a milter (mail filter) that plugs into the Postfix SMTP server, our approach fully leverages the existing e-mail infrastructure and requires only minimal communication overhead at the start.

We trade robustness against man-in-the-middle attacks (MITM) in favor of an unobtrusive user experience. However, by making communication confidential, we force potential adversaries to become active attackers rather than passive eavesdroppers, thus decreasing the feasibility for widespread and systematic data retention. Nevertheless, the users are given the opportunity to authenticate each other via a different means of communication by visually comparing each others digital signatures.

Developed at HackZurich 2015 by *Marco Eppenberger*, *Thomas Richner*, and *Fabian Schuiki* from ETH Zurich.


## Protocol Overview

```
              Alice's Trust                                           Bob's Trust                          
+--------------------------------+        untrusted     +--------------------------------+                 
|                                |                      |                                |                 
     +-------+        +-------+          +-------+         +-------+          +-------+                    
     |       |        |       |          |       |         |       |          |       |                    
     | Alice |        |  MTA  |          |  MTA  |         |  MTA  |          |  Bob  |                    
     |       |        |       |          | (NSA) |         |       |          |       |                    
     +---+---+        +---+---+          +---+---+         +---+---+          +---+---+                    
         |                |                  |                 |                  |                        
         |     M1         |                  |                 |                  |   ----+                
         +--------------> |        K_req     |                 |                  |       |                
         |                +----------------> |      K_req      |                  |       |                
         |                |                  +---------------> |                  |       |                
         |                |                  |      K_resp     |                  |       | key agreement &
         |                |      K_resp      | <---------------+                  |       | first message  
         |                | <----------------+                 |                  |       |                
         |                |     C1           |                 |                  |       |                
         |                +----------------> |     C1          |                  |       |                
         |                |                  +---------------> |        M1        |       |                
         |                |                  |                 +----------------> |       |                
         |                |                  |                 |                  |   ----+                
         |                |                  |                 |                  |                        
         |                |                  |                 |                  |   ----+                
         |     M2         |                  |                 |                  |       |                
         +--------------> |       C2         |                 |                  |       | All following  
         |                +----------------> |       C2        |                  |       | messages       
         |                |                  +---------------> |      M2          |       |                
         |                |                  |                 +----------------> |       |                
         |                |                  |                 |                  |       |                
                                                                                      ----+                
```


## External Sources

We use the following components not developed by ourselves:

- drunkenbishop [1], an implementation of the *Drunken Bishop* visualization method for hashes and keys
- pyaxo [2], an implementation of the Axolotl ratchet protocol used by TextSecure and to a lesser degree WhatsApp

[1]: https://github.com/natmchugh/drunken-bishop
[2]: https://github.com/rxcomm/pyaxo


## Virtual Machines on Azure

As a testing setup, we leverage Microsoft's Azure cloud infrastructure to create a three-hop route from a client in Zurich to another client in Zurich, via SMTP servers `Dublin -> North America -> Dublin`.

- URL *Alice*: maxo0.cloudapp.net or 40.113.12.166
- URL *Bob*: moxa1.cloudapp.net or 40.113.12.78
- URL *Relay*: maxorelay.cloudapp.net or 40.122.174.29

Username: `azureuser`, password `B77d795d`.

### E-Mail Addresses

- *maxo0*: alice@maxo0.cloudapp.net
- *moxa1*: bob@moxa1.cloudapp.net


## External Links

- pymilter: https://pythonhosted.org/milter/
- pymilter doc: https://pythonhosted.org/pymilter/namespaceMilter.html
- axolotl ratchet in Go: https://github.com/janimo/textsecure
- axolotl ratchet: https://github.com/trevp/axolotl/wiki
- Open Whisper Systems blog post: https://whispersystems.org/blog/advanced-ratcheting/
- Pond, similar stuff: https://github.com/agl/pond
- pyaxo, axolotl implementation in python: https://github.com/rxcomm/pyaxo
- postfix milters: http://www.postfix.org/MILTER_README.html


## Setup

- `pip install pyaxo`
- create `HOST` file in `src/`
- configure postfix for milter, add `smtpd_milters = inet:localhost:5000` to `/etc/postfix/main.cf`

