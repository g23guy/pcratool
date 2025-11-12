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
__date_modified__ = '2025 Nov 11'
__version__       = '0.0.2'

# IMPORTS
import sys
import json
from datetime import datetime as dt

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
            'time_analyzed': '',
            'patterns_total': 0,
            'patterns_applied': 0,
            'patterns_applied_keys': [],
            'results': {},
        }
        self.pattern_manifest = {
            self.__cpat1: True,
            self.__cpat2: True,
            self.__cpat3: True,
            self.__cpat4: True,
            self.__cpat5: True,
            self.__cpat6: True,
            self.__cpat7: True,
        }
        self.count = {
            'total': len(self.pattern_manifest),
            'current': 0,
        }
        self.analyzed = dt.now()
        self.analysis_data['time_analyzed'] = str(self.analyzed.year) + "-" + str(self.analyzed.month).zfill(2) + "-" + str(self.analyzed.day).zfill(2) + " " + str(self.analyzed.hour).zfill(2) + ":" + str(self.analyzed.minute).zfill(2) + ":" + str(self.analyzed.second).zfill(2)
        self.analysis_data['patterns_total'] = self.count['total']

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

    def __apply_common_patterns(self):
        self.msg.normal("Common Patterns", "Applying")
        for common_pattern in self.pattern_manifest.keys():
            self.count['current'] += 1
            common_pattern()

    def __set_applicable(self, result, preferred, key):
        num_tids = self.TID_MAX
        result['applicable'] = True
        self.analysis_data['patterns_applied'] += 1
        self.analysis_data['patterns_applied_keys'].append(key)
        if self.report_data['source_data']['search_tids']:
            num_tids -= len(preferred)
            tids = suse_kb.search_kb(result['product'], result['kb_search_terms'], num_tids)
        else:
            tids = {}
        result['kb_search_results'] = {**preferred, **tids}
        return result

    def analyze(self):
        if self.report_data['source_data']['search_tids']:
            self.msg.min("Cluster Data", "Analyzing")
        else:
            self.msg.min("Cluster Data", "Analyzing, TID Searching Disabled")
        self.__apply_common_patterns()
        self.msg.min("Cluster Data", "Total Patterns Evaluated: {}, Applicable to Cluster: {}".format(self.analysis_data['patterns_total'], self.analysis_data['patterns_applied']))
        if( self.msg.get_level() >= self.msg.LOG_NORMAL ):
            total_keys = len(self.analysis_data['patterns_applied_keys'])
            count_keys = 0
            for key in self.analysis_data['patterns_applied_keys']:
                count_keys += 1
                self.msg.normal(" Applicable Pattern [{}/{}]".format(count_keys, total_keys), self.analysis_data['results'][key]['description'])

