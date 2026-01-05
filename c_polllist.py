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
from pathlib import Path
import importlib

from c_settings_adapter import settings
from logger_util import logger
import utils


class cPollList:
    def __init__(self):
        """
        Initialisiert die Klasse
        """
        self.items = []
        self.num_items = 0
        self.onceonlies_removed = False
        self.module_date = "0"

    def make_list(self, reload = False):
        try:
            # import module where poll list is taken from
            if(os.path.exists("poll_list.py")):
                listmodule = importlib.import_module('poll_list')
            elif(os.path.exists("ha_shared_config.py")):
                listmodule = importlib.import_module('ha_shared_config')
            else:
                listmodule = importlib.import_module('settings_ini')
            
            # if reload is requested
            if reload:
                listmodule = importlib.reload(listmodule)
            
            # apply poll list
            self.items = listmodule.poll_items
            self.num_items = len(self.items)
            self.onceonlies_removed = False

            # apply poll interval if given
            settings.poll_interval = getattr(listmodule, 'poll_interval', settings.poll_interval)

            # info
            logger.info(f"poll_list made, {self.num_items} items")

            # get modified date of module
            self.module_date = utils.get_module_modified_datetime(listmodule)
        except Exception as e:
            logger.error(f"make_list: {e}")


    def remove_once_onlies(self) -> bool:
        if self.onceonlies_removed: 
            return False
        filtered = [item for item in self.items if not (isinstance(item[0], int) and item[0] == 0)]
        self.items = filtered
        self.onceonlies_removed = True
        newlen = len(self.items)
        if(self.num_items != newlen):
            self.num_items = newlen
            logger.info(f"poll_list shrinked to {self.num_items} items")
            return True
        return False

# for global use
poll_list = cPollList()
