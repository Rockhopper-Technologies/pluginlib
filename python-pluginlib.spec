%global pypi_name pluginlib
%global sum  A framework for creating and importing plugins in Python
%global desc Pluginlib is a Python framework for creating and importing plugins.\
Pluginlib makes creating plugins for your project simple.

%global with_python3 1
%global with_python2 0

# Drop Python 2 with Fedora 30 and EL8
%if 0%{?fedora} < 30 || 0%{?rhel} < 8
  %global with_python2 1
%endif


Name:           python-%{pypi_name}
Version:        0.5.0
Release:        1%{?dist}
Summary:        %{sum}

License:        MPLv2.0
URL:            https://github.com/Rockhopper-Technologies/pluginlib
Source0:        https://files.pythonhosted.org/packages/source/p/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

%if 0%{?with_python2}
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
BuildRequires:  python2-mock
%endif

%if 0%{?with_python3}
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
%endif

%if 0%{?with_python3_other}
BuildRequires:  python%{python3_other_pkgversion}-devel
BuildRequires:  python%{python3_other_pkgversion}-setuptools
%endif

# Additional build requirements for Python 2.6
%if 0%{?el6}
BuildRequires:  python-unittest2
BuildRequires:  python-importlib
%endif

%description
%{desc}


# Python 2 package
%if 0%{?with_python2}
%package -n     python2-%{pypi_name}

Summary:        %{sum}
%{?python_provide:%python_provide python2-%{pypi_name}}
Requires:       python2-setuptools

%if 0%{?el6}
Requires:  python-importlib
%endif

%description -n python2-%{pypi_name}
%{desc}
%endif

# Python 3 package
%if 0%{?with_python3}
%package -n     python%{python3_pkgversion}-%{pypi_name}
Summary:        %{sum}
%{?python_provide:%python_provide python%{python3_pkgversion}-%{pypi_name}}
Requires:       python%{python3_pkgversion}-setuptools

%description -n python%{python3_pkgversion}-%{pypi_name}
%{desc}
%endif

# Python 3 other package
%if 0%{?with_python3_other}
%package -n     python%{python3_other_pkgversion}-%{pypi_name}
Summary:        %{sum}
%{?python_provide:%python_provide python%{python3_other_pkgversion}-%{pypi_name}}
Requires:       python%{python3_other_pkgversion}-setuptools

%description -n python%{python3_other_pkgversion}-%{pypi_name}
%{desc}
%endif


%prep
%autosetup -p0 -n %{pypi_name}-%{version}

# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info


%build
%if 0%{?with_python2}
%py2_build
%endif

%if 0%{?with_python3}
%py3_build
%endif

%if 0%{?with_python3_other}
%py3_other_build
%endif


%install
%if 0%{?with_python3_other}
%py3_other_install
%endif

%if 0%{?with_python3}
%py3_install
%endif

%if 0%{?with_python2}
%py2_install
%endif


%check
%if 0%{?with_python2}
%{__python2} setup.py test
%endif

%if 0%{?with_python3}
%{__python3} setup.py test
%endif

%if 0%{?with_python3_other}
%{__python3_other} setup.py test
%endif


%if 0%{?with_python2}
%files -n python2-%{pypi_name}
%doc README*
%license LICENSE
%{python2_sitelib}/*
%endif

%if 0%{?with_python3}
%files -n python%{python3_pkgversion}-%{pypi_name}
%doc README*
%license LICENSE
%{python3_sitelib}/*
%endif

%if 0%{?with_python3_other}
%files -n python%{python3_other_pkgversion}-%{pypi_name}
%doc README*
%license LICENSE
%{python3_other_sitelib}/*
%endif

%changelog
* Mon Jul 16 2018 Avram Lubkin <aviso@rockhopper.net> - 0.5.0-1
- Initial package.
