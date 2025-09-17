'''
   Copyright 2025 philippoo66
   
   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

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
        self.onceonlies_removed = False

        if(os.path.exists("poll_list.py")):
            mylist = importlib.import_module('poll_list')
            self.items = mylist.poll_items
        else:
            self.items = settings_ini.poll_items
        self.num_items = len(self.items)
        print(f"poll_list made, {self.num_items} items")  #TEMP

    def remove_once_onlies(self):
        if self.onceonlies_removed: 
            return
        filtered = [item for item in self.items if not (isinstance(item[0], int) and item[0] == 0)]
        self.items = filtered
        newlen = len(self.items)
        if(self.num_items != newlen):
            self.num_items = newlen
            print(f"poll_list shrinked to {self.num_items} items")
        self.onceonlies_removed = True


# for global use
poll_list = cPollList()
