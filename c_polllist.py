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
        self.cycle_groups = {}
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
            
            # apply poll groups (if exists)
            if getattr(listmodule, "poll_groups", False):
                self.cycle_groups = listmodule.poll_groups
            # make 1-cycle
            self.cycle_groups["*#1"] = 1

            # apply poll list
            #self.items = listmodule.poll_items
            for item in listmodule.poll_items:
                new_item = []
                if item[0] in self.cycle_groups:
                    # is cycle-grouped item
                    new_item.append(item[0])
                    new_item.extend(item[1:])
                elif isinstance(item[0], int):
                    # has numeric cycle
                    key = f"*#{item[0]}"
                    self.cycle_groups[key] = item[0]
                    new_item.append(key)
                    new_item.extend(item[1:])
                else:
                    # no cycle given - set 1
                    new_item.append("*#1")
                    new_item.extend(item[0:])
                
                # make tuple
                new_tuple = tuple(new_item)
                # append to poll items
                self.items.append(new_tuple)

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


    def set_pollcycle(self, group_key:str, value) -> bool:
        if group_key not in self.cycle_groups:
            return False
        try:
            cyc = int(value)
        except:
            return False
        self.cycle_groups[group_key] = cyc
        return True


    def find_datapoint_by_name(self, dpname):
        """Find datapoint configuration by name in poll_list."""
        if not self.items:
            return None
        
        # Check cache first
        if dpname in self.datapoint_metadata:
            return self.datapoint_metadata[dpname]
        
        # Search in poll_list items
        for lstidx in range(self.num_items):
            # (PollCycleGroupKey, Name, DpAddr, Len, [bbFilter,] Scale/Type, Signed)
            item = self.items[lstidx]   

            name = item[1]
            
            if name == dpname:  #TODO case-insesitive?!
                addr = item[2] #if len(item1) > 1 else None
                dlen = item[3] #if len(item1) > 2 else 1
                bbfilter = None
                offset = 0
                if isinstance(item[4], str) and str(item[4]).startswith('b:'):
                    # is bb-filter
                    bbfilter = item[4]
                    offset = 1
                scale_type = item[4 + offset] if len(item) > 4 + offset else None
                signed = item[5 + offset] if len(item) > 5 + offset else False
                metadata = {
                    'addr': addr,
                    'len': dlen,
                    'bbfilter': bbfilter,
                    'scale_type': scale_type,
                    'signed': signed,
                    'list_index': lstidx
                }
                # cache it
                self.datapoint_metadata[name] = metadata
                return metadata
        return None


# === for global use ================
poll_list = cPollList()

# poll_list.make_list()
# print(poll_list.num_items)
# for itm in poll_list.items:
#     print(itm)
