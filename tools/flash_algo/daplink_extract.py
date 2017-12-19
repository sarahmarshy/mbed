#!/usr/bin/env python
"""
 mbed
 Copyright (c) 2017-2017 ARM Limited

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

from __future__ import print_function
import sys
import os
import argparse
from os.path import join, abspath, dirname
from flash_algo import PackFlashAlgo
from fuzzywuzzy import process
from itertools import takewhile

# Be sure that the tools directory is in the search path
ROOT = abspath(join(dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.targets import TARGETS
from tools.arm_pack_manager import Cache

TEMPLATE_PATH = join(dirname(__file__),"c_blob.tmpl")
# TODO
# FIXED LENGTH - remove and these (shrink offset to 4 for bkpt only)
BLOB_HEADER = '0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,'
HEADER_SIZE = 0x20

def str_to_num(val):
    return int(val,0)  #convert string to number and automatically handle hex conversion

def find_possible(match, choices):
    return process.extractOne(match, choices)


def main():
    """Generate flash algorithms"""
    parser = argparse.ArgumentParser(description='Flash generator')
    parser.add_argument("--rebuild_all", action="store_true",
                        help="Rebuild entire cache")
    parser.add_argument("--rebuild_descriptors", action="store_true",
                        help="Rebuild descriptors")
    parser.add_argument("--target", default=None,
                        help="Name of target to generate algo for")
    parser.add_argument("--daplink", default=None,
                        help="Root location of daplink")
    parser.add_argument("--all", action="store_true",
                        help="Build all flash algos for devcies")
    parser.add_argument("--blob_start", default=0x20000000, type=str_to_num, help="Starting "
                        "address of the flash blob. Used only for DAPLink.")
    args = parser.parse_args()

    cache = Cache(True, True)
    if args.rebuild_all:
        cache.cache_everything()
        print("Cache rebuilt")
        return

    if args.rebuild_descriptors:
        cache.cache_descriptors()
        print("Descriptors rebuilt")
        return

    if args.target is None:
        device_and_filenames = [(target.device_name, target.name.lower()) for target
                                in TARGETS if hasattr(target, "device_name")]
    else:
        device_and_filenames = [(args.target, args.target.replace("/", "-"))]

    try:
        os.mkdir("output")
    except OSError:
        # Directory already exists
        pass

    target_to_file = get_daplink_files(args.daplink)

    SP = args.blob_start + 2048
    data_dict = {
        'prog_header': BLOB_HEADER,
        'header_size': HEADER_SIZE,
        'entry': args.blob_start,
        'stack_pointer': SP,
    }
    print(len(target_to_file.keys()))
    print(len(device_and_filenames))
    added = []
    for device, mbed_target in device_and_filenames:
        dev = cache.index[device]
        if(mbed_target not in target_to_file):
            fuzz1 = find_possible(mbed_target, target_to_file.keys())
            fuzz2 = find_possible(device, target_to_file.keys())
            if fuzz1[1] >= 90:
                mbed_target = fuzz1[0]
            elif fuzz2[1] >= 90:
                mbed_target = fuzz2[0]
            else:
                continue
        added.append(mbed_target)
        binaries = cache.get_flash_algorthim_binary(device, all=True)
        algos = [PackFlashAlgo(binary.read()) for binary in binaries]
        filtered_algos = algos if args.all else filter_algos(dev, algos)
        for idx, algo in enumerate(filtered_algos):
            algo.process_template(TEMPLATE_PATH, target_to_file[mbed_target], data_dict)
        print("%s: %s      \r" % (device, target_to_file[mbed_target]))
    write_missing_symbols([dev for dev in target_to_file.keys() if dev not in added], target_to_file)

def write_missing_symbols(missing_devices, target_to_file):
    for device in missing_devices:
        flash_file = target_to_file[device]
        empty_array = 'static const uint32_t sectors_info[] = {};'
        with open(flash_file, 'a') as f:
            f.write(empty_array)


def get_daplink_files(daplink_root):
    daplink_targets = join(daplink_root, 'source', 'target')
    target_to_file = {}
    print(os.getcwd())
    for root,dirs,files in os.walk(daplink_targets):
        if 'flash_blob.c' in files:
            target = os.path.basename(os.path.normpath(root))
            flash_file = join(root, 'flash_blob.c')
            target_to_file[target] = flash_file
    return target_to_file


def filter_algos(dev, algos):
    if "memory" not in dev:
        return algos
    if "IROM1" not in dev["memory"] or "PROGRAM_FLASH" not in dev["memory"]:
        return algos
    if "IROM2" in dev["memory"]:
        return algos

    rom_rgn = dev["memory"]["IROM1"]
    try:
        start = int(rom_rgn["start"], 0)
        size = int(rom_rgn["size"], 0)
    except ValueError:
        return algos

    matching_algos = [algo for algo in algos if
                      algo.flash_start == start and algo.flash_size == size]
    return matching_algos if len(matching_algos) == 1 else algos


if __name__ == '__main__':
    main()
