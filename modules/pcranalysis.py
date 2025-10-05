'''
Pacemaker Cluster Report Analysis Module
Copyright (c) 2025 SUSE LLC

Module of functions that look for common cluster issues and suggestions.
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
__date_modified__ = '2025 Oct 01'
__version__       = '0.0.1'

# IMPORTS
import os
import re
import sys
import json
import datetime
from distutils.version import LooseVersion

# CONSTANTS

# COMMON ISSUES

class PacemakerClusterAnalysis():
    '''
    Analyzes the report_data from the cluster report files for known issues.
    '''
    GITHUB_OWNER = 'https://github.com/openSUSE/'

    def __init__(self, msg, report_data):
        self.msg = msg
        self.report_data = report_data
        self.analysis_data = {
            'timeAnalysis': '',
            'results': {},
        }
        
        self.analysis_datetime = datetime.datetime.now()
        self.analysis_data['timeAnalysis'] = str(self.analysis_datetime.year) + "-" + str(self.analysis_datetime.month).zfill(2) + "-" + str(self.analysis_datetime.day).zfill(2) + " " + str(self.analysis_datetime.hour).zfill(2) + ":" + str(self.analysis_datetime.minute).zfill(2) + ":" + str(self.analysis_datetime.second).zfill(2)
        self.common_patterns_total = 1

    def is_valid(self):
        return self.report_data['source_data']['valid']

    def get_results(self):
        return self.analysis_data

    def save_results(self):
        report_file = self.report_data['source_data']['dirpath_reports'] + "/analysis_data.json"
        try:
            with open(report_file, "w") as f:
                json.dump(self.analysis_data, f, indent = 4)
        except Exception as e:
            self.msg.min(" ERROR:", "Cannot write {} file - {}".format(report_file, str(e)))
            sys.exit(13)
        self.msg.min("Cluster Analysis Data File", report_file)

    def analyze(self):
        self.msg.min("Cluster Data", "Analyzing")
        self.__apply_common_patterns()

    def __apply_common_patterns(self):
        self.msg.normal("Common Patterns", "Applying")
        patterns = {
            self.__common_pattern_0: True,
            self.__common_pattern_1: True,
        }
        count_total = len(patterns)
        count_current = 0
        for key, value in patterns.items():
            count_current += 1
            key()

    def __common_pattern_0(self):
        key = 'common_pattern_0'
        result = {
            'title': "Fencing Resource Required",
            'product': 'HAE15ALL',
            'component': 'Fencing',
            'subcomponent': 'All',
            'applicable': False,
            'description': 'Clusters are supported when a stonith fencing resource is enabled.',
            'kb_search_terms': "stonith resource not enabled",
            'kb_search_results': {}
        }
        if self.report_data['cluster']['stonith']['enabled'] is False:
            result['applicable'] = True
        self.analysis_data['results'][key] = result

    def __common_pattern_1(self):
        key = 'common_pattern_1'
        result = {
            'title': "",
            'product': '',
            'component': '',
            'subcomponent': '',
            'applicable': False,
            'description': '',
            'kb_search_terms': "",
            'kb_search_results': {}
        }


