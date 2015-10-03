from subprocess import Popen, PIPE
from email.mime.text import MIMEText
import smtplib


# u need dat: from email.mime.text import MIMEText
def sendmimemail(mimetext, from_addr, to_addr):
    # msg = MIMEText(mail['body'])
    # msg["From"] = mail['from']
    # msg["To"] = mail['to']
    # msg["Subject"] = mail['subject']

    # use the sendmail command
    # p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    # p.communicate(mimetext.as_string())

    # use the builtin facilities
    s = smtplib.SMTP('localhost')
    s.sendmail(from_addr, [to_addr], mimetext.as_string())
    s.quit()


def sendmail(sender, receiver, subject, body):
    msg = MIMEText(body)
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(msg.as_string())

def prependHeaders(aheader, abody):
    nbody = str(len(aheader)) + "\n"
    for h, v in aheader:
        nbody += h + '=' + v + '\n'
    nbody += abody
    return nbody


def nomsHeaders(abody):
    liner = StringIO.StringIO(abody)
    nheader = int(liner.readline())
    headers = []
    for i in xrange(0, nheader):
        line = liner.readline()
        item = line.split('=')
        headers.append((item[0], item[1]))
    return headers, liner.read()