#################################################################################################
# Common Pattern Definitions
#################################################################################################
# self.report_data['cluster']['nodes'][node]['sysinfo']
# self.report_data['cluster']['nodes'][node]['sysstats']
# self.report_data['cluster']['nodes'][node]['is_included']
# self.report_data['cluster']['stonith']['sbd']['found']
# self.report_data['cluster']['cnt_nodes_configured']
# self.report_data['cluster']['cnt_nodes_included']

    def __cpat7(self):
        key = 'cpat7'
        result = {
            'title': "Consistent Package Versions Across Nodes",
            'description': 'Nodes with inconsistent package versions: None',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Maintenance',
            'subcomponent': 'Update',
            'applicable': False,
            'kb_search_terms': "updating cluster software",
            'suggestions': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Upgrading your cluster and updating software packages",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-migration.html",
            },
        }

        pkg_version_found = False
        pkg_versions = {
            'kernel': '', 
            'corosync': '', 
            'pacemaker': '', 
            'resource-agents': '', 
            'sbd': '', 
        }
        dirty_nodes = {}
        # Enhancement request: select nodes that have old package versions compared to other nodes
        for node in self.report_data['cluster']['nodes']:
            if( self.report_data['cluster']['nodes'][node]['is_included'] is True ):
                for pkg in pkg_versions.keys():
                    if( pkg_version_found is True ):
                        if( pkg in self.report_data['cluster']['nodes'][node]['sysinfo'] ):
                            if( pkg_versions[pkg] != self.report_data['cluster']['nodes'][node]['sysinfo'][pkg] ):
                                dirty_nodes[node] = True
                    else:
                        if( pkg in self.report_data['cluster']['nodes'][node]['sysinfo'] ):
                            pkg_versions[pkg] = self.report_data['cluster']['nodes'][node]['sysinfo'][pkg]
                pkg_version_found = True
        if( dirty_nodes ):
            node_list = list(dirty_nodes.keys())
            result['description'] = "Inconsistent package versions: {}".format(' '.join(node_list))
            result = self.__set_applicable(result, preferred, key)
        self.analysis_data['results'][key] = result

    def __cpat6(self):
        key = 'cpat6'
        result = {
            'title': "Node Directory Permissions",
            'description': 'Nodes with invalid permissions.txt: None',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Node',
            'subcomponent': 'Permissions',
            'applicable': False,
            'kb_search_terms': "permissions.txt crm report",
            'suggestions': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        preferred = {}

        dirty_nodes = []
        for node in self.report_data['cluster']['nodes']:
            if( 'permissions_valid' in self.report_data['cluster']['nodes'][node] ):
                if( self.report_data['cluster']['nodes'][node]['permissions_valid'] is False ):
                    dirty_nodes.append(node)
        if( dirty_nodes ):
            result = self.__set_applicable(result, preferred, key)
            result['description'] = "Fix permissions or ownership described in permissions.txt for nodes: {}".format(' '.join(dirty_nodes))
        self.analysis_data['results'][key] = result

    def __cpat5(self):
        key = 'cpat5'
        result = {
            'title': "Cluster Standby Mode",
            'description': 'Nodes in standby mode: None',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Maintenance',
            'subcomponent': 'Standby',
            'applicable': False,
            'kb_search_terms': "cluster standby mode",
            'suggestions': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Executing maintenance tasks",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-maintenance.html",
            },
        }

        nodes_in_standy = len(self.report_data['cluster']['nodes_standby'])
        if( nodes_in_standy > 0 ):
            result = self.__set_applicable(result, preferred, key)
            result['description'] = "Nodes in standby mode: {}".format(' '.join(self.report_data['cluster']['nodes_standby']))
        self.analysis_data['results'][key] = result

    def __cpat4(self):
        key = 'cpat4'
        result = {
            'title': "Cluster Maintenance Mode",
            'description': 'In Maintenance Mode, Cluster: False, Nodes: None',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Maintenance',
            'subcomponent': 'Mode',
            'applicable': False,
            'kb_search_terms': "cluster maintenance mode",
            'suggestions': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Executing maintenance tasks",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-maintenance.html",
            },
        }

        nodes_in_maint = len(self.report_data['cluster']['nodes_maintenance'])
        if( self.report_data['cluster']['cluster_maintenance'] is True ):
            result = self.__set_applicable(result, preferred, key)
            if( nodes_in_maint > 0 ):
                result['description'] = "In Maintenance Mode, Cluster: True, Nodes: {}".format(' '.join(self.report_data['cluster']['nodes_maintenance']))
            else:
                result['description'] = "In Maintenance Mode, Cluster: True, Nodes: None"
        elif( nodes_in_maint > 0 ):
            result = self.__set_applicable(result, preferred, key)
            result['description'] = "In Maintenance Mode, Cluster: False, Nodes: {}".format(' '.join(self.report_data['cluster']['nodes_maintenance']))
        self.analysis_data['results'][key] = result

    def __cpat3(self):
        key = 'cpat3'
        result = {
            'title': "Verify Clean SBD",
            'description': 'SBD nodes with dirty slots: None',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Fencing',
            'subcomponent': 'SBD',
            'applicable': False,
            'kb_search_terms': "stonith sbd nodes not clear",
            'suggestions': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Storage protection and SBD",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-storage-protect.html",
            },
        }

        unclean_nodes = []
        if( self.report_data['cluster']['stonith']['sbd']['found'] is True and self.report_data['cluster']['stonith']['sbd']['all_clear'] == 0 ):
            for node in self.report_data['cluster']['stonith']['sbd']['nodes']:
                if( self.report_data['cluster']['stonith']['sbd']['nodes'][node]['is_clear'] is False ):
                    unclean_nodes.append(node)
            result = self.__set_applicable(result, preferred, key)
            result['description'] = "SBD nodes with dirty slots: {}".format(' '.join(unclean_nodes))
        self.analysis_data['results'][key] = result

    def __cpat2(self):
        key = 'cpat2'
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
        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Fencing and STONITH",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-fencing.html",
            },
        }
        dc_list = []

        for node in self.report_data['cluster']['nodes']:
            if self.report_data['cluster']['nodes'][node]['is_dc_crm'] or self.report_data['cluster']['nodes'][node]['is_dc_local']:
                dc_list.append(node)
        if len(dc_list) > 1:
            result['description'] = result['description'] + ", multiple DC nodes: " + " ".join(dc_list)
            result = self.__set_applicable(result, preferred, key)
        self.analysis_data['results'][key] = result

    def __cpat1(self):
        key = 'cpat1'
        result = {
            'title': "Fencing Resource Required",
            'description': 'Missing STONITH resource required for supportability',
            'product': 'SUSE Linux Enterprise High Availability Extension',
            'component': 'Fencing',
            'subcomponent': 'STONITH',
            'applicable': False,
            'kb_search_terms': "stonith resource not enabled unsupported",
            'suggestions': {}
        }
        self.msg.verbose(" Searching [{}/{}]".format(self.count['current'], self.count['total']), result['title'])
        preferred = {
            "doc1": {
                "id": "Documentation",
                "title": "Hardware Requirements, Node fencing/STONITH",
                "url": "https://documentation.suse.com/sle-ha/15-SP7/html/SLE-HA-all/cha-ha-requirements.html",
            },
        }

        if self.report_data['cluster']['stonith']['enabled'] is False:
            result = self.__set_applicable(result, preferred, key)
        self.analysis_data['results'][key] = result


