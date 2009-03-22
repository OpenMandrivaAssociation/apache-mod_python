#Module-Specific definitions
%define mod_name mod_python
%define mod_conf 16_%{mod_name}.conf
%define mod_so %{mod_name}.so

Summary:	An embedded Python interpreter for the apache web server
Name:		apache-%{mod_name}
Version:	3.3.1
Release:	%mkrel 11
Group:		System/Servers
License:	Apache License
URL:		http://www.modpython.org/
Source0:	http://www.apache.org/dist/httpd/modpython/%{mod_name}-%{version}.tgz
Source1:	http://www.apache.org/dist/httpd/modpython/%{mod_name}-%{version}.tgz.asc
Source2:	%{mod_conf}
Source3:	mod_python-manual.conf
Patch0:		mod_python-3.0.3-version.patch
Patch1:		mod_python-20020610-gsr.patch
Patch2:		mod_python-3.1.3-ldflags.patch
Patch3:		mod_python-3.1.4-cflags.patch
Patch4:		mod_python-apr13.diff
Patch5:		mod_python-3.3.1-linkage.patch
BuildRequires:	python
BuildRequires:	python-devel
BuildRequires:	automake1.7
BuildRequires:	autoconf2.5
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.0.54
Requires(pre):	apache >= 2.0.54
Requires:	apache-conf >= 2.0.54
Requires:	apache >= 2.0.54
BuildRequires:  apache-mpm-prefork >= 2.0.54
BuildRequires:  apache-modules >= 2.0.54
BuildRequires:	apache-devel >= 2.0.54
BuildRequires:	file
BuildRequires:	flex >= 2.5.33
Provides:	mod_python
Obsoletes:	mod_python
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
Mod_python is a module that embeds the Python language interpreter within
the apache server, allowing Apache handlers to be written in Python.

Mod_python brings together the versatility of Python and the power of
the Apache Web server for a considerable boost in flexibility and
performance over the traditional CGI approach.

%package	doc
Summary:	Online html documentation for mod_python
Group:		System/Servers
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.0.54
Requires(pre):	apache >= 2.0.54

%description	doc
This package contains the mod_python manual in the html format.

You can view the documentation by using this URL:

http://localhost/manual/mod/mod_python

%prep

%setup -q -n %{mod_name}-%{version}
%patch0 -p0
%patch1 -p0 -b .gsr
%patch2 -p1 -b .ldflags
%patch3 -p1 -b .cflags
%patch4 -p0 -b .apr13
%patch5 -p0 -b .linkage

for i in `find . -type d -name CVS` `find . -type f -name .cvs\*` `find . -type f -name .#\*`; do
    if [ -e "$i" ]; then rm -r $i; fi >&/dev/null
done

# strip away annoying ^M
find . -type f|xargs file|grep 'CRLF'|cut -d: -f1|xargs perl -p -i -e 's/\r//'
find . -type f|xargs file|grep 'text'|cut -d: -f1|xargs perl -p -i -e 's/\r//'

cp %{SOURCE2} %{mod_conf}
cp %{SOURCE3} mod_python-manual.conf

%build
export WANT_AUTOCONF_2_5=1
rm -f configure
libtoolize --copy --force; aclocal-1.7; autoconf --force

export HTTPD="%{_sbindir}/httpd"
%define _disable_ld_no_undefined 1
%configure2_5x --localstatedir=/var/lib \
    --with-apxs=%{_sbindir}/apxs \
    --with-max-locks=4 \
    --with-mutex-dir=/var/cache/httpd/mod_python \
    --with-flex=%{_bindir}/flex

%make APXS_CFLAGS="-Wc,-fno-strict-aliasing"

#pushd test
#    python test.py
#popd

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d
install -d %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d

#export EXCLUDE_FROM_STRIP=%{buildroot}%{_libdir}/apache-extramodules/%{mod_so}

%makeinstall_std

# move the module in place
mv %{buildroot}%{_libdir}/apache/%{mod_so} %{buildroot}%{_libdir}/apache-extramodules

install -d %{buildroot}/var/www/html/addon-modules
ln -s ../../../..%{_docdir}/%{name} %{buildroot}/var/www/html/addon-modules/%{name}

# fix location for mutex files
install -d %{buildroot}/var/cache/httpd/mod_python

# install config files
install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/

# it has to be loaded before 00_manual.conf ;)
install -m0644 mod_python-manual.conf %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d/000_mod_python.conf

# fix absolute path to docdir
perl -pi -e "s|_REPLACE_ME_|%{_docdir}/%{name}-doc|g" %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d/*_mod_python.conf

cat > README.mdv << EOF

There is a bundled test suite that is somewhat tricky to use. I will explain how 
to run it here. I will not cover how to setup the proper rpm build environment and
nessesary packages you will have to install or how to do that.

Install the apache-%{mod_name}-%{version}-%{release}.src.rpm package as a non 
root user. Change directory to where the apache-mod_python.spec file is:

cd ~/RPM/SPECS/

and do:

rpm -bb apache-mod_python.spec

Make the /var/cache/httpd/mod_python directory owned by the user (you) who built the 
apache-%{mod_name}-%{version}-%{release} package.

su root; chown you:you /var/cache/httpd/mod_python

Then exit the root shell and change directory to the rpm build dir:

cd ~/RPM/BUILD/apache-%{mod_name}-%{version}/test

and do:

python test.py

All tests should pass.

Remember to reset the permissions on the mutex cache dir so that the apache user
can use it:

su root; chown apache:apache /var/cache/httpd/mod_python

Done.
EOF

%post
if [ -f /var/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f /var/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%post doc
if [ -f /var/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun doc
if [ "$1" = "0" ]; then
    if [ -f /var/lock/subsys/httpd ]; then
	%{_initrddir}/httpd restart 1>&2
    fi
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc CREDITS NEWS README* examples test
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/*_mod_python.conf
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
/var/www/html/addon-modules/*
%{py_platsitedir}/mod_python/
%{py_platsitedir}/*.egg-info
%attr(0755,apache,apache) %dir /var/cache/httpd/mod_python

%files doc
%defattr(-,root,root)
%doc doc-html/*
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/webapps.d/*_mod_python.conf
