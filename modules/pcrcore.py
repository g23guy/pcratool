# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#-*- coding: utf-8 -*-
'''
Pacemaker Cluster Report Core Module
Copyright (c) 2025 SUSE LLC

Module of functions for core tasks
'''
##############################################################################
#  Copyright (C) 2025 SUSE LLC
##############################################################################
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
__author__        = 'Jason Record <jason.record@suse.com>, Raine Curtis <raine.curtis@suse.com>'
__date_modified__ = '2025 Oct 09'
__version__       = '0.0.1'

# IMPORTS
import os
import sys
import json
from shutil import rmtree
import subprocess

def separator_line(width, use_char = '#'):
    print("{}".format(use_char*width))

def separate_entry(msg, width, count):
    if count > 1:
        msg.min()
        msg.separator(width, msg.LOG_MIN, '=')
        msg.min()

def config_entry(_entry, trailer = ''):
    formatted_entry = _entry.strip('\"\'')
    if( len(trailer) > 0 ):
        if len(formatted_entry) > 0:
            if not formatted_entry.endswith(trailer):
                formatted_entry = formatted_entry + str(trailer)
    return formatted_entry

class ProgressBar():
    """Initialize and update progress bar class"""

    def __init__(self, width, description_width, prefix, total):
        self.base_len = int(width)
        self.desc_width = int(description_width) + 1
        self.bar_width = self.base_len
        self.prefix = prefix
        self.prefix_size = len(self.prefix)
        self.total = int(total)
        self.count = 0
        self.out = sys.stdout
        if self.prefix_size > self.desc_width:
            self.bar_width = self.base_len - self.prefix_size - 2
        else:
            self.bar_width = self.base_len - self.desc_width - 2
        self.display = "{:" + str(self.desc_width) + "s}[{}{}] {:3g}% {:3g}/{}"

    def __str__(self):
        return 'class %s(\n  prefix=%r \n  bar_width=%r \n  total=%r\n)' % (self.__class__.__name__, self.prefix, self.bar_width, self.total)

    def set_prefix(self, _prefix):
        self.prefix = _prefix
        if ( self.bar_width_orig == self.base_len ):
            self.bar_width = self.base_len - self.prefix_size - 2
        else:
            self.bar_width = self.bar_width_orig

    def set_total(self, _new_total):
        self.total = _new_total

    def inc_count(self, increment = 1):
        """Increments one by default"""
        if self.count < self.total:
            self.count += increment

    def get_total(self):
        return self.total

    def get_count(self):
        return self.count

    def update(self):
        percent_complete = int(100*self.count/self.total)
        current_progress = int(self.bar_width*self.count/self.total)
        print(self.display.format(self.prefix, "#"*current_progress, "."*(self.bar_width-current_progress), percent_complete, self.count, self.total), end='\r', file=self.out, flush=True)

    def finish(self):
        if self.count != self.total:
            self.count = self.total
            self.update()
        print("", flush=True, file=self.out)

