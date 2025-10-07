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
    TID_MAX = 10

    def __init__(self, msg, report_data):
        self.msg = msg
        self.report_data = report_data
        self.analysis_data = {
            'timeAnalysis': '',
            'results': {},
        }
        self.pattern_manifest = {
            self.__common_pattern_0: True,
            self.__common_pattern_1: True,
        }
        self.count = {
            'total': len(self.pattern_manifest),
            'current': 0,
        }
        self.analysis_datetime = datetime.datetime.now()
        self.analysis_data['timeAnalysis'] = str(self.analysis_datetime.year) + "-" + str(self.analysis_datetime.month).zfill(2) + "-" + str(self.analysis_datetime.day).zfill(2) + " " + str(self.analysis_datetime.hour).zfill(2) + ":" + str(self.analysis_datetime.minute).zfill(2) + ":" + str(self.analysis_datetime.second).zfill(2)

    def is_valid(self):
        return self.report_data['source_data']['valid']

    def get_results(self):
        return self.analysis_data

    def get_pattern_count(self):
        return self.count['total']

    def save_results(self):
        report_file = self.report_data['source_data']['dirpath_reports'] + "/analysis_data.json"
        try:
            with open(report_file, "w") as f:
                json.dump(self.analysis_data, f, indent = 4)
        except Exception as e:
            self.msg.min(" ERROR:", "Cannot write {} file - {}".format(report_file, str(e)))
            sys.exit(13)
        self.msg.normal("Cluster Analysis Data File", report_file)

    def analyze(self):
        if self.report_data['source_data']['search_tids']:
            self.msg.min("Cluster Data", "Analyzing")
        else:
            self.msg.min("Cluster Data", "Analyzing, TID Searching Disabled")
        self.__apply_common_patterns()

    def __apply_common_patterns(self):
        self.msg.normal("Common Patterns", "Applying")
        for common_pattern, value in self.pattern_manifest.items():
            self.count['current'] += 1
            common_pattern()

    def __set_applicable(self, result, preferred):
        num_tids = self.TID_MAX
        result['applicable'] = True
        if self.report_data['source_data']['search_tids']:
            num_tids -= len(preferred)
            tids = suse_kb.search_kb(result['product'], result['kb_search_terms'], num_tids)
        else:
            tids = {}
        result['kb_search_results'] = {**preferred, **tids}
        return result

#################################################################################################
# Common Pattern Definitions
#################################################################################################

    def __common_pattern_0(self):
        key = 'common_pattern_0'
        num_tids = self.TID_MAX
        result = {
            'title': "Fencing Resource Required",
            'description': 'Clusters are supported when a stonith fencing resource is enabled.',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Fencing',
            'subcomponent': 'STONITH',
            'applicable': False,
            'kb_search_terms': "stonith resource not enabled unsupported",
            'suggestions': {}
        }
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Hardware Requirements, Node fencing/STONITH",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-requirements.html",
            },
        }

        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        if self.report_data['cluster']['stonith']['enabled'] is False:
            result = self.__set_applicable(result, preferred)
        self.analysis_data['results'][key] = result

    def __common_pattern_1(self):
        key = 'common_pattern_1'
        result = {
            'title': "Split Brain Detection",
            'description': 'Detected possible split brain cluster',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Fencing',
            'subcomponent': 'Split Brain',
            'applicable': False,
            'kb_search_terms': "troubleshooting stonith split brain",
            'suggestions': {}
        }
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Fencing and STONITH",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-fencing.html",
            },
        }
        dc_list = []

        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        for node in self.report_data['cluster']['nodes']:
            if self.report_data['cluster']['nodes'][node]['is_dc_crm'] or self.report_data['cluster']['nodes'][node]['is_dc_local']:
                dc_list.append(node)
        if len(dc_list) > 1:
            result['description'] = result['description'] + " per DC on nodes: " + " ".join(dc_list)
            result = self.__set_applicable(result, preferred)
        self.analysis_data['results'][key] = result


