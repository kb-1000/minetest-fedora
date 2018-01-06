Name:     minetest
Version:  0.4.16
Release:  8%{?dist}
Summary:  Multiplayer infinite-world block sandbox with survival mode

License:  LGPLv2+ and CC-BY-SA
URL:      http://minetest.net/

Source0:  https://github.com/minetest/minetest/archive/%{version}/%{name}-%{version}.tar.gz
Source1:  %{name}.desktop
Source2:  %{name}@.service
Source3:  %{name}.rsyslog
Source4:  %{name}.logrotate
Source5:  %{name}.README
Source6:  https://github.com/minetest/minetest_game/archive/%{version}/%{name}_game-%{version}.tar.gz
Source7:  http://www.gnu.org/licenses/lgpl-2.1.txt
Source8:  default.conf

# https://github.com/minetest/minetest/issues/4483
Patch0001:      0001-use-pkg-config-to-find-luajit.patch

%if 0%{?rhel}
ExclusiveArch:  %{ix86} x86_64
%else
# LuaJIT arches
ExclusiveArch:  %{arm} %{ix86} x86_64 %{mips} aarch64
%endif

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

cp %{SOURCE7} doc/

# purge bundled jsoncpp and lua, and gmp :P
rm -vrf lib/jsoncpp lib/lua lib/gmp

find . -name .gitignore -print -delete
find . -name .travis.yml -print -delete
find . -name .luacheckrc -print -delete

%build
# -DENABLE_FREETYPE=ON needed for Unicode in text chat
%cmake -DENABLE_CURL=TRUE           \
       -DENABLE_LEVELDB=TRUE        \
       -DENABLE_LUAJIT=TRUE         \
       -DENABLE_GETTEXT=TRUE        \
       -DENABLE_SOUND=TRUE          \
       -DENABLE_SYSTEM_JSONCPP=TRUE \
       -DENABLE_SYSTEM_GMP=TRUE     \
       -DENABLE_FREETYPE=TRUE       \
       -DBUILD_SERVER=TRUE          \
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
%license doc/lgpl-2.1.txt
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
%license doc/lgpl-2.1.txt
%doc README.txt doc/world_format.txt doc/protocol.txt README.fedora
%{_bindir}/%{name}server
%{_unitdir}/%{name}@.service
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}-server
%config(noreplace) %{_sysconfdir}/rsyslog.d/%{name}.conf
%attr(-,minetest,minetest)%{_sharedstatedir}/%{name}/
%attr(-,minetest,minetest)%{_sysconfdir}/%{name}/
%attr(-,minetest,minetest)%{_sysconfdir}/sysconfig/%{name}/
%{_mandir}/man6/%{name}server.*

%changelog
* Sat Jan 06 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.4.16-8
- Remove obsolete scriptlets

* Tue Dec 26 2017 Björn Esser <besser82@fedoraproject.org> - 0.4.16-7
- Rebuilt for jsoncpp.so.20

* Fri Sep 01 2017 Björn Esser <besser82@fedoraproject.org> - 0.4.16-6
- Rebuilt for jsoncpp-1.8.3

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.16-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.16-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jul 17 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.4.16-3
- Use %%find_lang

* Mon Jul 17 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.4.16-2
- Re-enable freetype
- Properly unbundle 3rd-party libs

* Tue Jun 06 2017 Gwyn Ciesla <limburgher@gmail.com> - 0.4.16-1
- 0.4.16.
- Fixes font licensing issue.
- Appdata fixes.

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.15-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Dec 27 2016 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.15-1
- Update to 0.4.15

* Thu Oct 06 2016 Björn Esser <fedora@besser82.io> - 0.4.14-4
- Rebuilt for libjsoncpp.so.11

* Mon Aug 29 2016 Igor Gnatenko <ignatenko@redhat.com> - 0.4.14-3
- Rebuild for LuaJIT 2.1.0

* Sun Aug 07 2016 Igor Gnatenko <ignatenko@redhat.com> - 0.4.14-2
- Rebuild for LevelDB 1.18

* Tue Jun 21 2016 Igor Gnatenko <ignatenko@redhat.com> - 0.4.14-1
- Update to 0.4.14 (RHBZ #1336243)
  Kudos to Ben Rosser <rosser.bjr@gmail.com>

* Tue Mar 29 2016 Björn Esser <fedora@besser82.io> - 0.4.13-5
- Rebuilt for libjsoncpp.so.1

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.4.13-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Aug 24 2015 Oliver Haessler <oliver@redhat.com> - 0.4.13-3
- disabled freetyp to prevent the need for libcguittfont.so()(64bit)

* Mon Aug 24 2015 Oliver Haessler <oliver@redhat.com> - 0.4.13-2
- removed Patch1 as it is no longer needed
- enabled build of minetestserver

* Mon Aug 24 2015 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.4.13-1
- Update to 0.4.13

* Fri Aug 07 2015 Oliver Haessler <oliver@redhat.com> - 0.4.12-5
- only build x86_64 on EPEL as minetest needs luajit and this has no ppc64 support

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.12-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Thu May 14 2015 Ville Skyttä <ville.skytta@iki.fi> - 0.4.12-3
- Don't ship .gitignore

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 0.4.12-2
- Rebuilt for GCC 5 C++11 ABI change

* Sat Mar 14 2015 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.4.12-1
- Update to 0.4.12 (Changelog: http://dev.minetest.net/Changelog#0.4.11_.E2.86.92_0.4.12)

* Fri Dec 26 2014 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 0.4.11-1
- Update to 0.4.11 (Changelog: http://dev.minetest.net/Changelog#0.4.10_.E2.86.92_0.4.11)

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.10-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Mon Jul 07 2014 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.10-1
- 0.4.10 upstream release (Changelog: http://dev.minetest.net/Changelog#0.4.9_.E2.86.92_0.4.10) (RHBZ #1116862)

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.9-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sun May 25 2014 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.9-2
- rebuild against new irrlicht (RHBZ #1098784)

* Sun Jan 12 2014 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.9-1
- Update to 0.4.9 (Changelog: http://dev.minetest.net/Changelog#0.4.8_.E2.86.92_0.4.9)

* Mon Nov 25 2013 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.8-2
- add support of multiple server cfgs
- allow acces for group to server parts
- Shared irrlicht (patch from gentoo)

* Sun Nov 24 2013 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.8-1
- Update to 0.4.8 (Changelog: http://dev.minetest.net/Changelog#0.4.7_.E2.86.92_0.4.8)

* Fri Oct 11 2013 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.7-1
- Update to 0.4.7 w/ bundled jthread
- Bundle jthread correctly (kalev)

* Thu Sep  5 2013 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.4.4-1
- Update to 0.4.4
- Fix systemd scripts (rhbz 850208)
- fixed hardcoded paths
- Spaces instead of tabs
- Fixed URL, sources
- buildroot macro instead of rpm_build_dir

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

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

* Sun Nov 13 2011 Aleksandra Bookwar <alpha@bookwar.info> - 0.3.1-3.gitbc0e5c0
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
