"""
mbed SDK
Copyright (c) 2011-2013 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from workspace_tools.export.exporters import Exporter
import re
import os
class IAREmbeddedWorkbench(Exporter):
    """
    Exporter class for IAR Systems.
    """
    NAME = 'IAR'
    TOOLCHAIN = 'IAR'

    TARGETS = [
        'LPC1768',
        'LPC1347',
        'LPC11U24',
        'LPC11U35_401',
        'LPC11U35_501',
        #Removed LPCCAPPUCCINO linker file and startup file missing
        #'LPCCAPPUCCINO',
        'LPC1114',
        'LPC1549',
        'LPC812',
        'LPC4088',
        'LPC4088_DM',
        'LPC824',
        'UBLOX_C027',
        'ARCH_PRO',
        'K20D50M',
        'KL05Z',
        'KL25Z',
        'KL46Z',
        'K22F',
        'K64F',
        'NUCLEO_F030R8',
        'NUCLEO_F070RB',
        'NUCLEO_F072RB',
        'NUCLEO_F091RC',
        'NUCLEO_F103RB',
        'NUCLEO_F302R8',
        'NUCLEO_F303RE',
        'NUCLEO_F334R8',
        'NUCLEO_F401RE',
        'NUCLEO_F411RE',
        'NUCLEO_F446RE',
        'NUCLEO_L053R8',
        'NUCLEO_L073RZ',
        'NUCLEO_L152RE',
        'DISCO_L053C8',
        'DISCO_F334C8',
        'DISCO_F746NG',
        'DISCO_L476VG',
        #'STM32F407', Fails to build same for GCC
        'MAXWSNENV',
        'MAX32600MBED',
        'MTS_MDOT_F405RG',
        'MTS_MDOT_F411RE',
        'MTS_DRAGONFLY_F411RE',
        'NRF51822',
        'NRF51_DK',
        'NRF51_DONGLE',
        'DELTA_DFCM_NNN40',
        'SEEED_TINY_BLE',
        'HRM1017',
        'ARCH_BLE',
        'MOTE_L152RC',
    ]
