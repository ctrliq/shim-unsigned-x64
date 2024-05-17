%global pesign_vre 0.106-1
%global gnuefi_vre 1:3.0.5-6
%global openssl_vre 1.0.2j

%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/rocky/'))
%global shimrootdir %{_datadir}/shim/
%global shimversiondir %{shimrootdir}/%{version}-%{release}
%global efiarch x64
%global shimdir %{shimversiondir}/%{efiarch}
%global efialtarch ia32
%global shimaltdir %{shimversiondir}/%{efialtarch}

%global debug_package %{nil}
%global __debug_package 1
%global _binaries_in_noarch_packages_terminate_build 0
%global __debug_install_post %{SOURCE100} %{efiarch} %{efialtarch}
%undefine _debuginfo_subpackages

# currently here's what's in our dbx: nothing
%global dbxfile %{nil}

Name:                 shim-unsigned-%{efiarch}
Version:              15.8
Release:              0%{?dist}
Summary:              First-stage UEFI bootloader
ExclusiveArch:        x86_64
License:              BSD
URL:                  https://github.com/rhboot/shim
Source0:              https://github.com/rhboot/shim/releases/download/%{version}/shim-%{version}.tar.bz2
%if 0%{?dbxfile}
Source2:	%{dbxfile}
%endif
Source4:              shim.patches

Source100:            shim-find-debuginfo.sh
Source90000:          sbat.ciq.csv
Source90001:          ciq_sb_ca.der

%include %{SOURCE4}

BuildRequires:        gcc make
BuildRequires:        elfutils-libelf-devel
BuildRequires:        git openssl-devel openssl
BuildRequires:        pesign >= %{pesign_vre}
BuildRequires:        dos2unix findutils

# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires:	OpenSSL
Provides:             bundled(openssl) = %{openssl_vre}

%global desc \
Initial UEFI bootloader that handles chaining to a trusted full \
bootloader under secure boot environments.
%global debug_desc \
This package provides debug information for package %{expand:%%{name}} \
Debug information is useful when developing applications that \
use this package or when debugging this package.

%description
%desc

%package -n shim-unsigned-%{efialtarch}
Summary:	First-stage UEFI bootloader (unsigned data)
Provides:	bundled(openssl) = %{openssl_vre}

%description -n shim-unsigned-%{efialtarch}
%desc

%package debuginfo
Summary:	Debug information for shim-unsigned-%{efiarch}
Group:		Development/Debug
AutoReqProv:	0
BuildArch:	noarch

%description debuginfo
%debug_desc

%package -n shim-unsigned-%{efialtarch}-debuginfo
Summary:	Debug information for shim-unsigned-%{efialtarch}
Group:		Development/Debug
AutoReqProv:	0
BuildArch:	noarch

%description -n shim-unsigned-%{efialtarch}-debuginfo
%debug_desc

%package debugsource
Summary:	Debug Source for shim-unsigned
Group:		Development/Debug
AutoReqProv:	0
BuildArch:	noarch

%description debugsource
%debug_desc

%prep
%autosetup -S git_am -n shim-%{version}
git config --unset user.email
git config --unset user.name
mkdir build-%{efiarch}
mkdir build-%{efialtarch}
cp %{SOURCE90000} data/


