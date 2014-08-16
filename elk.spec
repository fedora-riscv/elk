# missing on el6
%{?!_fmoddir: %global _fmoddir %{_libdir}/gfortran/modules}

%if 0%{?el7}
# Error: No Package found for openblas-devel on el7
ExcludeArch: ppc64
%endif
%if 0%{?el6}
# Error: No Package found for mpich2-devel on el6
ExcludeArch: ppc64
%endif

# Error: No Package found for openblas-devel
ExcludeArch: %arm

%if 0%{?el6}
%global mpich mpich2
%global mpich_load %_mpich2_load
%global mpich_unload %_mpich2_unload
%else
%global mpich mpich
%global mpich_load %_mpich_load
%global mpich_unload %_mpich_unload
%endif

%global BLASLAPACK -L%{_libdir} -lopenblas
%global FFTW -L%{_libdir} -lfftw3
%global LIBXC -L%{_libdir} -lxc

Name:			elk
Version:		2.3.22
Release:		8%{?dist}
Summary:		FP-LAPW Code

License:		GPLv3+
URL:			http://elk.sourceforge.net/
Source0:		https://downloads.sourceforge.net/project/%{name}/%{name}-%{version}.tgz


BuildRequires:		time

BuildRequires:		gcc-gfortran
BuildRequires:		openblas-devel
BuildRequires:		fftw3-devel
BuildRequires:		libxc-devel

Requires:		%{name}-species = %{version}-%{release}


%global desc_base \
An all-electron full-potential linearised augmented-plane wave (FP-LAPW) code\
with many advanced features. Written originally at\
Karl-Franzens-Universität Graz as a milestone of the EXCITING EU Research and\
Training Network, the code is designed to be as simple as possible so that new\
developments in the field of density functional theory (DFT) can be added\
quickly and reliably. 


%description
%{desc_base}


%package openmpi
Summary:		%{name} - openmpi version
BuildRequires:		openmpi-devel
Requires:		openmpi
Requires:		%{name}-species = %{version}-%{release}

%description openmpi
%{desc_base}

This package contains the openmpi version.


%package %{mpich}
Summary:		%{name} - %{mpich} version
BuildRequires:		%{mpich}-devel
Requires:		%{mpich}
Requires:		%{name}-species = %{version}-%{release}

%description %{mpich}
%{desc_base}

This package contains the %{mpich} version.


%package species
Summary:		%{name} - species files
Requires:		%{name}-common = %{version}-%{release}
BuildArch:		noarch

%description species
%{desc_base}

This package contains the species files.


%package common
Summary:		%{name} - common files

%description common
%{desc_base}

This package contains the common binaries.


%prep
%setup -q -n %{name}-%{version}
# create common make.inc.common
# default serial fortran
echo "SRC_MPI = mpi_stub.f90" > make.inc.common
echo "F90 = gfortran -fopenmp" >> make.inc.common
echo "F77 = gfortran -fopenmp" >> make.inc.common
echo "F90_OPTS = -I%{_fmoddir} %{optflags}" >> make.inc.common
echo "F77_OPTS = \$(F90_OPTS)" >> make.inc.common
echo "AR = ar" >> make.inc.common
echo "LIB_LPK = %BLASLAPACK" >> make.inc.common
# enable fftw/libxc dynamic linking
echo "LIB_FFT = %FFTW" >> make.inc.common
echo "SRC_FFT = zfftifc_fftw.f90" >> make.inc.common
echo "LIB_libxc = %LIBXC" >> make.inc.common
echo "SRC_libxc = libxcifc.f90" >> make.inc.common

# remove bundling of BLAS/LAPACK/FFTW/LIBXC/ERF
sed -i "s/blas lapack fft elk/elk/" src/Makefile
sed -i "s/erf.f90//" src/Makefile
sed -i "s/,erf//" src/stheta_mp.f90
# remove bundled sources
rm -rf src/LAPACK src/BLAS src/fftlib
rm -f src/libxc_funcs.f90 src/libxc.f90
rm -f src/erf.f90


%build
# Have to do off-root builds to be able to build many versions at once
mv src src.orig

# To avoid replicated code define a macro
%global dobuild() \
cp -p make.inc.common make.inc; \
%{__sed} -i "s|F90 =.*|F90 = mpif90 -fopenmp|" make.inc; \
%{__sed} -i "s|F77 =.*|F77 = mpif77 -fopenmp|" make.inc; \
echo "SRC_MPI =" >> make.inc;\
cat make.inc; \
cp -p make.inc make.inc$MPI_SUFFIX; \
%{__make}; \
mv src/%{name} %{name}$MPI_SUFFIX; \
%{__make} clean

