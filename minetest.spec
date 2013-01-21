%define _hardened_build 1
%global gitcommit 9696ed3
%global gitname celeron55
%global gitgamecommit 87a1e37

Name:		minetest
Version:	0.4.3
Release:	2%{?dist}
Summary:	Multiplayer infinite-world block sandbox with survival mode

Group:		Amusements/Games
License:	LGPLv2+ and CC-BY-SA
URL:		http://celeron.55.lt/minetest/		

# curl -L -O http://github.com/celeron55/minetest/tarball/0.4.3/minetest-0.4.3.tar.gz
# wget https://raw.github.com/RussianFedora/minetest/fedora/minetest.desktop
# wget https://raw.github.com/RussianFedora/minetest/fedora/minetest.service
# wget https://raw.github.com/RussianFedora/minetest/fedora/minetest.rsyslog
# wget https://raw.github.com/RussianFedora/minetest/fedora/minetest.logrotate
# wget https://raw.github.com/RussianFedora/minetest/fedora/minetest.README

Source0:	http://github.com/%{gitname}/%{name}/tarball/%{version}/%{name}-%{version}.tar.gz
Source1:	%{name}.desktop
Source2:	%{name}.service
Source3:	%{name}.rsyslog
Source4:	%{name}.logrotate
Source5:	%{name}.README
Source6:	http://github.com/%{gitname}/%{name}_game/tarball/%{version}/%{name}_game-%{version}.tar.gz
Source7:	http://www.gnu.org/licenses/lgpl-2.1.txt

# Fix to build with gcc-4.7.0
Patch1:		%{name}-0.4.3-gcc.patch

BuildRequires:	cmake >= 2.6.0
BuildRequires:	irrlicht-devel
BuildRequires:	bzip2-devel gettext-devel jthread-devel sqlite-devel
BuildRequires:	libpng-devel libjpeg-turbo-devel libXxf86vm mesa-libGL-devel
BuildRequires:	desktop-file-utils
BuildRequires:	systemd-units
BuildRequires:	openal-soft-devel
BuildRequires:	libvorbis-devel

Requires:	%{name}-server = %{version}-%{release}
Requires:	hicolor-icon-theme

%description 
Game of mining, crafting and building in the infinite world of cubic
blocks with optional hostile creatures, features both single and the
network multiplayer mode. There are no in-game sounds yet

%package	server
Summary:	Minetest multiplayer server
Group:		Amusements/Games

Requires(pre):		shadow-utils
Requires(post):		systemd-units
Requires(preun):	systemd-units
Requires(postun):	systemd-units


%description	server
Minetest multiplayer server. This package does not require X Window System

%prep
%setup -q -n %{gitname}-%{name}-%{gitcommit}
%patch1 -p1

pushd games
tar xf %{SOURCE6}
mv %{gitname}-%{name}_game-%{gitgamecommit} %{name}_game
popd

cp %{SOURCE7} doc/

%build
%cmake -DJTHREAD_INCLUDE_DIR=%{_includedir}/jthread .
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT

# Add desktop file
desktop-file-install --dir=${RPM_BUILD_ROOT}%{_datadir}/applications %{SOURCE1}

# Systemd unit file
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
cp -p %{SOURCE2} $RPM_BUILD_ROOT%{_unitdir}

# /etc/rsyslog.d/minetest.conf
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p %{SOURCE3} $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/%{name}.conf

# /etc/logrotate.d/minetest
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d
cp -p %{SOURCE4} $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d/%{name}-server

# /var/lib/minetest directory for server data files
mkdir -p $RPM_BUILD_ROOT%{_sharedstatedir}/%{name} 

# /etc/minetest.conf
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
cp -p minetest.conf.example $RPM_BUILD_ROOT%{_sysconfdir}/%{name}.conf

cp -p %{SOURCE5} README.fedora

# Move doc directory back to the sources
mkdir __doc
mv  $RPM_BUILD_ROOT%{_datadir}/doc/%{name}/* __doc
rm -rf $RPM_BUILD_ROOT%{_datadir}/doc/%{name}

# %find_lang %{name}

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%pre server
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d /var/lib/%{name} -s /sbin/nologin \
    -c "Minetest multiplayer server" %{name}
exit 0

%post server
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun server
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}.service > /dev/null 2>&1 || :
fi

%postun server
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

# %%files -f %{name}.lang
%files
%doc doc/lgpl-2.1.txt README.fedora
%{_bindir}/%{name}
%{_datadir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/scalable/apps/%{name}-icon.svg
%{_mandir}/man6/minetest.*

%files server
%doc README.txt doc/lgpl-2.1.txt doc/mapformat.txt doc/protocol.txt README.fedora
%{_bindir}/%{name}server
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-server
%config(noreplace) %{_sysconfdir}/rsyslog.d/%{name}.conf
%attr(0755,minetest,minetest) %dir %{_sharedstatedir}/%{name}
%{_mandir}/man6/minetestserver.*


%changelog
* Mon Jan 21 2013 Adam Tkac <atkac redhat com> - 0.4.3-2
- rebuild due to "jpeg8-ABI" feature drop

* Tue Nov 13 2012 Tom Callaway <spot@fedoraproject.org> - 0.4.3-1
- update to 0.4.3

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.1-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Fri Apr 13 2012 Jon Ciesla <limburgher@gmail.com> - 0.3.1-10
- Added hardened build.

* Tue Feb 28 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.1-9
- Rebuilt for c++ ABI breakage

* Sat Jan 14 2012 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-8
- Fixed to build with gcc-4.7.0

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.1-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Dec  8 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-6
- Fixed docs for minetest package

* Mon Dec  5 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-5
- Changed tarball and logrotate names, removed git commit, new README file.

* Mon Nov 14 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-4.gitbc0e5c0
- Removed clean section and defattr according to guidelines

* Sat Nov 13 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-3.gitbc0e5c0
- Systemd unit file, rsyslog, user/group and other server-related fixes
- Fixed Release tag for Fedora review

* Sat Nov 12 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-2.gitbc0e5c0.R
- Fixed doc directories
- Split package into main and -server parts

* Wed Nov  9 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-1.gitbc0e5c0.R
- Update to stable 0.3.1 version

* Thu Nov  3 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.0-1.gitf65d157.R
- Update to stable 0.3.0 version

* Fri Sep 30 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.2.20110922_2-2.git960009d
- Desktop file and icon

* Fri Sep 30 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.2.20110922_2-1.git960009d
- Basic build of the current stable version
