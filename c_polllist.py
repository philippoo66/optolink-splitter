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
        self.module_date = "0"
        # datapoint metadata cache for /set topics
        self.datapoint_metadata = {}


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
            self.module_date = utils.get_module_modified_datetime(listmodule)

            # reset cache
            self.datapoint_metadata = {}

            # apply poll interval if given
            settings.poll_interval = getattr(listmodule, 'poll_interval', settings.poll_interval)

            # info
            logger.info(f"poll_list made, {self.num_items} items")
        except Exception as e:
            logger.error(f"make_list: {e}")


    def find_datapoint_by_name(self, dpname):
        """Find datapoint configuration by name in poll_list."""
        if not self.items:
            return None
        
        # Check cache first
        if dpname in self.datapoint_metadata:
            return self.datapoint_metadata[dpname]
        
        # Search in poll_list items
        for lstidx in range(self.num_items):
            # Handle PollCycle entries: ([PollCycle,] Name, DpAddr, Len, [bbFilter,] Scale/Type, Signed)
            item = self.items[lstidx]
            if len(item) > 1 and isinstance(item[0], int):
                # has PollCycle prefix
                item = item[1:] 

            name = item[0]
            
            if name == dpname:
                addr = item[1] #if len(item1) > 1 else None
                dlen = item[2] #if len(item1) > 2 else 1
                #TODO bbFilter...
                scale_type = item[3] if len(item) > 3 else None
                signed = item[4] if len(item) > 4 else False
                metadata = {
                    'addr': addr,
                    'len': dlen,
                    'scale_type': scale_type,
                    'signed': signed,
                    'list_index': lstidx
                }
                # Cache it
                self.datapoint_metadata[dpname] = metadata
                return metadata
        return None


# === for global use ================
poll_list = cPollList()