class DisplayMessages():
    "Display message string for a given log level"
    LOG_QUIET = 0    # turns off messages
    LOG_MIN = 1    # minimal messages
    LOG_NORMAL = 2    # normal, but significant, messages
    LOG_VERBOSE = 3    # detailed messages
    LOG_DEBUG = 4    # debug-level messages
    LOG_LEVELS = {0: "Quiet", 1: "Minimal", 2: "Normal", 3: "Verbose", 4: "Debug" }

    def __init__(self):
        self.level = self.LOG_MIN # instance default
        self.desc_width = 30 # instance default
        self.msg_display = "{:" + str(self.desc_width) + "}"
        self.msg_display_pair = self.msg_display + " = {}"

    def __str__ (self):
        return "class %s(level=%r)" % (self.__class__.__name__,self.level)

    def set_width(self, width_value):
        self.desc_width = width_value
        self.msg_display = "{:" + str(self.desc_width) + "}"
        self.msg_display_pair = self.msg_display + " = {}"

    def get_level(self):
        return self.level

    def get_level_str(self):
        return self.LOG_LEVELS[self.level]

    def set_level(self, level):
        if( level >= self.LOG_DEBUG ):
            self.level = self.LOG_DEBUG
        else:
            self.level = level

    def validate_level(self, level):
        validated_level = -1
        if( level.isdigit() ):
            validated_level = int(level)
        else:
            argstr = level.lower()
            if( argstr.startswith("qui") ):
                validated_level = self.LOG_QUIET
            elif( argstr.startswith("min") ):
                validated_level = self.LOG_MIN
            elif( argstr.startswith("norm") ):
                validated_level = self.LOG_NORMAL
            elif( argstr.startswith("verb") ):
                validated_level = self.LOG_VERBOSE
            elif( argstr.startswith("debug") ):
                validated_level = self.LOG_DEBUG

        return validated_level


    def __write_paired_msg(self, level, msgtag, msgstr):
        if( level <= self.level ):
            print(self.msg_display_pair.format(msgtag, msgstr))

    def __write_msg(self, level, msgtag):
        if( level <= self.level ):
            print(self.msg_display.format(msgtag))

    def quiet(self, msgtag = None, msgstr = None):
        "Write messages even if quiet is set"
        if msgtag:
            if msgstr:
                self.__write_paired_msg(self.LOG_QUIET, msgtag, msgstr)
            else:
                self.__write_msg(self.LOG_QUIET, msgtag)
        else:
            if( self.level >= self.LOG_QUIET ):
                print()

    def min(self, msgtag = None, msgstr = None):
        "Write the minium amount of messages"
        if msgtag:
            if msgstr:
                self.__write_paired_msg(self.LOG_MIN, msgtag, msgstr)
            else:
                self.__write_msg(self.LOG_MIN, msgtag)
        else:
            if( self.level >= self.LOG_MIN ):
                print()

    def normal(self, msgtag = None, msgstr = None):
        "Write normal, but significant, messages"
        if msgtag:
            if msgstr:
                self.__write_paired_msg(self.LOG_NORMAL, msgtag, msgstr)
            else:
                self.__write_msg(self.LOG_NORMAL, msgtag)
        else:
            if( self.level >= self.LOG_NORMAL ):
                print()

    def verbose(self, msgtag = None, msgstr = None):
        "Write more verbose informational messages"
        if msgtag:
            if msgstr:
                self.__write_paired_msg(self.LOG_VERBOSE, msgtag, msgstr)
            else:
                self.__write_msg(self.LOG_VERBOSE, msgtag)
        else:
            if( self.level >= self.LOG_VERBOSE ):
                print()

    def debug(self, msgtag = None, msgstr = None):
        "Write all messages, including debug level"
        if msgtag:
            updated_msgtag = "+ " + msgtag
            if msgstr:
                self.__write_paired_msg(self.LOG_DEBUG, updated_msgtag, msgstr)
            else:
                self.__write_msg(self.LOG_DEBUG, updated_msgtag)
        else:
            if( self.level >= self.LOG_DEBUG ):
                print()

    def separator(self, width, required_level, use_char = '#'):
        if self.level >= required_level:
            print("{}".format(use_char*width))


def valid_archive_dir(msg, given_path):
    TEST_FILES = ['description.txt', 'analysis.txt']
    if not os.access(given_path, os.R_OK | os.X_OK):
        msg.min(" ERROR:", "Directory permission denied: {0}".format(given_path))
        msg.min(" * Suggestion", "Try sudo {} {}".format(tool_name, given_path))
        return False
    else:
        for test_file in TEST_FILES:
            file_path = given_path + '/' + test_file
            if not os.access(file_path, os.F_OK):
                msg.min(" ERROR:", "Invalid cluster report directory: {0}".format(given_path))
                msg.min(" * Missing", "{0}".format(file_path))
                return False
            elif not os.access(file_path, os.R_OK):
                msg.min(" ERROR:", "Read file permission denied: {0}".format(file_path))
                msg.min(" * Suggestion", "Try sudo {} {}".format(tool_name, given_path))
                return False
    return True

