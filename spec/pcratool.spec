#
# spec file for package pcratool
#
# Copyright (c) 2025 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#


%define tool_common pcratool
%define tool_config %{tool_common}
%define mod_base /usr/lib/%{tool_common}

Name:           pcratool
Version:        0.0.5
Release:        0
Summary:        Supportconfig Analysis Server Report
License:        GPL-3.0
URL:            https://github.com/g23guy/pcratool
Group:          System/Monitoring
Source:         %{name}-%{version}.tar.gz
Requires:       python3-base
Requires:       python3-urllib3,python3-requests,python3-beautifulsoup4
BuildRequires:  python3-urllib3,python3-requests,python3-beautifulsoup4
BuildArch:      noarch

%description
A tool that primarily analyzes an HB report file.

%prep
%setup -q

%build
gzip -9f man/*5
gzip -9f man/*8

%install
pwd;ls -la
install -d %{buildroot}%{_sysconfdir}/%{tool_config}
install -d %{buildroot}%{_mandir}/man5
install -d %{buildroot}%{_mandir}/man8
install -d %{buildroot}%{mod_base}
mkdir -p %{buildroot}%{_bindir}
install -m 755 bin/pcratool %{buildroot}%{_bindir}
install -m 644 modules/* %{buildroot}%{mod_base}
install -m 644 config/pcratool.conf %{buildroot}%{_sysconfdir}/%{tool_config}
install -m 644 man/*.5.gz %{buildroot}%{_mandir}/man5
install -m 644 man/*.8.gz %{buildroot}%{_mandir}/man8

%files
%defattr(-,root,root)
%{_bindir}/pcratool
%{mod_base}
%{mod_base}/*
%dir %{_sysconfdir}/%{tool_config}
%config %{_sysconfdir}/%{tool_config}/*
%doc %{_mandir}/man5/*
%doc %{_mandir}/man8/*

%changelog
