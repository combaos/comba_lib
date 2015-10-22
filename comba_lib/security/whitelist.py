#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       combawhitelist
#
"""
Comba Whitelist  - IP-Adressen oder Domains aus der Whitelist holen
"""
import os
import sys
import redis


"""
Whitelisting ips or hostnames
"""
class CombaWhitelist(object):
    def __init__(self):
        self.db = redis.Redis()
        self.dbname = 'combawhitelist'
        pass
    #------------------------------------------------------------------------------------------#
    def getList(self):
        """
        get the whitelist
        :return: list - list of whitelisted ip's
        """
        return self.db.lrange(self.dbname, 0, -1)

    #------------------------------------------------------------------------------------------#
    def add(self,address):
        """
        Add ip/host to whitelist
        :param address: string - ip or hostname
        :return: boolean
        """
        list = self.getList()
        for item in list:
            if item == address:
                return False
        self.db.lpush(self.dbname, address)
        return True

    #------------------------------------------------------------------------------------------#
    def remove(self,address):
        """
        Remove an ip or host from whitelist
        :param address: string - ip or hostname
        :return: boolean
        """
        if not address:
            return False
        self.db.lrem(self.dbname, address, 1)
        return True


