#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       user.py
#
"""
Comba User Class  - Benutzerverwaltung
"""
import os
import sys
import redis
import random
import string

## current directory
scriptdir = os.path.dirname(os.path.abspath(__file__))
# Hier stecken unsere eigenen Python libraries
package_dir = os.path.join(scriptdir, 'python')
path = list(sys.path)
# Das package_dir zu den Systempfaden hinzufügen, damit wir Importe durchführen können
sys.path.insert(0, package_dir)
"""
User verwalten
"""
class CombaUser(object):

    def __init__(self):
        self.db = redis.Redis()
        self.dbname = 'combausers'
        self.userprefix = 'combauser:'
        pass

    #------------------------------------------------------------------------------------------#
    def delete(self, username):
        """
        Delete an user
        :param username:
        :return: boolean
        """
        userid = self.db.hget(self.dbname,username)
        if not userid:
            return False
        else:
            self.db.delete(self.userprefix + str(userid))
            self.db.hdel(self.dbname,username)
            return True

    #------------------------------------------------------------------------------------------#
    def setPassword(self,username, password):
        """
        Set users password
        :param username: string
        :param password: string
        :return: boolean
        """
        userid = self.db.hget(self.dbname,username)
        if not userid:
            return False
        self.db.hset(self.userprefix + str(userid), 'password', password)
        return True

    #------------------------------------------------------------------------------------------#
    def hasRole(self, username, role):
        """
        Compare users role
        :param username: string
        :param role: string
        :return:boolean
        """
        userid = self.db.hget(self.dbname,username)
        dbrole = self.db.hget(self.userprefix + str(userid), 'role')
        return (dbrole == role)

    #------------------------------------------------------------------------------------------#
    def hasPassword(self,username, password):
        """
        Compare users password with the given one
        :param username: string
        :param password: string
        :return:
        """
        userid = self.db.hget(self.dbname,username)
        dbpassword = self.db.hget(self.userprefix + str(userid), 'password')
        return (dbpassword == password)

    #------------------------------------------------------------------------------------------#
    def hasAdminRights(self, username, password):
        """
        Check admin rights
        :param username: username
        :param password: password
        :return:
        """
        return (self.hasPassword(username,password) and self.hasRole(username, 'admin'))

    #------------------------------------------------------------------------------------------#
    def insertUser(self, username, password, role="user"):
        """
        Insert or update user
        :param username: string
        :param password: string
        :param role: string
        :return: string - the password
        """
        userid = self.db.hget(self.dbname,username)

        if not userid:
            userid = self.db.incr("next_combauser_id")
            self.db.hset(self.dbname,username,userid)
        self.db.hmset(self.userprefix + str(userid), {"username" : username,"password" :password, "role" : role})
        return password

    #------------------------------------------------------------------------------------------#
    def getUser(self, username):
        """
        Get users data
        :param username: string
        :return: dict - userdata
        """
        userid = self.db.hget(self.dbname,username)
        return self.db.hgetall(self.userprefix + str(userid))

    #------------------------------------------------------------------------------------------#
    def getUserlist(self):
        """
        get all users
        :return: list - the userlist
        """
        accounts=[]
        keys  = self.db.keys(self.userprefix + "*")
        for key in keys:
            accounts.append(self.db.hgetall(key))
        return accounts

    #------------------------------------------------------------------------------------------#
    def getLogins(self):
        """
        get usernames passwords as dict in format  {username1:password1, username2;password2, ...}
        :return:
        """
        accounts={}
        keys  = self.db.keys(self.userprefix + "*")

        for key in keys:
            account = self.db.hgetall(key)
            try:
                accounts[account['username']] = account['password']
            except:
                pass
        return accounts

    #------------------------------------------------------------------------------------------#
    def createPassword(self):
        """
        create a new passoword
        :return: string - the password
        """
        password = ''.join(random.sample(string.lowercase+string.uppercase+string.digits,14))
        return password