def extract_archive(msg, tarball):
    path_in_tarball = ''
    archfile = tarball['path'] 
    archdir = tarball['dirpath_extract_here']
    msg.verbose(" Extracting File", archfile)
    msg.debug("archdir", archdir)
    cmd = "tar -xvf "  + archfile + " -C " + archdir
    msg.debug('Process Command', cmd)
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    outfile = stdout.splitlines()[0]
    msg.debug("outfile", outfile)
    rc = process.returncode
    if( rc > 0 ):
        print(" Error: Cannot extract tar file", file=sys.stderr)
        print(stderr, file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(7)
    else:
        path_in_tarball = archdir + '/' + os.path.dirname(outfile).split("/")[0]
        msg.verbose(' Embedded Directory', path_in_tarball)

    return path_in_tarball

def i_am_root():
    if not os.environ.get("SUDO_UID") and os.geteuid() != 0:
        return False
    return True

def clean_up(msg, data):
    if data['source_data']['valid']:
        if data['source_data']['remove_directory']:
            try:
                rmtree(data['source_data']['dirpath_data_source'])
            except:
                True

        if data['source_data']['remove_tarball']:
            try:
                os.remove(data['source_data']['path'])
            except:
                True

def evaluate_given_path(msg, given_path):
    given_results = {
        'exists': False, 
        'given_path': given_path, 
        'path': '', 
        'head': '', 
        'tail': '', 
        'type': '', 
        'tail_mime_type': '',
        'head_read': False, 'head_write': False, 'head_exec': False, 
        'tail_read': False, 'tail_write': False, 'tail_exec': False, 
    }

    if os.path.exists(given_path):
        given_results['exists'] = True
        given_results['path'] = os.path.abspath(given_path)
        given_results['head'] = os.path.dirname(given_results['path'])
        given_results['tail'] = os.path.basename(given_results['path'])
        if os.access(given_results['path'], os.R_OK):
            given_results['tail_read'] = True
        if os.access(given_results['path'], os.W_OK):
            given_results['tail_write'] = True
        if os.access(given_results['path'], os.X_OK):
            given_results['tail_exec'] = True
        if given_results['tail_read']:
            if os.path.isfile(given_results['path']):
                given_results['type'] = 'file'
                cmd = "file --brief --mime-type " + given_path
                msg.debug('Process Command', cmd)
                process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = process.communicate()
                given_results['tail_mime_type'] = stdout.strip()
            elif os.path.isdir(given_results['path']):
                given_results['type'] = 'dir'
                given_results['tail_mime_type'] = 'inode/directory'
        if os.access(given_results['head'], os.R_OK):
            given_results['head_read'] = True
        if os.access(given_results['head'], os.W_OK):
            given_results['head_write'] = True
        if os.access(given_results['head'], os.X_OK):
            given_results['head_exec'] = True

    msg.debug("Evaluate Path", given_results)
    return given_results

def check_extraction_path_given(msg, config_file, extract_path_cmd, extract_path_config):
    path_data = {}

    if extract_path_cmd:
        path_data = evaluate_given_path(msg, extract_path_cmd)
        msg.verbose("Extraction Directory", "Evaluating path given on command line: {0}".format(path_data['given_path']))
        if path_data['exists']:
            if path_data['tail_write']:
                path_data['dirpath_extract_here'] = path_data['path']
                path_data['extract_here_for_reports'] = True
                msg.normal("Extraction Directory Change", "From command line: {0}".format(path_data['path']))
            else:
                msg.min("Extraction Directory", "Evaluating path given on command line: {0}".format(path_data['given_path']))
                msg.min(" Error", "Write permisson denied, cannot extract file to {0}".format(path_data['path']))
                msg.min(" * Suggestion", "Fix the -x, --dirpath_extract_here directory\n")
                sys.exit(2)
        else:
            msg.min("Extraction Directory", "Evaluating path given on command line: {0}".format(path_data['given_path']))
            msg.min(" Error", "Directory not found - {0}".format(path_data['given_path']))
            msg.min(" * Suggestion", "Try mkdir -p {0} or fix the -x, --dirpath_extract_here directory\n".format(path_data['given_path']))
            sys.exit(2)
    elif extract_path_config:
        path_data = evaluate_given_path(msg, extract_path_config)
        msg.verbose("Extraction Directory", "Evaluating path given in the config file: {0}".format(path_data['given_path']))
        if path_data['exists']:
            if path_data['tail_write']:
                path_data['dirpath_extract_here'] = path_data['path']
                path_data['extract_here_for_reports'] = True
                msg.normal("Extraction Directory Change", "From config file: {0}".format(path_data['path']))
            else:
                msg.min("Extraction Directory", "Evaluating path given in the config file: {0}".format(path_data['given_path']))
                msg.min(" Error", "Write permisson denied, cannot extract file to {0}".format(path_data['path']))
                msg.min(" * Suggestion", "Fix the extract_path in {0}\n".format(config_file))
                sys.exit(2)
        else:
            msg.min("Extraction Directory", "Evaluating path given in the config file: {0}".format(path_data['given_path']))
            msg.min(" Error", "Directory not found - {0}".format(path_data['given_path']))
            msg.min(" * Suggestion", "Try mkdir -p {0} or fix the extract_path in {1}\n".format(path_data['given_path'], config_file))
            sys.exit(2)

    return path_data

def check_report_path_given(msg, config_file, report_path_cmd, report_path_config):
    path_data = {}

    if report_path_cmd:
        path_data = evaluate_given_path(msg, report_path_cmd)
        msg.verbose("Report Directory", "Evaluating path given on command line: {0}".format(path_data['given_path']))
        if path_data['exists']:
            if path_data['tail_write']:
                msg.normal("Report Directory Change", "From command line: {0}".format(path_data['path']))
            else:
                msg.min("Report Directory", "Evaluating path given on command line: {0}".format(path_data['given_path']))
                msg.min(" Error", "Write permisson denied, cannot create report file in {0}".format(path_data['path']))
                msg.min(" * Suggestion", "Fix the -o, --output directory\n")
                sys.exit(3)
        else:
            msg.min("Report Directory", "Evaluating path given on command line: {0}".format(path_data['given_path']))
            msg.min(" Error", "Directory not found - {0}".format(path_data['given_path']))
            msg.min(" * Suggestion", "Try mkdir -p {0} or fix the -o, --output directory\n".format(path_data['given_path']))
            sys.exit(3)
    elif report_path_config:
        path_data = evaluate_given_path(msg, report_path_config)
        msg.verbose("Report Directory", "Evaluating path given in the config file: {0}".format(path_data['given_path']))
        if path_data['exists']:
            if path_data['tail_write']:
                msg.normal("Report Directory Change", "From config file: {0}".format(path_data['path']))
            else:
                msg.min("Report Directory", "Evaluating path given in the config file: {0}".format(path_data['given_path']))
                msg.min(" Error", "Write permisson denied, cannot create report file in {0}".format(path_data['path']))
                msg.min(" * Suggestion", "Fix the report_output_path in {0}\n".format(config_file))
                sys.exit(3)
        else:
            msg.min("Report Directory", "Evaluating path given in the config file: {0}".format(path_data['given_path']))
            msg.min(" Error", "Directory not found - {0}".format(path_data['given_path']))
            msg.min(" * Suggestion", "Try mkdir -p {0} or fix the report_output_path in {1}\n".format(path_data['given_path'], config_file))
            sys.exit(3)

    return path_data

def create_reports_path(msg, data):
    msg.min("Report Files Directory", data['dirpath_reports'])
    try:
        os.makedirs(data['dirpath_reports'], exist_ok=True)
    except OSError as e:
        msg.min(" ERROR:", "{}".format(str(e)))
        sys.exit(13)

    return

def save_report_data(msg, report_data):
    report_file = report_data['source_data']['dirpath_reports'] + "/report_data.json"
    try:
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent = 4)
    except Exception as e:
        msg.min(" ERROR:", "Cannot write {} file - {}".format(report_file, str(e)))
        sys.exit(13)
    msg.normal("Cluster Report Data File", report_file)


