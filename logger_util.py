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

# ---------------------------------------------------------------
# This module is used for the application logging,
# console and optolinkvs2_switch.log
# settings: no_logger_file
# ---------------------------------------------------------------

from c_LoggerUtil import LoggerUtil
from c_settings_adapter import settings 

# === Globale Loggerinstanz ===============================================
logger = LoggerUtil(
                name = "optolinkvs2_switch",
                level = settings.log_level, # DEBUG=10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50,  
                max_bytes = 5*1024*1024, # 5 MB
                backup_count = 1,
                no_file = settings.no_logger_file
            ).logger
