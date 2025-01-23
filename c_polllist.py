import os
import importlib

import settings_ini


class cPollList:
    def __init__(self):
        """
        Initialisiert die Klasse
        """
        self.items = []
        self.num_items = 0

        if(os.path.exists("poll_list.py")):
            mylist = importlib.import_module('poll_list')
            self.items = mylist.poll_items
        else:
            self.items = settings_ini.poll_items
        self.num_items = len(self.items)
        print(f"poll_list made, {self.num_items} items")  #TEMP


# for global use
poll_list = cPollList()
