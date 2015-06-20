#!/usr/bin/env python2
# TODO - switch to python3 once OSX and Ubuntu/Redhat distros do
__author__ = 'stackhut'

import argparse
import logging
import yaml

# TODO here


# parse cmd args
def parse_main_cmd():
    pass

# parse cmd args
def parse_cmd_args():
    # parse cmd-args
    # aws_key[s], s3bucket id, --?
    # get AWS keys - hmm, how do we do this securly?
    # need temp keys
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id", help="Id representing the specific task", type=str)
    parser.add_argument("aws_id", help="Key used to communicate with AWS", type=str)
    parser.add_argument("aws_key", help="Key used to communicate with AWS", type=str)
    parser.add_argument("--local", help="Run system locally", action="store_true")
    args = parser.parse_args()
    self.aws_id = args.aws_id
    self.aws_key = args.aws_key
    self.task_id = args.task_id
    global LOCAL
    LOCAL = args.local








if __name__ == "__main__":
    # setup the logger
    logging.basicConfig(filename='./stackhut.log', level=logging.INFO)

    # import the hutfile
    hutfile = yaml.load(open('./Hutfile', 'r'))

    main_cmd = parse_main_cmd()

    # dispatch to correct subfunction - i.e. build, compile, run, etc.




    exit(0)
