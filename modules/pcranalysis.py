# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#-*- coding: utf-8 -*-
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
import suse_kb

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
        count = {
            'total': len(patterns),
            'current': 0,
        }
        for key, value in patterns.items():
            count['current'] += 1
            key(count)

    def __common_pattern_0(self, count):
        key = 'common_pattern_0'
        num_tids = 10
        result = {
            'title': "Fencing Resource Required",
            'description': 'Clusters are supported when a stonith fencing resource is enabled.',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Fencing',
            'subcomponent': 'All',
            'applicable': False,
            'kb_search_terms': "stonith resource not enabled unsupported",
            'kb_search_results': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(count['current'], count['total']), result['title'])
        if self.report_data['cluster']['stonith']['enabled'] is False:
            result['applicable'] = True
            result['kb_search_results'] = suse_kb.search_kb(result['product'], result['kb_search_terms'], num_tids)
        self.analysis_data['results'][key] = result

    def __common_pattern_1(self, count):
        key = 'common_pattern_1'
        result = {
            'title': "",
            'description': '',
            'product': '',
            'component': '',
            'subcomponent': '',
            'applicable': False,
            'kb_search_terms': "",
            'kb_search_results': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(count['current'], count['total']), result['title'])
        self.analysis_data['results'][key] = result