%build
COMMITID=$(cat commit)
MAKEFLAGS="TOPDIR=.. -f ../Makefile COMMITID=${COMMITID} "
MAKEFLAGS+="EFIDIR=%{efidir} PKGNAME=shim RELEASE=%{release} "
MAKEFLAGS+="ENABLE_SHIM_HASH=true "
MAKEFLAGS+="%{_smp_mflags}"
if [ -s "%{SOURCE90001}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_CERT_FILE=%{SOURCE90001}"
fi
%if 0%{?dbxfile}
if [ -f "%{SOURCE2}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_DBX_FILE=%{SOURCE2}"
fi
%endif

cd build-%{efiarch}
make ${MAKEFLAGS} \
	DEFAULT_LOADER='\\\\grub%{efiarch}.efi' \
	all
cd ..

%install
COMMITID=$(cat commit)
MAKEFLAGS="TOPDIR=.. -f ../Makefile COMMITID=${COMMITID} "
MAKEFLAGS+="EFIDIR=%{efidir} PKGNAME=shim RELEASE=%{release} "
MAKEFLAGS+="ENABLE_HTTPBOOT=true ENABLE_SHIM_HASH=true "
if [ -s "%{SOURCE90001}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_CERT_FILE=%{SOURCE90001}"
fi
%if 0%{?dbxfile}
if [ -f "%{SOURCE2}" ]; then
	MAKEFLAGS="$MAKEFLAGS VENDOR_DBX_FILE=%{SOURCE2}"
fi
%endif

cd build-%{efiarch}
make ${MAKEFLAGS} \
	DEFAULT_LOADER='\\\\grub%{efiarch}.efi' \
	DESTDIR=${RPM_BUILD_ROOT} \
	install-as-data install-debuginfo install-debugsource
cd ..

%files
%license COPYRIGHT
%dir %{shimrootdir}
%dir %{shimversiondir}
%dir %{shimdir}
%{shimdir}/*.efi
%{shimdir}/*.hash
%{shimdir}/*.CSV

%files debuginfo -f build-%{efiarch}/debugfiles.list

%files debugsource -f build-%{efiarch}/debugsource.list

%changelog
* Tue Jan 23 2024 Jason Rodriguez <jrodriguez@ciq.com> - 15.8-0
- Upgrading to Shim 15.8 For CIQ

* Mon Nov 20 2023 Jason Rodriguez <jrodriguez@ciq.com> - 15.7-4
- Removing NX-enabling patch due to NX not being compatible with grub2 and kernel at this time

* Sun Oct 22 2023 Jason Rodriguez <jrodriguez@ciq.com> - 15.7-3
- Enable fix for buggy binutils

* Tue Aug 22 2023 Skip Grube <sgrube@ciq.com> - 15.7-2
- Added real CA from CIQ IT, fixed SBAT

* Fri Mar 24 2023 Skip Grube <sgrube@ciq.co> - 15.7-1
- Added NX-enabling patch from upstream

* Tue Mar 21 2023 Skip Grube <sgrube@ciq.co> - 15.7-0
- Upgrading to Shim 15.7 for CIQ

* Thu Dec 01 2022 Skip Grube <sgrube@ciq.co> - 15.6-1
- Debranded and CA swapped for CIQ from upstream Rocky Linux

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- shim 15.6

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- Remove main branch

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- Adding more patches based on review board feedback https://github.com/rhboot/shim-review/issues/194#issuecomment-894187000 and cherry-pick patches for shim-reivew git 15.4..4583db41ea58195956d4cdf97c43a195939f906b

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- cherry-pick patches for shim-reivew git 15.4..4d64389c6c941d21548b06423b8131c872e3c3c7 and bump version to .1.2

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- cherry-pick patches for shim-reivew git format-patch 15.4..9f973e4e95b1136b8c98051dbbdb1773072cc998

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- Adding prod certs

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- Updating Rocky test CA

* Tue Aug 16 2022 Sherif Nagy <sherif@rockylinux.org> - 15.6-1
- Adding Rocky testing CA

* Tue Aug 16 2022 Louis Abel <label@rockylinux.org> - 15.6-1
- Debranding work for shim-unsigned

* Wed Jun 01 2022 Peter Jones <pjones@redhat.com> - 15.6-1.el8
- Update to shim-15.6
  Resolves: CVE-2022-28737

* Thu Sep 17 2020 Peter Jones <pjones@redhat.com> - 15-9.el8
- Fix an incorrect allocation size.
  Related: rhbz#1877253

* Thu Jul 30 2020 Peter Jones <pjones@redhat.com> - 15-8
- Fix a load-address-dependent forever loop.
  Resolves: rhbz#1861977
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311
  Related: CVE-2020-15705
  Related: CVE-2020-15706
  Related: CVE-2020-15707

* Sat Jul 25 2020 Peter Jones <pjones@redhat.com> - 15-7
- Implement Lenny's workaround
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311

* Fri Jul 24 2020 Peter Jones <pjones@redhat.com> - 15-5
- Once more with the MokListRT config table patch added.
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311

* Thu Jul 23 2020 Peter Jones <pjones@redhat.com> - 15-4
- Rebuild for bug fixes and new signing keys
  Related: CVE-2020-10713
  Related: CVE-2020-14308
  Related: CVE-2020-14309
  Related: CVE-2020-14310
  Related: CVE-2020-14311

* Wed Jun 05 2019 Javier Martinez Canillas <javierm@redhat.com> - 15-3
- Make EFI variable copying fatal only on secureboot enabled systems
  Resolves: rhbz#1715878
- Fix booting shim from an EFI shell using a relative path
  Resolves: rhbz#1717064

* Tue Feb 12 2019 Peter Jones <pjones@redhat.com> - 15-2
- Fix MoK mirroring issue which breaks kdump without intervention
  Related: rhbz#1668966

* Fri Jul 20 2018 Peter Jones <pjones@redhat.com> - 15-1
- Update to shim 15

* Tue Sep 19 2017 Peter Jones <pjones@redhat.com> - 13-3
- Actually update to the *real* 13 final.
  Related: rhbz#1489604

* Thu Aug 31 2017 Peter Jones <pjones@redhat.com> - 13-2
- Actually update to 13 final.

* Fri Aug 18 2017 Peter Jones <pjones@redhat.com> - 13-1
- Make a new shim-unsigned-x64 package like the shim-unsigned-aarch64 one.
- This will (eventually) supersede what's in the "shim" package so we can
  make "shim" hold the signed one, which will confuse fewer people.
