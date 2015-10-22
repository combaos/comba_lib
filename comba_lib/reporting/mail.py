__author__ = 'michel'

import os


class CombaMailer():

    def __init__(self, adminMails, fromMail):
        self.adminMails = adminMails
        self.fromMail = fromMail

    def sendAdminMail(self, subject, body):
        adminMails = self.adminMails.split()
        for mailTo in adminMails:
            self.send(self.fromMail, mailTo, subject, body)

    def send(self, mailFrom, mailTo, subject, body):
        sendmail_location = "/usr/sbin/sendmail"
        p = os.popen("%s -t" % sendmail_location, "w")
        p.write("From: %s\n" % mailFrom)
        p.write("To: %s\n" % mailTo)
        p.write("Subject: " + subject + "\n")
        p.write("\n") # blank line separating headers from body
        p.write(body)
        status = p.close()
        return status