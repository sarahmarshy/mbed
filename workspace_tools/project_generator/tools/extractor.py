# Copyright 2014-2015 0xc0170
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from os.path import join
import os
import yaml

class Extractor():

    MCU_TEMPLATE = {
        'mcu': {
            'core': '',
            'vendor': ''
        },
        'tool_specific': {}
    }

    def save_mcu_data(self, mcu_data, mcu_name):

        filename = join(os.getcwd(), mcu_name + '.yaml')

        logging.info("Writing mcu data to %s",filename)

        with open(filename, 'wt') as f:
            f.write(yaml.safe_dump(mcu_data, default_flow_style=False, width=200))

        return 0