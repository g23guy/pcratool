# pcratool
## Pacemaker Cluster Report Analysis Tool

This project will require significant parsing and analysis of various log files and configuration files to provide a holistic view of the cluster's health and state.
Here is a breakdown of the milestones you've set, along with some key considerations for each phase.

# Application Requirements Completion
This is the foundation of your project. Before you start coding, you need to clearly define what the application should do.
Define the scope: What specific problems will this tool solve for a cluster administrator? Will it provide a single, easy-to-read summary, or will it allow for detailed, interactive drilling down into specific events?

# Identify key analysis points: 
Based on the files you've listed, the tool should be able to identify:
Resource status: Which resources are running, stopped, or failed? Where are they located?
Cluster membership: Which nodes are online, offline, or partitioned?
SBD status: Is SBD synchronized? Are there split-brain issues?
Quorum status: Does the cluster have quorum? What's the state of SBD fencing?
Event correlation: Link an event in events.txt to a specific log entry in ha-log.txt or pacemaker.log?
Determine output format: How will the results be presented? 
Creates JSON files for analysis
Writes output in markdown to be compiled into docx, html, and pdf with SUSE branding.
Objectives:
Identify the cluster
Nodes
OS
Cluster versions
Configuration
Cluster
Resource agents
STONITH
Analysis




# Alpha Release with Module Utility Draft (by Sept 1)
This phase is about creating the core engine that can parse the data. The goal is to have a functional, albeit rough, version of the analysis logic.

Pseudocode for Initial Port from SCA Tool

Entry point
if __name__ == "__main__":
    Handle signal input
    configure a config file parser
    configure message handling
    main(sys.argv)
    
Main
    set variables
    get config file settings
    process startup options
    validate variables and settings to be processed
    validate hb_report data
    create analysis results directory
    gather analysis tool data
    gather cluster data
    write JSON data to analysis results directory


Parsing scripts: Completed parsing and analysis of report files 
Parse and analyze the following files from a Pacemaker cluster report:
journal.log
ha-log.txt
ha-log.txt.info
members.txt
description.txt

// nodes.peplap05997.kernel
 {
   "date": "Thu Mar 14 15:34:56 CST 2024",
   "by": "report -f 2024/03/02 10:00 -t 2024/03/02 11:59 /tmp/hb_report-20240314-1533",
   "nodes": {
       "peplap05997": {
           "pacemaker": "pacemaker 2.1.2+20211124.ada5c3b36-150400.4.17.1",
           "corosync": "corosync 2.4.6-150300.12.10.1",
           "platform": "Linux",
           "kernel": "5.14.21-150400.24.108-default",
           "architecture": "x86_64",
           "os_version": "SUSE Linux Enterprise Server 15 SP4"
       },
       "peplap05998": {
           "pacemaker": "pacemaker 2.1.2+20211124.ada5c3b36-150400.4.14.9",
           "corosync": "corosync 2.4.6-150300.12.10.1",
           "platform": "Linux",
           "kernel": "5.14.21-150400.24.97-default",
           "architecture": "x86_64",
           "os_version": "SUSE Linux Enterprise Server 15 SP4"
       }
   }
}
// SCA Fragment
"sc_info": {
       "valid": true,
       "serverName": "skylark",
       "hardWare": "OptiPlex 7000",
       "virtualization": "KVM",
       "Summary": "openSUSE Leap 15.6",
       "timeArchiveRun": "2025-02-12 15:28:39",
       "report": {
           "json": "/var/log/scc_skylark_250212_1528_report.json"
       },
       "timeAnalysis": "2025-08-11 11:47:31",
       "supportconfigVersion": "3.2.8-1",
       "kernelVersion": "6.4.0-150600.23.33-default",
       "osArch": "x86_64",
       "vmIdentity": "Virtual Machine Server - Dom0",
       "name": "scc_skylark_250212_1528",
       "path": "/var/log"
   },




crm_mon.txt
corosync.conf
sysinfo.txt
events.txt
Analysis.txt
Parse and analyze the following node files for each node in the cluster report:
./<node>/journal.log
./<node>/ha-log.txt
./<node>/ha-log.txt.info
./<node>/drbd.conf
./<node>/drbd.d/global_common.conf
./<node>/dlm_dump.txt
./<node>/ocfs2.txt
./<node>/permissions.txt
./<node>/cib.xml
./<node>/sbd
./<node>/sbd.txt
./<node>/RUNNING
./<node>/crm_verify.txt
./<node>/sysstats.txt
./<node>/time.txt
./<node>/messages
./<node>/pacemaker.log
./<node>/pacemaker.log.info
./<node>/profiles.yml
./<node>/profiles.yml.info
./<node>/crm.conf
./<node>/crm.conf.info
./<node>/events.txt
Data structures: Create a data model that can hold the parsed information in a structured way. This will be crucial for the analysis phase. For example, a Node object might contain properties for its status, resources, sbd_state, etc.
Initial analysis logic: Implement basic checks and a simple report generation. For example, a function that reads crm_mon.txt and reports if any resources are not started.

# Web Interface (by Sept 15)
This milestone focuses on presenting the data in a more user-friendly way. The web interface will consume the data from your analysis engine and display it visually.
Choose a framework: Select a web framework (e.g., Flask) that will handle the front-end and back-end logic.
Design the UI: Plan a layout that is intuitive for a cluster administrator. A dashboard view with high-level summaries and a drill-down option for detailed logs and resource information would be effective.
API integration: Should the web interface need an API to communicate with the analysis engine. The analysis tool will act as the data source, and the web interface will be the consumer.

# Containerized (by Sept 30)
Making the application containerized (e.g., using podman) will greatly simplify deployment and portability.
Create a Dockerfile: Define a Dockerfile that specifies the necessary dependencies and instructions to build your application image.
Isolate dependencies: Ensure all required libraries and tools are included in the container image, so the application can run in any environment without external dependencies.
Create a startup script: Write a script that can be executed when the container starts. This script should launch your analysis engine and the web server.

# Beta Release with Container (by Oct 1)
This is the first end-to-end version of your application. The container should contain both the analysis engine and the web interface, ready for testing.
User testing: Gather feedback from a small group of users. This is critical for identifying bugs, usability issues, and missing features.
Bug fixes: Address any issues reported during the beta testing phase.
Documentation: Start writing user documentation, including how to set up and run the container, and how to interpret the results.

# Release Candidate (by Oct 15)
The final step before the official launch. The application should be stable, well-documented, and ready for production use.
Final polish: Refine the user interface, improve the wording in the analysis reports, and ensure the code is clean and well-commented.
Performance testing: Verify that the application can handle large cluster report files without significant performance degradation.
Final documentation: Complete all user guides, API references, and developer documentation.

