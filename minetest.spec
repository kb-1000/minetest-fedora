Name:     minetest
Version:  5.0.0
Release:  1%{?dist}
Summary:  Multiplayer infinite-world block sandbox with survival mode

# See LICENSE.txt for more details
# * System irrlicht is used → no zlib
License:  LGPLv2+ and CC-BY-SA and ASL 2.0 and MIT
URL:      http://minetest.net/

Source0:  https://github.com/minetest/minetest/archive/%{version}/%{name}-%{version}.tar.gz
Source1:  %{name}.desktop
Source2:  %{name}@.service
Source3:  %{name}.rsyslog
Source4:  %{name}.logrotate
Source5:  %{name}.README
Source6:  https://github.com/minetest/minetest_game/archive/%{version}/%{name}_game-%{version}.tar.gz
Source8:  default.conf

# https://github.com/minetest/minetest/issues/4483
#Patch0001:      0001-use-pkg-config-to-find-luajit.patch

# LuaJIT arches
ExclusiveArch:  %{arm} %{ix86} x86_64 %{mips} aarch64

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  cmake >= 2.6.0
BuildRequires:  irrlicht-devel
BuildRequires:  bzip2-devel gettext-devel sqlite-devel
BuildRequires:  libpng-devel libjpeg-turbo-devel libXxf86vm mesa-libGL-devel
BuildRequires:  desktop-file-utils
BuildRequires:  systemd
BuildRequires:  openal-soft-devel
BuildRequires:  libvorbis-devel
BuildRequires:  jsoncpp-devel
BuildRequires:  libcurl-devel
BuildRequires:  luajit-devel
BuildRequires:  leveldb-devel
BuildRequires:  gmp-devel
BuildRequires:	libappstream-glib
BuildRequires:  freetype-devel

Requires:       %{name}-server = %{version}-%{release}
Requires:       hicolor-icon-theme

%description
Game of mining, crafting and building in the infinite world of cubic
blocks with optional hostile creatures, features both single and the
network multiplayer mode. There are no in-game sounds yet

%package server
Summary:  Minetest multiplayer server

Requires(pre):    shadow-utils
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd

%description server
Minetest multiplayer server. This package does not require X Window System

%prep
%autosetup -p1

pushd games
tar xf %{SOURCE6}
mv %{name}_game-%{version} %{name}_game
popd

# purge bundled jsoncpp and lua, and gmp :P
rm -vrf lib/jsoncpp lib/lua lib/gmp

find . -name .gitignore -print -delete
find . -name .travis.yml -print -delete
find . -name .luacheckrc -print -delete

%build
# -DENABLE_FREETYPE=ON needed for Unicode in text chat
%cmake -DENABLE_CURL=TRUE            \
       -DENABLE_LEVELDB=TRUE         \
       -DENABLE_LUAJIT=TRUE          \
       -DENABLE_GETTEXT=TRUE         \
       -DENABLE_SOUND=TRUE           \
       -DENABLE_SYSTEM_JSONCPP=TRUE  \
       -DENABLE_SYSTEM_GMP=TRUE      \
       -DENABLE_FREETYPE=TRUE        \
       -DBUILD_SERVER=TRUE           \
       -DCUSTOM_DOCDIR=%{_pkgdocdir} \
       .
%make_build

%install
%make_install

# Add desktop file
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

# Systemd unit file
mkdir -p %{buildroot}%{_unitdir}/
install -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}

# /etc/rsyslog.d/minetest.conf
mkdir -p %{buildroot}%{_sysconfdir}/rsyslog.d/
install -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/rsyslog.d/%{name}.conf

# /etc/logrotate.d/minetest
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d/
install -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}-server

# /var/lib/minetest directory for server data files
install -d -m 0775 %{buildroot}%{_sharedstatedir}/%{name}/
install -d -m 0775 %{buildroot}%{_sharedstatedir}/%{name}/default/

# /etc/minetest/default.conf
install -d -m 0775 %{buildroot}%{_sysconfdir}/%{name}/
install    -m 0664 minetest.conf.example %{buildroot}%{_sysconfdir}/%{name}/default.conf

# /etc/sysconfig/default.conf
install -d -m 0775 %{buildroot}%{_sysconfdir}/sysconfig/%{name}/
install    -m 0664 %{SOURCE8} %{buildroot}%{_sysconfdir}/sysconfig/%{name}

cp -p %{SOURCE5} README.fedora

# Move doc directory back to the sources
mkdir __doc
mv  %{buildroot}%{_datadir}/doc/%{name}/* __doc
rm -rf %{buildroot}%{_datadir}/doc/%{name}

%find_lang %{name}

#move appdata file to the proper location, and validate
mkdir -p %{buildroot}%{_datadir}/appdata
mv %{buildroot}%{_datadir}/metainfo/net.minetest.minetest.appdata.xml %{buildroot}%{_datadir}/appdata/%{name}.appdata.xml
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/appdata/%{name}.appdata.xml

%pre server
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
    -c "Minetest multiplayer server" %{name}
exit 0

%post server
%systemd_post %{name}@default.service

%preun server
%systemd_preun %{name}@default.service

%postun server
%systemd_postun_with_restart %{name}@default.service

%files -f %{name}.lang
%license LICENSE.txt
%doc README.fedora
%{_bindir}/%{name}
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%exclude %{_datadir}/applications/net.%{name}.%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/icons/hicolor/scalable/apps/%{name}.svg
%{_mandir}/man6/%{name}.*
%{_datadir}/appdata/%{name}.appdata.xml

%files server
%license LICENSE.txt
%{_pkgdocdir}
%doc README.fedora
%{_bindir}/%{name}server
%{_unitdir}/%{name}@.service
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-server
%config(noreplace) %{_sysconfdir}/rsyslog.d/%{name}.conf
%attr(-,minetest,minetest)%{_sharedstatedir}/%{name}/
%attr(-,minetest,minetest)%{_sysconfdir}/%{name}/
%attr(-,minetest,minetest)%{_sysconfdir}/sysconfig/%{name}/
%{_mandir}/man6/%{name}server.*

%changelog
* Fri Mar 08 2019 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 5.0.0-1
- Initial package
