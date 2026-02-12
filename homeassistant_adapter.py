''' 
   Copyright 2026 matthias-oe
   Contributions by: EarlSneedSinclair

   Licensed under the GNU GENERAL PUBLIC LICENSE, Version 3 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       https://www.gnu.org/licenses/gpl-3.0.html

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   This script is designed to make Optolink-Splitter datapoints available from 
   the homeassistant_poll_list.py file.

   The documentation can be found here:
      https://github.com/philippoo66/optolink-splitter/wiki/211-Alternative-Home-Assistant-Integration
'''

import homeassistant_poll_list 

def extract_poll_items(poll_list):
    poll_items = []
    if "domains" in poll_list:
        for domain in poll_list["domains"]:
            if "poll" in domain:
                poll_items.extend(domain["poll"])
            if "units" in domain:
                for unit in domain["units"]:
                    if "poll" in unit:
                        poll_items.extend(unit["poll"])
    return poll_items

poll_items = extract_poll_items(homeassistant_poll_list.poll_list)
poll_interval = homeassistant_poll_list.poll_list.get("poll_interval", None)

ha_device = homeassistant_poll_list.poll_list
