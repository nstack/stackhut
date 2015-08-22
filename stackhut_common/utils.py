# Copyright 2015 StackHut Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import sys
import os
from colorlog import ColoredFormatter

####################################################################################################
# App Config
# global constants
CONTRACTFILE = '.api.json'
IDLFILE = 'api.idl'
SERVER_URL = "https://api.stackhut.com/"
IN_CONTAINER = os.path.exists('/workdir')
VERBOSE = False
ROOT_DIR = os.getcwd()

# Logging
# LOGFILE = '.stackhut.log'
logging.getLogger().disabled = True
logging.getLogger('werkzeug').disabled = True

log = logging.getLogger('stackhut')
def setup_logging(verbose_mode):
    global VERBOSE
    global log
    VERBOSE = verbose_mode
    log.propagate = False
    log.setLevel(logging.DEBUG if verbose_mode else logging.INFO)

    logFormatter = ColoredFormatter(
        '%(blue)s%(asctime)s%(reset)s [%(log_color)s%(levelname)-5s%(reset)s] %(message)s',
        datefmt='%H:%M:%S',
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # file output
    # fileHandler = logging.FileHandler(LOGFILE, mode='w')
    # fileHandler.setFormatter(logFormatter)
    # log.addHandler(fileHandler)

    # console
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)
