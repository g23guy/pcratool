# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#-*- coding: utf-8 -*-
'''
Pacemaker Cluster Report Cluster Module
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
import re
import sys
import xml.dom.minidom
from datetime import datetime as dt

def _write_diff_file(msg, filename, filepath, diff_content):
    msg.normal(" Differences Data File", filepath)
    try:
        with open(filepath, "w") as f:
            for line in diff_content:
                f.write(line + "\n")
            f.close()
    except Exception as e:
        msg.min(" Cannot write file {}".format(filename), "{}".format(str(e)))

def _get_cluster_basics(msg, file_data, cluster_data):
    ##### description.txt
    filename = "description.txt"
    msg.debug("_get_cluster_basics: File", filename)
    filepath = file_data['dirpath_data_source'] + "/" + filename
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.min(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    if filedata:
        for line in filedata:
            if line.startswith("Date: "):
                cluster_data['hb_report_date'] = line.split(' ', 1)[1]
                msg.debug("> get hb_report_date", cluster_data['hb_report_date'])
            if line.startswith("By: "):
                cluster_data['hb_report_by'] = line.split(' ', 1)[1]
                msg.debug("> get hb_report_by", cluster_data['hb_report_by'])

    ##### analysis.txt
    msg.min("Analysis Files", "Evaluating Differences")
    filename = "analysis.txt"
    msg.debug("_get_cluster_basics: File", filename)
    filepath = file_data['dirpath_data_source'] + "/" + filename
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.min(" Missing {}".format(filename), "{}".format(str(e)))
        cluster_data['data_complete'] = False
        msg.min(" WARNING:", "Cluster data incomplete, no {} file found.".format(filename))
        msg.min("          All cluster_data[insync_*] values are wrong.")
        filedata = ''

    in_state = False
    diff_file = ''
    diff_content = []
    filepath_diff = ''
    next_line = ''
    if filedata:
        for i, line in enumerate(filedata):
            if i < len(filedata) - 1:  # Check if a next element exists
                next_line = filedata[i + 1]
            else:
                next_line = ''

            if in_state:
                if next_line.startswith('Diff') or next_line.startswith('Checking problems with '):
                    filepath_diff = file_data['dirpath_reports'] + "/" + diff_file
                    _write_diff_file(msg, diff_file, filepath_diff, diff_content)
                    cluster_data['diffs'][diff_key] = {}
                    cluster_data['diffs'][diff_key]['filepath_diff'] = filepath_diff
                    cluster_data['diffs'][diff_key]['count'] = len(diff_content)
                    in_state = False
                    diff_file = ''
                    diff_content = []
                else:
                    diff_content.append(line)
            else:
                if "Diff members.txt" in line:
                    msg.debug("> evaluate", "insync_members_txt")
                    if "OK" in line:
                        cluster_data['insync_members_txt'] = True
                    else:
                        cluster_data['insync_members_txt'] = False
                        in_state = True
                        diff_file = "diff_members.txt"
                        diff_key = "diff_members_txt"
                        msg.debug(">", "differences found")

                if "Diff crm_mon.txt" in line:
                    msg.debug("> evaluate", "insync_crm_mon_txt")
                    if "OK" in line:
                        cluster_data['insync_crm_mon_txt'] = True
                    else:
                        cluster_data['insync_crm_mon_txt'] = False
                        in_state = True
                        diff_file = "diff_crm_mon.txt"
                        diff_key = "diff_crm_mon_txt"
                        msg.debug(">", "differences found")

                if "Diff corosync.conf" in line:
                    msg.debug("> evaluate", "insync_corosync_conf")
                    if "OK" in line:
                        cluster_data['insync_corosync_conf'] = True
                    else:
                        cluster_data['insync_corosync_conf'] = False
                        in_state = True
                        diff_file = "diff_corosync_conf.txt"
                        diff_key = "diff_corosync_conf"
                        msg.debug(">", "differences found")

                if "Diff sysinfo.txt" in line:
                    msg.debug("> evaluate", "insync_sysinfo_txt")
                    if "OK" in line:
                        cluster_data['insync_sysinfo_txt'] = True
                    else:
                        cluster_data['insync_sysinfo_txt'] = False
                        in_state = True
                        diff_file = "diff_sysinfo.txt"
                        diff_key = "diff_sysinfo_txt"
                        msg.debug(">", "differences found")

                if "Diff cib.xml" in line:
                    msg.debug("> evaluate", "insync_cib_xml")
                    if "OK" in line:
                        cluster_data['insync_cib_xml'] = True
                    else:
                        cluster_data['insync_cib_xml'] = False
                        in_state = True
                        diff_file = "diff_cib_xml.txt"
                        diff_key = "diff_cib_xml"
                        msg.debug(">", "differences found")

    return cluster_data

def _parse_permissions_txt(msg, dirpath, node_name, cluster_data, found_permissions):
    ##### permissions.txt
    filename = "permissions.txt"
    filepath = dirpath + "/" + filename
    msg.verbose(" Parsing file", filepath)

    msg.debug("> evaluate", "permissions_valid")
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        cluster_data['nodes'][node_name]['permissions_valid'] = None
        filedata = ''

    if filedata:
        found_permissions = True
        cluster_data['nodes'][node_name]['permissions_valid'] = True
        for line in filedata:
            if "OK" not in line:
                cluster_data['nodes'][node_name]['permissions_valid'] = False
                cluster_data['permissions_valid_all_nodes'] = 0

    return [cluster_data, found_permissions]

def _parse_sysinfo_txt(msg, dirpath, node_name, cluster_data, found_sysinfo):
    ##### sysinfo.txt
    filename = "sysinfo.txt"
    filepath = dirpath + "/" + filename
    msg.verbose(" Parsing file", filepath)
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    tmp_dist_list = []
    if filedata:
        found_sysinfo = True
        msg.debug(">", "pkg versions and summary info")
        if 'sysinfo' not in cluster_data['nodes'][node_name]:
            cluster_data['nodes'][node_name]['sysinfo'] = {}
        for line in filedata:
            line = line.lstrip()
            if line.startswith("CRM Version: "):
                cluster_data['nodes'][node_name]['sysinfo']['crm'] = line.split()[2]

            if line.startswith("corosync "):
                cluster_data['nodes'][node_name]['sysinfo']['corosync'] = line.split()[1]
                tmp_dist_list = line.split()
                del tmp_dist_list[-1]
                del tmp_dist_list[0:3]
            elif re.search(r"^corosync-[0-9]", line):
                tmp_ver1 = line.split('-', 1)[1]
                tmp_ver2 = tmp_ver1.split('.')
                del tmp_ver2[-1]
                tmp_ver1 = '.'.join(tmp_ver2)
                cluster_data['nodes'][node_name]['sysinfo']['corosync'] = tmp_ver1

            if line.startswith("pacemaker "):
                cluster_data['nodes'][node_name]['sysinfo']['pacemaker'] = line.split()[1]
            elif re.search(r"^pacemaker-[0-9]", line):
                tmp_ver1 = line.split('-', 1)[1]
                tmp_ver2 = tmp_ver1.split('.')
                del tmp_ver2[-1]
                tmp_ver1 = '.'.join(tmp_ver2)
                cluster_data['nodes'][node_name]['sysinfo']['pacemaker'] = tmp_ver1

            if line.startswith("resource-agents "):
                cluster_data['nodes'][node_name]['sysinfo']['resource-agents'] = line.split()[1]
            elif re.search(r"^resource-agents-[0-9]", line):
                tmp_ver1 = line.split('-', 2)[2]
                tmp_ver2 = tmp_ver1.split('.')
                del tmp_ver2[-1]
                tmp_ver1 = '.'.join(tmp_ver2)
                cluster_data['nodes'][node_name]['sysinfo']['resource-agents'] = tmp_ver1

            if line.startswith("sbd "):
                cluster_data['nodes'][node_name]['sysinfo']['sbd'] = line.split()[1]
            elif re.search(r"^sbd-[0-9]", line):
                tmp_ver1 = line.split('-', 1)[1]
                tmp_ver2 = tmp_ver1.split('.')
                del tmp_ver2[-1]
                tmp_ver1 = '.'.join(tmp_ver2)
                cluster_data['nodes'][node_name]['sysinfo']['sbd'] = tmp_ver1

            if line.startswith("Platform: "):
                cluster_data['nodes'][node_name]['sysinfo']['platform'] = line.split()[-1]
            if line.startswith("Kernel release: "):
                cluster_data['nodes'][node_name]['sysinfo']['kernel'] = line.split()[-1]
            if line.startswith("Architecture: "):
                cluster_data['nodes'][node_name]['sysinfo']['arch'] = line.split()[-1]
            if line.startswith("Distribution: "):
                dist = line.split(' ', 1)[1]
                if "SUSE Linux Enterprise" in dist:
                    last_word = dist.split()[-1]
                    if "SP" in last_word:
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_major'] = dist.split()[-2]
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_minor'] = last_word.replace("SP", '')
                        cluster_data['nodes'][node_name]['sysinfo']['distribution'] = dist
                    else:
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_major'] = dist.split()[-1]
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_minor'] = "0"
                        cluster_data['nodes'][node_name]['sysinfo']['distribution'] = dist
                else:
                    if tmp_dist_list:
                        cluster_data['nodes'][node_name]['sysinfo']['distribution'] = " ".join(tmp_dist_list)
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_major'] = tmp_dist_list[-1]
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_minor'] = ''
                    else:
                        cluster_data['nodes'][node_name]['sysinfo']['distribution'] = ''
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_major'] = ''
                        cluster_data['nodes'][node_name]['sysinfo']['os_version_minor'] = ''
                msg.verbose(" Distribution found", cluster_data['nodes'][node_name]['sysinfo']['distribution'])

    return [cluster_data, found_sysinfo]

def _get_sysstats_section(msg, filedata, section):
    content = []
    found = False
    in_section = False
    next_line = ''

    for i, line in enumerate(filedata):
        if i < len(filedata) - 1:  # Check if a next element exists
            next_line = filedata[i + 1]
        else:
            next_line = ''

        if in_section:
            if next_line.startswith('#####'):
                in_section = False
            else:
                content.append(line)
                found = True
        else:
            if line.startswith('#####') and section in line:
                in_section = True

    return [content, found]

def _parse_sysstats_txt(msg, dirpath, node_name, cluster_data, found_sysstats):
    ##### sysstats.txt
    filename = "sysstats.txt"
    filepath = dirpath + "/" + filename
    msg.verbose(" Parsing file", filepath)
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    if filedata:
        found_sysstats = True
        if "sysstats" not in cluster_data['nodes'][node_name]:
            cluster_data['nodes'][node_name]['sysstats'] = {}

        # uptime
        uptime_info, found = _get_sysstats_section(msg, filedata, '"uptime"')
        cluster_data['nodes'][node_name]['sysstats']['uptime'] = -1 # in minutes
        cluster_data['nodes'][node_name]['sysstats']['tasks'] = {'load_average': []} # the average number of jobs in the run queue over the last 1, 5 and 15 minutes.
        if found is True:
            for entry in uptime_info:
                if 'average' in entry:
                    updays = 0
                    uphrs = 0
                    upmin = 0
                    values = re.split('[:,]', entry)
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['load_average'].append(float(values[-3])) # last 1 minute, index 0
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['load_average'].append(float(values[-2])) # last 5 minutes, index 1
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['load_average'].append(float(values[-1])) # last 15 minutes, index 2
                    values = entry.split('up')[1].split(",")[0]
                    if "days" in values:
                        updays = values.split("days")[0]
                        uphrs, upmin = values.split("days")[1].split(":")
                    elif "day" in values:
                        updays = 1
                        uphrs, upmin = values.split("day")[1].split(":")
                    else:
                        uphrs, upmin = values.split(":")
                    updays = int(updays)
                    uphrs = int(uphrs)
                    upmin = int(upmin)
                    upall = (updays * 1440) + (uphrs * 60) + upmin
                    cluster_data['nodes'][node_name]['sysstats']['uptime'] = upall

        # cpuinfo
        cpu_info, found = _get_sysstats_section(msg, filedata, "cat /proc/cpuinfo")
        cluster_data['nodes'][node_name]['sysstats']['cpu'] = { 'count': 0 }
        if found is True:
            for entry in cpu_info:
                if entry.startswith("processor"):
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['count'] += 1

        # memory from top output
        top_info, found = _get_sysstats_section(msg, filedata, "top -b -n")
        cluster_data['nodes'][node_name]['sysstats']['tasks'].update({'total': -1, 'running': -1, 'sleeping': -1, 'stopped': -1, 'zombie': -1})
        cluster_data['nodes'][node_name]['sysstats']['cpu'].update({'user': -1.0, 'system': -1.0, 'nice': -1.0, 'idle': -1.0, 'wait': -1.0, 'hard_int': -1.0, 'soft_int': -1.0, 'steal_time': -1.0})
        cluster_data['nodes'][node_name]['sysstats']['mem'] = { 'total': -1, 'used': -1, 'avail': -1, 'avail_percent': -1 }
        cluster_data['nodes'][node_name]['sysstats']['swap'] = { 'total': -1, 'used': -1 }

        if found is True:
            for entry in top_info:
                if entry.startswith("Tasks:"):
                    value = entry.split()
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['total'] = int(value[1])
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['running'] = int(value[3])
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['sleeping'] = int(value[5])
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['stopped'] = int(value[7])
                    cluster_data['nodes'][node_name]['sysstats']['tasks']['zombie'] = int(value[9])
                if entry.startswith('%Cpu(s):'):
                    value = entry.split(',')
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['user'] = float(value[0].split()[1])
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['system'] = float(value[1].split()[0])
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['nice'] = float(value[2].split()[0])
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['idle'] = float(value[3].split()[0])
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['wait'] = float(value[4].split()[0])
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['hard_int'] = float(value[5].split()[0])
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['soft_int'] = float(value[6].split()[0])
                    cluster_data['nodes'][node_name]['sysstats']['cpu']['steal_time'] = float(value[7].split()[0])
                if entry.startswith("MiB Mem"):
                    values = re.split(r"[,:]", entry)
                    for value in values:
                        if "total" in value:
                            if "." in value:
                                mem_value = value.split('.')[0]
                            elif "+" in value:
                                mem_value = value.split('+')[0]
                            cluster_data['nodes'][node_name]['sysstats']['mem']['total'] = int(mem_value)
                        elif "used" in value:
                            if "." in value:
                                mem_value = value.split('.')[0]
                            elif "+" in value:
                                mem_value = value.split('+')[0]
                            cluster_data['nodes'][node_name]['sysstats']['mem']['used'] = int(mem_value)
                if entry.startswith("MiB Swap"):
                    values = re.split(r"[,:]", entry)
                    for value in values:
                        if "total" in value:
                            if "." in value:
                                mem_value = value.split('.')[0]
                            elif "+" in value:
                                mem_value = value.split('+')[0]
                            cluster_data['nodes'][node_name]['sysstats']['swap']['total'] = int(mem_value)
                        elif "avail" in value:
                            values = value.split('d. ') # split the used and available value
                            break
                    for value in values:
                        if "use" in value:
                            if "." in value:
                                mem_value = value.split('.')[0]
                            elif "+" in value:
                                mem_value = value.split('+')[0]
                            cluster_data['nodes'][node_name]['sysstats']['swap']['used'] = int(mem_value)
                        elif "avail" in value:
                            if "." in value:
                                mem_value = value.split('.')[0]
                            elif "+" in value:
                                mem_value = value.split('+')[0]
                            cluster_data['nodes'][node_name]['sysstats']['mem']['avail'] = int(mem_value)

                    cluster_data['nodes'][node_name]['sysstats']['mem']['avail_percent'] = int(100-((cluster_data['nodes'][node_name]['sysstats']['mem']['total'] - cluster_data['nodes'][node_name]['sysstats']['mem']['avail'])*100/cluster_data['nodes'][node_name]['sysstats']['mem']['total']))

    return [cluster_data, found_sysstats]

def _parse_crm_mon_txt(msg, dirpath, node_name, cluster_data, found_crm_mon):
    ##### crm_mon.txt
    filename = "crm_mon.txt"
    filepath = dirpath + "/" + filename
    msg.debug("_parse_crm_mon_txt: File", filename)
    stop_early = False
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    if filedata:
        found_crm_mon = True
        for line in filedata:
            line = line.strip()
            if line.startswith('* '):
                line = line[2:]

            if line.startswith('##'):
                if stop_early:
                    break
                else:
                    stop_early = True
                    continue
            if "Resource management is DISABLED" in line:
                msg.debug(">", "found cluster maintenance status")
                cluster_data['cluster_maintenance'] = True
            if "partition with quorum" in line:
                msg.debug(">", "found quorum status")
                cluster_data['has_quorum'] = True
            if "Current DC" in line:
                dc_node_name = line.split()[2]
                if dc_node_name not in cluster_data['nodes']:
                    msg.debug(">", "Added {} from {}".format(dc_node_name, filename))
                    cluster_data['nodes'][dc_node_name] = {}
                    cluster_data['nodes'][dc_node_name]['is_included'] = False
                msg.debug(">", "Added DC node {} from {}".format(node_name, filename))
                cluster_data['nodes'][dc_node_name]['is_dc_crm'] = True
            if " nodes configured" in line:
                msg.debug(">", "cnt_nodes_configured")
                value = line.split()[0]
                if value.isdigit():
                    cluster_data['cnt_nodes_configured'] = int(value)
            if " resource instances configured" in line:
                msg.debug(">", "cnt_resources_configured")
                value = line.split()[0]
                if value.isdigit():
                    cluster_data['cnt_resources_configured'] = int(value)
            if " resources configured" in line:
                msg.debug(">", "cnt_resources_configured")
                value = line.split()[0]
                if value.isdigit():
                    cluster_data['cnt_resources_configured'] = int(value)
            if "Online: [" in line:
                entry = re.findall(r"\[(.*?)\]", line)
                cluster_data['nodes_online'] = entry[0].strip().split()
                msg.debug("> nodes_online", "added {}".format(cluster_data['nodes_online']))
            if "OFFLINE: [" in line:
                entry = re.findall(r"\[(.*?)\]", line)
                cluster_data['nodes_offline'] = entry[0].strip().split()
                msg.debug("> nodes_offline", "added {}".format(cluster_data['nodes_offline']))
            if "maintenance" in line:
                entry = re.findall(r"Node (.*?): maintenance", line)
                if entry:
                    if entry[0] not in cluster_data['nodes_maintenance']:
                        msg.debug(">", "nodes_maintenance list, appended {}".format(entry[0]))
                        cluster_data['nodes_maintenance'].append(entry[0])
            if "UNCLEAN" in line:
                entry = re.findall(r"Node (.*?): UNCLEAN", line)
                if entry:
                    if entry[0] not in cluster_data['nodes_unclean']:
                        msg.debug(">", "nodes_unclean list, appended {}".format(entry[0]))
                        cluster_data['nodes_unclean'].append(entry[0])
            if "standby" in line:
                entry = re.findall(r"Node (.*?): standby", line)
                if entry:
                    if entry[0] not in cluster_data['nodes_standby']:
                        msg.debug(">", "nodes_standby list, appended {}".format(entry[0]))
                        cluster_data['nodes_standby'].append(entry[0])
            if "pending" in line:
                entry = re.findall(r"Node (.*?): pending", line)
                if entry:
                    if entry[0] not in cluster_data['nodes_pending']:
                        msg.debug(">", "nodes_pending list, appended {}".format(entry[0]))
                        cluster_data['nodes_pending'].append(entry[0])
            if "stonith:" in line:
                cluster_data['stonith']['enabled'] = True
                if "stonith:external/sbd" in line:
                    cluster_data['stonith']['sbd']['found'] = True
                    msg.debug(">", "stonith:external/sbd found")
                else:
                    entry = re.findall(r"\(stonith:(.*)\):", line)
                    if entry:
                        _type = entry[0]
                        if _type not in cluster_data['stonith']:
                            cluster_data['stonith'][_type] = {}
                            cluster_data['stonith'][_type]['found'] = True
                    msg.debug(">", "stonith:{} found".format(_type))


    return [cluster_data, found_crm_mon]

def _parse_members_txt(msg, dirpath, cluster_data, found_members):
    ##### members.txt
    filename = "members.txt"
    filepath = dirpath + "/" + filename
    msg.verbose(" Parse File", filepath)
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    if filedata:
        found_members = True
        node_list = []
        for line in filedata:
            node_list = line.split()
        for node_name in node_list:
            if node_name not in cluster_data['nodes']:
                msg.debug(">", "Added {} from {}".format(node_name, filename))
                cluster_data['nodes'][node_name] = {}
                cluster_data['nodes'][node_name]['is_included'] = False

    return [cluster_data, found_members]

def _get_nodes_system_details(msg, file_data, cluster_data):
    msg.min("System Details", "Gathering per Node")
    found_permissions = False
    found_sysinfo = False
    found_sysstats = False
    subfolders = [ f.path for f in os.scandir(file_data['dirpath_data_source']) if f.is_dir() ]
    for node_data_source in subfolders:
        node_name = os.path.basename(node_data_source)
        msg.verbose("Processing system details", "from {} node directory".format(node_name))
        if node_name not in cluster_data['nodes']:
            cluster_data['nodes'][node_name] = {}
            msg.debug("_get_nodes_system_details:", "Added {} from {}".format(node_name, "directory"))

        cluster_data, found_sysinfo = _parse_sysinfo_txt(msg, node_data_source, node_name, cluster_data, found_sysinfo)
        cluster_data, found_sysstats = _parse_sysstats_txt(msg, node_data_source, node_name, cluster_data, found_sysstats)
        cluster_data, found_permissions = _parse_permissions_txt(msg, node_data_source, node_name, cluster_data, found_permissions)

    if not found_permissions:
        msg.verbose("Warning:", "No permissions.txt file found")
    if not found_sysinfo:
        msg.verbose("Warning:", "No sysinfo.txt file found")

    return cluster_data

def _parse_cib_xml_cfg(msg, dirpath, node_name, cluster_data):
    msg.verbose("Parsing cluster CIB ", "from {} node directory".format(node_name))
    ##### crm_mon.txt
    filename = "cib.xml"
    filepath = dirpath + "/" + filename
    msg.debug("_parse_crm_mon_txt: File", filename)
    stop_early = False
    try:
        with open(filepath) as f:
            #xtree = ET.parse(f)
            xdom = xml.dom.minidom.parse(f)
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ""

    cib_data = {}

    if xdom:
        cib_element = xdom.getElementsByTagName("cib")[0]
        for attr in cib_element.attributes.keys():
            msg.debug("> cib attribute", "{} = {}".format(attr, cib_element.getAttribute(attr)))  
            #if attr in ["crm_feature_set", "cib-last-written", "update-origin", "have-quorum"]:
            cib_data[attr] = cib_element.getAttribute(attr)

        # Walking through cib.xml to get configuration values
        cfg = xdom.getElementsByTagName("configuration")

        cib_data["cluster_property_sets"] = {}
        # Get cluster properties
        crm_configs = cfg[0].getElementsByTagName("crm_config")
        if len(crm_configs) > 0:
            cluster_property_sets  = crm_configs[0].getElementsByTagName("cluster_property_set")
            if len(cluster_property_sets) > 0:
                for cps in cluster_property_sets:
                    for attr in cps.attributes.keys():
                        cib_data["cluster_property_sets"][cps.getAttribute(attr)] = {}
                        nvpairs = cps.getElementsByTagName("nvpair")
                        for nv in nvpairs:
                            nv_name = nv.getAttribute("name")
                            nv_value = nv.getAttribute("value")
                            cib_data["cluster_property_sets"][cps.getAttribute(attr)][nv_name] = nv_value

        # Get node attributes
        nodes_parent = xdom.getElementsByTagName("nodes")
        nodes = nodes_parent[0].getElementsByTagName("node")
        if len(nodes) > 0:
            if "nodes" not in cib_data.keys():
                cib_data["nodes"] = {}
            for node in nodes:
                node_uname= node.getAttribute("uname")
                msg.debug("> cib node", "Found node {}".format(node_uname))
                if node_uname not in cib_data:
                    cib_data["nodes"][node_uname] = {}
                instance_attributes = node.getElementsByTagName("instance_attributes")
                nvpairs = instance_attributes[0].getElementsByTagName("nvpair") 
                for nvp in nvpairs:
                    nv_name = nvp.getAttribute("name")
                    nv_value = nvp.getAttribute("value")
                    cib_data["nodes"][node_uname][nv_name] = nv_value

        # Get resources 
        resources_parent = xdom.getElementsByTagName("resources")
        if len(resources_parent) > 0:
            cib_data["resources"] = {}
            # Get primitives
            primitives = resources_parent[0].getElementsByTagName("primitive")
            if len(primitives) > 0:
                if "primitives" not in cib_data["resources"]:
                    cib_data["resources"]["primitives"] = {}
                for primitive in primitives:
                    primitive_id = primitive.getAttribute("id")
                    cib_data["resources"]["primitives"][primitive_id] = {}
                    for attr in primitive.attributes.keys():
                        if attr not in ["id"]:
                            cib_data["resources"]["primitives"][primitive_id][attr] = primitive.getAttribute(attr)
                        instance_attributes = primitive.getElementsByTagName("instance_attributes")
                        if len(instance_attributes) > 0:
                            cib_data["resources"]["primitives"][primitive_id]["params"] = {}
                            nvpairs = instance_attributes[0].getElementsByTagName("nvpair")
                            for nv in nvpairs:
                                nv_name = nv.getAttribute("name")
                                nv_value = nv.getAttribute("value")
                                cib_data["resources"]["primitives"][primitive_id]["params"][nv_name] = nv_value

            # Get groups
            # Get tags: group > meta_attributes > primitives > instance-attributes > operations > op
            groups = resources_parent[0].getElementsByTagName("group")
            if len(groups) > 0: 
                if "groups" not in cib_data["resources"]:
                    cib_data["resources"]["groups"] = {}
                for group in groups:
                    group_id = group.getAttribute("id")
                    cib_data["resources"]["groups"][group_id] = {}
                    # Get group attributes
                    for attr in group.attributes.keys():
                        if attr not in ["id"]:
                            cib_data["resources"]["groups"][group_id][attr] = group.getAttribute(attr)
                    meta_attributes = group.getElementsByTagName("meta_attributes")
                    if len(meta_attributes) > 0:
                        cib_data["resources"]["groups"][group_id]["meta"] = {}
                        nvpairs = meta_attributes[0].getElementsByTagName("nvpair")
                        for nv in nvpairs:
                            nv_name = nv.getAttribute("name")
                            nv_value = nv.getAttribute("value")
                            cib_data["resources"]["groups"][group_id]["meta"][nv_name] = nv_value
                    # Get primivites under groups
                    group_primitives = group.getElementsByTagName("primitive")
                    if len(group_primitives) > 0:
                        if "primitives" not in cib_data["resources"]["groups"][group_id]:
                            cib_data["resources"]["groups"][group_id]["primitives"] = {}
                        for primitive in group_primitives:
                            primitive_id = primitive.getAttribute("id")
                            cib_data["resources"]["groups"][group_id]["primitives"][primitive_id] = {}
                            # Get primitive attributes
                            for attr in primitive.attributes.keys():
                                if attr not in ["id"]:
                                    cib_data["resources"]["groups"][group_id]["primitives"][primitive_id][attr] = primitive.getAttribute(attr)
                            instance_attributes = primitive.getElementsByTagName("instance_attributes")
                            if len(instance_attributes) > 0:
                                cib_data["resources"]["groups"][group_id]["primitives"][primitive_id]["params"] = {}
                                nvpairs = instance_attributes[0].getElementsByTagName("nvpair")
                                # Get nvpairs under attrs
                                for nv in nvpairs:
                                    nv_name = nv.getAttribute("name")
                                    nv_value = nv.getAttribute("value")
                                    cib_data["resources"]["groups"][group_id]["primitives"][primitive_id]["params"][nv_name] = nv_value
                            # Get operations
                            operations = primitive.getElementsByTagName("operations")
                            ops = operations[0].getElementsByTagName("op")
                            if len(ops) > 0:
                                cib_data["resources"]["groups"][group_id]["primitives"][primitive_id]["operations"] = {}
                                for op in ops:
                                    op_name = op.getAttribute("name")
                                    cib_data["resources"]["groups"][group_id]["primitives"][primitive_id]["operations"][op_name] = {}
                                    for attr in op.attributes.keys():
                                        cib_data["resources"]["groups"][group_id]["primitives"][primitive_id]["operations"][op_name][attr] = op.getAttribute(attr)

            # Get master/slave (multi-state resources)
            masters = resources_parent[0].getElementsByTagName("master")
            if len(masters) > 0:
                cib_data["resources"]["masters"] = {}
            for master in masters:
                master_id = master.getAttribute("id")
                cib_data["resources"]["masters"][master_id] = {}
                meta_attributes = master.getElementsByTagName("meta_attributes")
                if len(meta_attributes) > 0:
                    cib_data["resources"]["masters"][master_id]["meta"] = {}
                    nvpairs = meta_attributes[0].getElementsByTagName("nvpair")
                    for nv in nvpairs:
                        nv_name = nv.getAttribute("name")
                        nv_value = nv.getAttribute("value")
                        cib_data["resources"]["masters"][master_id]["meta"][nv_name] = nv_value
                primitives = master.getElementsByTagName("primitive")
                if len(primitives) > 0:
                    cib_data["resources"]["masters"][master_id]["primitives"] = {}
                    for primitive in primitives:
                        primitive_id = primitive.getAttribute("id")
                        cib_data["resources"]["masters"][master_id]["primitives"][primitive_id] = {}
                        # Get primitive attributes
                        for attr in primitive.attributes.keys():
                            if attr not in ["id"]:
                                cib_data["resources"]["masters"][master_id]["primitives"][primitive_id][attr] = primitive.getAttribute(attr)
                        instance_attributes = primitive.getElementsByTagName("instance_attributes")
                        if len(instance_attributes) > 0:
                            cib_data["resources"]["masters"][master_id]["primitives"][primitive_id]["params"] = {}
                            nvpairs = instance_attributes[0].getElementsByTagName("nvpair")
                            # Get nvpairs under attrs
                            for nv in nvpairs:
                                nv_name = nv.getAttribute("name")
                                nv_value = nv.getAttribute("value")
                                cib_data["resources"]["masters"][master_id]["primitives"][primitive_id]["params"][nv_name] = nv_value
                        # Get operations
                        operations = primitive.getElementsByTagName("operations")
                        ops = operations[0].getElementsByTagName("op")
                        if len(ops) > 0:
                            cib_data["resources"]["masters"][master_id]["primitives"][primitive_id]["operations"] = {}
                            for op in ops:
                                op_name = op.getAttribute("name")
                                cib_data["resources"]["masters"][master_id]["primitives"][primitive_id]["operations"][op_name] = {}
                                for attr in op.attributes.keys():
                                    cib_data["resources"]["masters"][master_id]["primitives"][primitive_id]["operations"][op_name][attr] = op.getAttribute(attr)

            # Get clones
            clones = resources_parent[0].getElementsByTagName("clone")  
            if len(clones) > 0:
                cib_data["resources"]["clones"] = {}
                for clone in clones:
                    clone_id = clone.getAttribute("id")
                    cib_data["resources"]["clones"][clone_id] = {}
                    meta_attributes = clone.getElementsByTagName("meta_attributes")
                    if len(meta_attributes) > 0:
                        cib_data["resources"]["clones"][clone_id]["meta"] = {}
                        nvpairs = meta_attributes[0].getElementsByTagName("nvpair")
                        for nv in nvpairs:
                            nv_name = nv.getAttribute("name")
                            nv_value = nv.getAttribute("value")
                            cib_data["resources"]["clones"][clone_id]["meta"][nv_name] = nv_value
                    primitives = clone.getElementsByTagName("primitive")
                    if len(primitives) > 0:
                        cib_data["resources"]["clones"][clone_id]["primitives"] = {}
                        for primitive in primitives:
                            primitive_id = primitive.getAttribute("id")
                            cib_data["resources"]["clones"][clone_id]["primitives"][primitive_id] = {}
                            # Get primitive attributes
                            for attr in primitive.attributes.keys():
                                if attr not in ["id"]:
                                    cib_data["resources"]["clones"][clone_id]["primitives"][primitive_id][attr] = primitive.getAttribute(attr)
                            instance_attributes = primitive.getElementsByTagName("instance_attributes")
                            if len(instance_attributes) > 0:
                                cib_data["resources"]["clones"][clone_id]["primitives"][primitive_id]["params"] = {}
                                nvpairs = instance_attributes[0].getElementsByTagName("nvpair")
                                # Get nvpairs under attrs
                                for nv in nvpairs:
                                    nv_name = nv.getAttribute("name")
                                    nv_value = nv.getAttribute("value")
                                    cib_data["resources"]["clones"][clone_id]["primitives"][primitive_id]["params"][nv_name] = nv_value
                            # Get operations
                            operations = primitive.getElementsByTagName("operations")
                            ops = operations[0].getElementsByTagName("op")
                            if len(ops) > 0:
                                cib_data["resources"]["clones"][clone_id]["primitives"][primitive_id]["operations"] = {}
                                for op in ops:
                                    op_name = op.getAttribute("name")
                                    cib_data["resources"]["clones"][clone_id]["primitives"][primitive_id]["operations"][op_name] = {}
                                    for attr in op.attributes.keys():
                                        cib_data["resources"]["clones"][clone_id]["primitives"][primitive_id]["operations"][op_name][attr] = op.getAttribute(attr)

        # Get constraints
        constraints = cfg[0].getElementsByTagName("constraints")
        if len(constraints) > 0:
            cib_data["constraints"] = {}
            rsc_colocation = constraints[0].getElementsByTagName("rsc_colocation")
            if len(rsc_colocation) > 0:
                cib_data["constraints"]["colocations"] = {}
                for colocation in rsc_colocation:
                    colocation_id = colocation.getAttribute("id")
                    cib_data["constraints"]["colocations"][colocation_id] = {}
                    for attr in colocation.attributes.keys():
                        cib_data["constraints"]["colocations"][colocation_id][attr] = colocation.getAttribute(attr)

         # Get resource defaults
        rsc_defaults = xdom.getElementsByTagName("rsc_defaults")
        if len(rsc_defaults) > 0:
            cib_data["rsc_defaults"] = {}
            meta_attributes = rsc_defaults[0].getElementsByTagName("meta_attributes")
            if len(meta_attributes) > 0:
                rsc_defaults_id =  meta_attributes[0].getAttribute("id")
                print(f"Resource Defaults ID: {rsc_defaults_id}")
                cib_data["rsc_defaults"][rsc_defaults_id] =   {}
                nvpairs = meta_attributes[0].getElementsByTagName("nvpair")
                if len(nvpairs) > 0:
                    for nv in nvpairs:
                        nv_name = nv.getAttribute("name")
                        nv_value = nv.getAttribute("value")
                        cib_data["rsc_defaults"][rsc_defaults_id][nv_name] = nv_value

        # Get operation defaults
        op_defaults = xdom.getElementsByTagName("op_defaults")
        if len(op_defaults) > 0:
            cib_data["op_defaults"] = {}
            meta_attributes = op_defaults[0].getElementsByTagName("meta_attributes")
            if len(meta_attributes) > 0:
                op_defaults_id =  meta_attributes[0].getAttribute("id")
                print(f"Operation Defaults ID: {op_defaults_id}")
                cib_data["op_defaults"][op_defaults_id] =   {}
                nvpairs = meta_attributes[0].getElementsByTagName("nvpair")
                if len(nvpairs) > 0:
                    for nv in nvpairs:
                        nv_name = nv.getAttribute("name")
                        nv_value = nv.getAttribute("value")
                        cib_data["op_defaults"][op_defaults_id][nv_name] = nv_value

    if cluster_data.get("cib") is None:
        cluster_data["cib"] = cib_data
    if cluster_data.get('insync_cib_xml') is False:
        if cluster_data['nodes'].get(node_name) is None:
            print(f"Node {node_name} not found in cluster_data['nodes'], creating entry.")
            cluster_data['nodes'][node_name] = {}
        cluster_data['nodes'][node_name]['cib'] = cib_data
    #pprint.pprint(cib_data, indent=4)
    #print('-' * 80)
    #pprint.pprint(cluster_data)
    #print("Node: ", node_name)
    return cluster_data

def _parse_cib_xml_node_state(msg, dirpath, node_name, cluster_data):
    msg.verbose("Parsing cluster CIB ", "from {} node directory".format(node_name))
    ##### crm_mon.txt
    filename = "cib.xml"
    filepath = dirpath + "/" + filename
    msg.debug("_parse_crm_mon_txt: File", filename)
    stop_early = False
    try:
        with open(filepath) as f:
            #xtree = ET.parse(f)
            xdom = xml.dom.minidom.parse(f)
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    if cluster_data.get('cib') is None:
        cluster_data['cib'] = {}

    if xdom:
        cib_element = xdom.getElementsByTagName('cib')[0]
        for attr in cib_element.attributes.keys():
            msg.debug("> cib attribute", "{} = {}".format(attr, cib_element.getAttribute(attr)))  
            #if attr in ['crm_feature_set', 'cib-last-written', 'update-origin', 'have-quorum']:
            cluster_data['cib'][attr] = cib_element.getAttribute(attr)

        # walking through cib.xml to get values
        # cib > node_state > transient_attributes > instance_attributes > nvpair
        node_element = xdom.getElementsByTagName('node_state')
        for node in node_element:
            uname =  node.getAttribute("uname")
            if uname not in cluster_data['nodes']:
                cluster_data['nodes'][uname] = {}
            if 'cib_state' not in cluster_data['nodes'][uname]:
                cluster_data['nodes'][uname]['cib_state'] = {}
            for attr in node.attributes.keys():
                    cluster_data['nodes'][uname]['cib_state'][attr] = node.getAttribute(attr)

            trans_attrs = node.getElementsByTagName('transient_attributes')
            for t_attr in trans_attrs:
                cluster_data['nodes'][uname]['cib_node_attrs'] = {}
                for attr in t_attr.attributes.keys():
                    cluster_data['nodes'][uname]['cib_node_attrs'][str(t_attr.getAttribute(attr))] = {}
                    i_attrs = t_attr.getElementsByTagName('instance_attributes')
                    for i_attr in i_attrs:
                       i_attr_id = i_attr.getAttribute('id').split('-')[1]
                       nv_pairs = i_attr.getElementsByTagName('nvpair')
                       for nv in nv_pairs:
                        nv_name = nv.getAttribute('name')
                        nv_value = nv.getAttribute('value')
                        cluster_data['nodes'][uname]['cib_node_attrs'][i_attr_id][nv_name] = nv_value
            
            node_resources = {}
            lrm_resources = node.getElementsByTagName('lrm_resource')
            for lrm in lrm_resources:
                resource_id = lrm.getAttribute("id")
                if resource_id not in node_resources:
                    node_resources[resource_id] = {}
                for attr in ['type', 'class']:
                    node_resources[resource_id][attr] = lrm.getAttribute(attr)
                    lrm_ops = lrm.getElementsByTagName('lrm_rsc_op')

                    if node_resources[resource_id].get('operations') is None:
                        node_resources[resource_id]['operations'] = {}
                    for op in lrm_ops:
                        op_name = op.getAttribute('operation')
                        on_node = op.getAttribute('on_node')
                        rc_code = op.getAttribute('rc-code')
                        node_resources[resource_id]['operations'][op_name] = {
                            'on_node': on_node,
                            'rc_code': rc_code
                        }

            if cluster_data['insync_cib_xml'] is True:
                cluster_data['resources'] = node_resources
                break
            else:
                cluster_data['nodes'][uname]['cib_resources'] = node_resources

    return cluster_data


def _get_nodes_cluster_cib(msg, file_data, cluster_data):
    found_crm_xml = False
    subfolders = [ f.path for f in os.scandir(file_data['dirpath_data_source']) if f.is_dir() ]
    for node_data_source in subfolders:
        node_name = os.path.basename(node_data_source)
        msg.verbose("Processing cluster CIB info", "from {} node directory".format(node_name))
        if node_name not in cluster_data['nodes']:
            cluster_data['nodes'][node_name] = {}
            msg.debug("_get_nodes_cluster_cib:", "Added {} from {}".format(node_name, "directory"))
            cluster_data = _parse_cib_xml_cfg(msg, node_data_source, node_name, cluster_data)

    return cluster_data
            

def _get_nodes_cluster_crm(msg, file_data, cluster_data):
    found_crm_mon = False
    found_members = False
    subfolders = [ f.path for f in os.scandir(file_data['dirpath_data_source']) if f.is_dir() ]
    for node_data_source in subfolders:
        node_name = os.path.basename(node_data_source)
        msg.verbose("Processing cluster CRM info", "from {} node directory".format(node_name))
        if node_name not in cluster_data['nodes']:
            cluster_data['nodes'][node_name] = {}
            msg.debug("_get_nodes_cluster_crm:", "Added {} from {}".format(node_name, "directory"))

        msg.debug("_get_nodes_cluster_crm:", "incremented cnt_nodes_included and set is_included on {}".format(node_name))
        cluster_data['cnt_nodes_included'] += 1
        cluster_data['nodes'][node_name]['is_included'] = True

        ##### DC and RUNNING files
        file_dc = node_data_source + "/DC"
        file_running = node_data_source + "/RUNNING"
        if os.path.exists(file_dc):
            msg.debug(">", "Added DC node {} from {}".format(node_name, "directory"))
            cluster_data['nodes'][node_name]['is_dc_local'] = True
        else:
            cluster_data['nodes'][node_name]['is_dc_local'] = False

        if os.path.exists(file_running):
            cluster_data['nodes'][node_name]['is_running'] = True
        else:
            cluster_data['nodes'][node_name]['is_running'] = False

        cluster_data, found_crm_mon = _parse_crm_mon_txt(msg, node_data_source, node_name, cluster_data, found_crm_mon)
        cluster_data, found_members = _parse_members_txt(msg, node_data_source, cluster_data, found_members)

    # find missing nodes excluded from members.txt or directories
    node_states = ['unclean', 'standby', 'pending', 'maintenance', 'offline', 'online']
    msg.debug("_get_nodes_cluster_crm:", "Find missing nodes from lists")
    for state in node_states:
        check_nodes = "nodes_" + state
        msg.debug("> {}".format(check_nodes), "cluster_data[nodes] {}".format(cluster_data['nodes'].keys()))
        for node_name in cluster_data[check_nodes]:
            if node_name not in cluster_data['nodes']:
                msg.debug(">", "Added {} from {}".format(node_name, check_nodes))
                cluster_data['nodes'][node_name] = {}
                cluster_data['nodes'][node_name]['is_included'] = False

    # if node directories don't have crm_mon.txt, check source directory
    if not found_crm_mon:
        filename = "crm_mon.txt"
        filepath = file_data['dirpath_data_source'] + "/" + filename
        if os.path.exists(filepath):
            msg.verbose("Found {}".format(filename), filepath)
            cluster_data, found_crm_mon = _parse_crm_mon_txt(msg, file_data['dirpath_data_source'], node_name, cluster_data, found_crm_mon)

    if not found_crm_mon:
        msg.min("WARNING:", "Cluster data incomplete, no crm_mon.txt file found.")
    if not found_members:
        msg.verbose("Warning:", "No members.txt file found")

    cluster_data['data_complete'] = found_crm_mon

    return cluster_data

def _parse_sbd_txt(msg, dirpath, cluster_data, found_sbd_txt):
    ##### sbd.txt
    filename = "sbd.txt"
    filepath = dirpath + "/" + filename
    msg.verbose(" Parse File", filepath)
    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    if filedata:
        found_sbd_txt = True
        for line in filedata:
            if line and line[0].isdigit():
                entry = line.split()
                server = entry[1]
                status = entry[2]
                if 'nodes' not in cluster_data['stonith']['sbd']:
                    cluster_data['stonith']['sbd']['nodes'] = {}
                if server not in cluster_data['stonith']['sbd']['nodes']:
                    cluster_data['stonith']['sbd']['nodes'][server] = {'slots': []}
                cluster_data['stonith']['sbd']['nodes'][server]['slots'].append(entry)

    return [cluster_data, found_sbd_txt]

def _parse_sbd(msg, dirpath, cluster_data, found_sbd):
    ##### sbd
    filename = "sbd"
    filepath = dirpath + "/" + filename
    msg.verbose(" Parse File", filepath)

    try:
        with open(filepath) as f:
            filedata = f.read().splitlines()
            f.close()
    except Exception as e:
        msg.verbose(" Missing {}".format(filename), "{}".format(str(e)))
        filedata = ''

    if filedata:
        found_sbd = True
        for line in filedata:
            if line.startswith("#"):
                continue
            line = line.strip()
            if line and "=" in line:
                key, value = line.split('=', 1)
                if 'SBD_DEVICE' in key:
                    device_list = value.strip().strip('"').strip("'").split(';')
                    cluster_data['stonith']['sbd']['config'][key.strip()] = device_list
                else:
                    cluster_data['stonith']['sbd']['config'][key.strip()] = value.strip().strip('"').strip("'")

    return [cluster_data, found_sbd]

def _get_stonith_sbd(msg, file_data, cluster_data):
    subfolders = [ f.path for f in os.scandir(file_data['dirpath_data_source']) if f.is_dir() ]
    found_sbd_txt = False
    found_sbd = False
    cluster_data['stonith']['sbd']['all_clear'] = -1
    for node_data_source in subfolders:
        node_name = os.path.basename(node_data_source)
        msg.verbose("Processing SBD info", "from {} node directory".format(node_name))

        cluster_data, found_sbd_txt = _parse_sbd_txt(msg, node_data_source, cluster_data, found_sbd_txt)
        cluster_data, found_sbd = _parse_sbd(msg, node_data_source, cluster_data, found_sbd)

    if not found_sbd:
        msg.verbose("Warning:", "No sbd configuration file found")
    if found_sbd_txt:
        msg.debug("_get_stonith_sbd:", "Calculating stonith SBD all_clear and is_clear")
        cluster_data['stonith']['sbd']['all_clear'] = 1
        for node_name in cluster_data['stonith']['sbd']['nodes'].keys():
            cluster_data['stonith']['sbd']['nodes'][node_name]['is_clear'] = True
            for status in cluster_data['stonith']['sbd']['nodes'][node_name]['slots']:
                if 'clear' not in status:
                    cluster_data['stonith']['sbd']['nodes'][node_name]['is_clear'] = False
                    cluster_data['stonith']['sbd']['all_clear'] = 0
    else:
        msg.verbose("Warning:", "No sbd.txt configuration file found")

    return cluster_data

def _get_cluster_nodes_state(msg, file_data, cluster_data):
    msg.debug("_get_cluster_nodes_state:", "Determining node states from nodes lists")
    for node_name in cluster_data['nodes'].keys():
        if node_name in cluster_data['nodes_unclean']:
            cluster_data['nodes'][node_name]['is_unclean'] = True
        else:
            cluster_data['nodes'][node_name]['is_unclean'] = False

        if node_name in cluster_data['nodes_pending']:
            cluster_data['nodes'][node_name]['is_pending'] = True
        else:
            cluster_data['nodes'][node_name]['is_pending'] = False

        if node_name in cluster_data['nodes_standby']:
            cluster_data['nodes'][node_name]['is_standby'] = True
        else:
            cluster_data['nodes'][node_name]['is_standby'] = False

        if node_name in cluster_data['nodes_maintenance']:
            cluster_data['nodes'][node_name]['is_maintenance'] = True
        else:
            if cluster_data['cluster_maintenance']:
                cluster_data['nodes'][node_name]['is_maintenance'] = True
            else:
                cluster_data['nodes'][node_name]['is_maintenance'] = False

        if 'is_running' not in cluster_data['nodes'][node_name]:
            msg.debug("> is_running", "Check in nodes_online: {}".format(node_name))
            if node_name in cluster_data['nodes_online']:
                cluster_data['nodes'][node_name]['is_running'] = True
            else:
                cluster_data['nodes'][node_name]['is_running'] = False

        if 'is_dc_local' not in cluster_data['nodes'][node_name]:
            msg.debug("> is_dc_local", "No DC file was found for {}".format(node_name))
            cluster_data['nodes'][node_name]['is_dc_local'] = False

        if 'is_dc_crm' not in cluster_data['nodes'][node_name]:
            msg.debug("> is_dc_crm", "Not Current DC for {} in crm_mon.txt".format(node_name))
            cluster_data['nodes'][node_name]['is_dc_crm'] = False

    return cluster_data

def get_cluster_data(msg, file_data):
    cluster_data = {
        'data_complete': True,
        'nodes': {},
        'stonith': {
            'sbd': {
                'found': False,
                'config': {},
            },
            'enabled': False,
        },
        'diffs': {},
        'cnt_nodes_configured': -1,
        'cnt_nodes_included': 0,
        'cnt_resources_configured': -1,
        'has_quorum': False,
        'cluster_maintenance': False,
        'nodes_online': [],
        'nodes_offline': [],
        'nodes_unclean': [],
        'nodes_pending': [],
        'nodes_standby': [],
        'nodes_maintenance': [],
        'permissions_valid_all_nodes': 1,
        'insync_members_txt': False,
        'insync_crm_mon_txt': False,
        'insync_corosync_conf': False,
        'insync_sysinfo_txt': False,
        'insync_cib_xml': False,
   }

    cluster_data = _get_cluster_basics(msg, file_data, cluster_data)
    cluster_data = _get_nodes_system_details(msg, file_data, cluster_data)
    cluster_data = _get_nodes_cluster_crm(msg, file_data, cluster_data)
    cluster_data = _get_nodes_cluster_cib(msg, file_data, cluster_data)
#    else:
#        cluster_data = _get_nodes_cluster_crm(msg, file_data, cluster_data)
#        cluster_data = _get_nodes_cluster_cib(msg, file_data, cluster_data)

    if cluster_data['stonith']['sbd']['found']:
        cluster_data = _get_stonith_sbd(msg, file_data, cluster_data)
    cluster_data = _get_cluster_nodes_state(msg, file_data, cluster_data)
    if cluster_data['cnt_nodes_configured'] != cluster_data['cnt_nodes_included']:
        cluster_data['permissions_valid_all_nodes'] = -1

    return cluster_data

def synchronize_log_files(msg, report_data):
    msg.min("Log Files", "Combining and Sorting")
    EX_OK = 0
    MAX_HEADER_LINES = 100
    date_formats = [
    #   List of all possible log file data formats
    #   ['date format', string trim amount left to right, unless negative which if right to left],
        [],
        ['%Y-%m-%dT%H:%M:%S.%f', 26],
        ['%b %d %H:%M:%S.%f', 19],
        ['%b %d %H:%M:%S', 15],
    ]
    log_files = {
    #   The date format to use for each log file and the preferred order to test which is used
    #   'log file': [list of indeces to possible date_formats],
        'pacemaker.log': [2, 3, 1],
        'corosync.log': [3, 2, 1],
        'journal_corosync.log': [1, 2, 3],
        'journal_pacemaker.log': [1, 2, 3],
        'journal_sbd.log': [1, 2, 3],
        'ha-log.txt': [1, 2, 3],
    }
    f_names = []

    def _get_date_format(f_path, date_formats, eval_order):
        header_lines = []
        date_info = []
        idx_date = 0
        empty = 0
        len_fnames = 0

        # Read the first MAX_HEADER_LINES header_lines to determine the date format from the f_path given
        with open(f_path, 'r') as f:
            msg.debug("_get_date_format", f_path)
            line_count = 0
            for line in f:
                line_count += 1
                header_lines.append(line.strip())
                if line_count > MAX_HEADER_LINES:
                    break
        if header_lines:
            for i in eval_order:
                msg.debug("> attempt", date_formats[i])
                if date_formats[i]:
                    tmp_fmt = date_formats[i][0]
                    tmp_trim = date_formats[i][1]

                    tmp_now = dt.now().strftime(tmp_fmt)
                    if tmp_trim != 0:
                        tmp_now = tmp_now[:tmp_trim]

                    for line in header_lines:
                        dummy, exception, dummy = _parse_log_line(line, date_formats[i])
                        if exception == 0:
                            idx_date = i
                            date_info = date_formats[i]
                            break
                if idx_date > 0:
                    break

            msg.debug("> use", "idx_date={}, header_lines={}, date_info={}".format(idx_date, len(header_lines), date_info))
        else:
            empty = 1
            msg.debug("> emtpy", "idx_date={}, empty_file={}".format(idx_date, empty))

        return empty, idx_date

    def _parse_log_line(line, date_info):
        EX_OK = 0
        t_fmt = date_info[0]
        t_trim = date_info[1]
        try:
            # Attempt to parse the timestamp from the beginning of the line
            timestamp_str = line[:t_trim]
            timestamp = dt.strptime(timestamp_str, t_fmt)
            return EX_OK, 0, (timestamp, line)
        except ValueError:
            # If timestamp parsing fails, treat it as a non-timestamped line
            # and place it at the end of the sorted output (or handle as needed)
            return EX_OK, 1, (dt.max, line) # Puts non-timestamped lines last

    for log_file in log_files.keys():
        f_names = []
        all_lines = []
        subfolders = [ f.path for f in os.scandir(report_data['source_data']['dirpath_data_source']) if f.is_dir() ]
        for dirpath in subfolders:
            f_path = dirpath + "/" + log_file
            if os.path.exists(f_path):
                f_names.append(f_path)
        len_f_names = len(f_names)

        if len_f_names > 0:
            combined_notes = []
            f_combined_path = report_data['source_data']['dirpath_reports'] + "/combined." + log_file
            msg.normal(" Combining {} File(s)".format(len_f_names), f_combined_path)
            t_parse_exceptions = 0
            empty_files = 0
            unsorted_files = 0
            for f_path in f_names:
                empty, idx_date = _get_date_format(f_path, date_formats, log_files[log_file])
                combined_notes.append("{}: {}".format(date_formats[idx_date], f_path))
                if empty > 0:
                    msg.verbose(" Empty file", f_path)
                    combined_notes.append(" Empty file")
                    empty_files += 1
                    continue
                elif idx_date == 0:
                    msg.verbose(" Skipping", f_path)
                    combined_notes.append(" Skipped file, missing known date_formats")
                    unsorted_files += 1
                    continue
                
                # Read and parse lines from the each file in f_names
                _rc = EX_OK
                len_before = len(all_lines)
                with open(f_path, 'r') as f:
                    msg.debug("> parse", log_file)
                    for line in f:
                        line = line.strip()
                        _rc, exception, _line_parts = _parse_log_line(line, date_formats[idx_date])
                        t_parse_exceptions += exception
                        all_lines.append(_line_parts)
                len_after = len(all_lines)

                msg.debug(">", "len_before={}, len_after={}, _rc={}".format(len_before, len_after, _rc))
                if len_after > 0 and t_parse_exceptions == len_after:
                    break
                

            msg.debug(">", "all_lines={}, t_parse_exceptions={}, empty_files={}, unsorted_files={}, total files={}".format(len(all_lines), t_parse_exceptions, empty_files, unsorted_files, len_f_names))
            with open(f_combined_path, 'w') as outfile:
                for line in combined_notes:
                    outfile.write(line + '\n')
                outfile.write('\n\n')

            if empty_files == len_f_names:
                msg.min(" Warning", "All {} files were empty".format(log_file))
            elif empty_files > 0:
                msg.min(" Note", "{} of {} {} files were empty".format(empty_files, len_f_names, log_file))
            if unsorted_files == len_f_names:
                msg.min(" Skipping", "All {} files could not be sorted, unexpected time format".format(log_file))
            elif unsorted_files > 0:
                msg.min(" Note", "{} of {} {} files could not be sorted and were skipped, unexpected time format".format(unsorted_files, len_f_names, log_file))

            # Sort all log entries by their parsed timestamps
            if all_lines:
                all_lines.sort(key=lambda x: x[0])
                with open(f_combined_path, 'a') as outfile:
                    for timestamp, line in all_lines:
                        outfile.write(line + '\n')
        else:
            msg.debug("Warning", "No {} files found".format(log_file))