# build serial/openmp version
export MPI_SUFFIX=_openmp
cp -rp src.orig src
cp -p make.inc.common make.inc; \
cat make.inc; \
cp -p make.inc make.inc$MPI_SUFFIX; \
%{__make}; \
mv src/%{name} .; \
mv src/eos/eos elk-eos; \
mv src/spacegroup/spacegroup elk-spacegroup; \
%{__make} clean; \
rm -rf src

# build openmpi version
cp -rp src.orig src
%{_openmpi_load}
%dobuild
%{_openmpi_unload}
rm -rf src

cp -rp src.orig src
# build mpich version
%{mpich_load}
%dobuild
%{mpich_unload}
# leave last src build for debuginfo


%install
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}

# To avoid replicated code define a macro
%global doinstall() \
mkdir -p $RPM_BUILD_ROOT/$MPI_BIN; \
install -p -m 755 %{name}$MPI_SUFFIX $RPM_BUILD_ROOT/$MPI_BIN

# install serial version
mkdir -p $RPM_BUILD_ROOT%{_bindir}
install -p -m 755 %{name} elk-eos elk-spacegroup $RPM_BUILD_ROOT%{_bindir}

# install openmpi version
%{_openmpi_load}
%doinstall
%{_openmpi_unload}

# install mpich version
%{mpich_load}
%doinstall
%{mpich_unload}

mkdir -p $RPM_BUILD_ROOT%{_datadir}/%{name}

# don't copy utilities - they trigger dependency on perl, python ...
cp -rp species $RPM_BUILD_ROOT%{_datadir}/%{name}
cp -rp make.inc* $RPM_BUILD_ROOT%{_datadir}/%{name}
cp -rp tests examples $RPM_BUILD_ROOT%{_datadir}/%{name}


%check

export NPROC=2 # test on 2 cores
export OMP_NUM_THREADS=$NPROC

# To avoid replicated code define a macro
%global docheck() \
cp -rp tests.orig tests; \
sed -i "s#../../src/elk#$ELK_EXECUTABLE#g" tests/tests.sh; \
time %{__make} test 2>&1 | tee tests.${NPROC}$MPI_SUFFIX.log; \
rm -rf tests

# check serial version
mv tests tests.orig.orig
cp -rp tests.orig.orig tests.orig
rm -rf tests.orig/test-018
ELK_EXECUTABLE="../../%{name}" MPI_SUFFIX=_openmp %docheck

# check openmpi version
%{_openmpi_load}
ELK_EXECUTABLE="mpiexec -np ${NPROC} ../../%{name}$MPI_SUFFIX" %docheck
%{_openmpi_unload}

# this will fail for mpich2 on el6 - mpd would need to be started ...
# check mpich version
%{mpich_load}
ELK_EXECUTABLE="mpiexec -np ${NPROC} ../../%{name}$MPI_SUFFIX" %docheck
%{mpich_unload}

# restore tests
mv tests.orig tests


%files
%{_bindir}/%{name}


%files common
%doc COPYING README
%{_bindir}/elk-eos
%{_bindir}/elk-spacegroup
%{_datadir}/%{name}
%exclude %{_datadir}/%{name}/species


%files species
%{_datadir}/%{name}/species


%files openmpi
%{_libdir}/openmpi%{?_opt_cc_suffix}/bin/%{name}_openmpi


%files %{mpich}
%{_libdir}/%{mpich}%{?_opt_cc_suffix}/bin/%{name}_%{mpich}


%changelog
* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.22-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Marcin Dulak <Marcin.Dulak@gmail.com> - 2.3.22-7
- upstream update
- fix mpi build
- tests/test-018 hangs - disabled

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.3.16-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Apr 22 2014 Marcin Dulak <Marcin.Dulak@gmail.com> - 2.3.16-5
- upstream update

* Tue Mar 18 2014 Björn Esser <bjoern.esser@gmail.com> - 2.2.10-4
- rebuilt for mpich-3.1

* Tue Feb 18 2014 Marcin Dulak <Marcin.Dulak@gmail.com> 2.2.10-3
- removed bundling of BLAS, LAPACK, FFTW, LIBXC, ERF
- test on 2 cores to reduce randomness in koji multicore builds

* Fri Feb 7 2014 Marcin Dulak <Marcin.Dulak@gmail.com> 2.2.10-2
- update for Fedora/EPEL

* Fri Jun 12 2009 Marcin Dulak <Marcin.Dulak@gmail.com> 0.9.262-1
- initial build

