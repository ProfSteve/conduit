AC_INIT([conduit], [0.3.18],[john.stowers@gmail.com],[conduit])
AM_INIT_AUTOMAKE([1.9])
AC_CONFIG_SRCDIR(conduit/__init__.py)
AC_CONFIG_MACRO_DIR([m4])
AM_MAINTAINER_MODE
AC_SUBST(ACLOCAL_AMFLAGS, "$ACLOCAL_FLAGS -I m4")

################################################################################
# Translation & i18n
################################################################################
GETTEXT_PACKAGE="conduit"
AC_SUBST([GETTEXT_PACKAGE])
AC_DEFINE_UNQUOTED([GETTEXT_PACKAGE], "$GETTEXT_PACKAGE", [Gettext package])
AM_GLIB_GNU_GETTEXT
IT_PROG_INTLTOOL([0.35.0])

################################################################################
# Gnome Doc Utils
################################################################################
GNOME_DOC_INIT

################################################################################
# Requirements
################################################################################
AM_PATH_PYTHON(2.5)

################################################################################
# Browser Implementation
################################################################################
BROWSER_IMPL="webkit"

AC_ARG_WITH([browser_impl],
            AC_HELP_STRING([--with-browser-impl], [webkit (default), system]),
            [],
            [with_browser_impl=webkit])
if test "$with_browser_impl" = "webkit" || 
   test "$with_browser_impl" = "system"; then
        BROWSER_IMPL=$with_browser_impl
fi

AC_SUBST(BROWSER_IMPL)

################################################################################
# Check for neccessary python modules (that dont install pc files)
################################################################################
AM_CHECK_PYMOD([vobject], , , AC_MSG_ERROR([Python module vobject required to run Conduit]))
AM_CHECK_PYMOD([dateutil], , , AC_MSG_ERROR([Python module dateutil required to run Conduit]))
AM_CHECK_PYMOD_VERSION([goocanvas], [pygoocanvas_version], [0.9.0], , AC_MSG_ERROR([Python module goocanvas >= 0.9.0 required to run Conduit]))
AM_CHECK_PYMOD_VERSION([dbus], [__version__], [0.80.0], , AC_MSG_ERROR([Python module dbus >= 0.80.0 required to run Conduit]))
AM_CHECK_PYMOD_VERSION([gio], [pygio_version], [2.16.1], , AC_MSG_ERROR([Python module gio >= 2.16.1 required to run Conduit]))
AM_CHECK_PYMOD_VERSION([gudev], [__version__], [147.1], , AC_MSG_ERROR([Python module gudev >= 147.1 required to run Conduit]))
AM_CHECK_PYMOD_VERSION([gobject], [pygobject_version], [2.21.1], , AC_MSG_ERROR([Python module gobject >= 2.21.1 required to run Conduit]))
AM_CHECK_PYMOD_VERSION([glib], [pyglib_version], [2.21.1], , AC_MSG_ERROR([Python module glib >= 2.21.1 required to run Conduit]))

if test "$with_browser_impl" = "webkit"; then
    AM_CHECK_PYMOD([webkit], , , AC_MSG_ERROR([Python module webkit required to run Conduit]))
fi

################################################################################
# DBus
################################################################################
AC_ARG_WITH([session_bus_services_dir],
            AC_HELP_STRING([--with-session-bus-services-dir], [Path to DBus services directory]))

if test "x$with_dbus_service_dir" != "x"; then
	DBUS_SERVICES_DIR=$with_dbus_service_dir
else
	DBUS_SERVICES_DIR=${datadir}/dbus-1/services
fi
AC_SUBST(DBUS_SERVICES_DIR)

####################################################################
# Nautilus Extension
####################################################################

AC_ARG_ENABLE([nautilus_extension],
              AC_HELP_STRING([--enable-nautilus-extension], [Enable support for nautilus extension]),,
              [enable_nautilus_extension=no])
AC_ARG_WITH([nautilus_extension_dir],
            AC_HELP_STRING([--with-nautilus-extension-dir], [Path to nautilus extension dir]))


AM_CONDITIONAL(ENABLE_NAUTILUS_EXTENSION, test "$enable_nautilus_extension" != "no")
if test "x$with_nautilus_extension_dir" = "x" ; then
	ext_dir="~/.nautilus/python-extensions/"
else
	ext_dir="$with_nautilus_extension_dir"
fi

NAUTILUS_EXTENSION_DIR="$ext_dir"
AC_SUBST(NAUTILUS_EXTENSION_DIR)

####################################################################
# EOG Plugin
####################################################################

AC_ARG_ENABLE([eog_plugin],
              AC_HELP_STRING([--enable-eog-plugin], [Enable support for eog plugin]),,
              [enable_eog_plugin=no])
AC_ARG_WITH([eog_plugin_dir],
            AC_HELP_STRING([--with-eog-plugin-dir], [Path to eog plugin dir]))


AM_CONDITIONAL(ENABLE_EOG_PLUGIN, test "$enable_eog_plugin" != "no")
if test "x$with_eog_plugin_dir" = "x" ; then
	plug_dir="~/.gnome2/eog/plugins/"
else
	plug_dir="$with_eog_plugin_dir"
fi

EOG_PLUGIN_DIR="$plug_dir"
AC_SUBST(EOG_PLUGIN_DIR)

####################################################################
# Totem Plugin
####################################################################

AC_ARG_ENABLE([totem_plugin],
              AC_HELP_STRING([--enable-totem-plugin], [Enable support for Totem plugin]),,
              [enable_totem_plugin=no])
AC_ARG_WITH([totem_plugin_dir],
            AC_HELP_STRING([--with-totem-plugin-dir], [Path to Totem plugin dir]))


AM_CONDITIONAL(ENABLE_TOTEM_PLUGIN, test "$enable_totem_plugin" != "no")
if test "x$with_totem_plugin_dir" = "x" ; then
	plug_dir="~/.config/totem/plugins/"
else
	plug_dir="$with_totem_plugin_dir"
fi

TOTEM_PLUGIN_DIR="$plug_dir"
AC_SUBST(TOTEM_PLUGIN_DIR)

################################################################################
# Write the values of various paths for defs.py
################################################################################
AC_SUBST(VERSION)
AC_SUBST(PACKAGE)

AS_AC_EXPAND(PYTHONDIR, $pythondir)
AS_AC_EXPAND(BINDIR, $bindir)
AS_AC_EXPAND(LIBDIR, $libdir)
AS_AC_EXPAND(LOCALEDIR, $datarootdir/locale)
AS_AC_EXPAND(PKGDATADIR, $datarootdir/$PACKAGE)
AS_AC_EXPAND(DATADIR, $datarootdir/$PACKAGE)
AS_AC_EXPAND(MODULEDIR, $libdir/$PACKAGE/modules)
AS_AC_EXPAND(DESKTOPFILEDIR, $datarootdir/applications)

################################################################################
#-------------------------------------------------------------------------------
################################################################################
AC_OUTPUT(
Makefile
conduit/defs.py
conduit/Makefile
conduit/utils/Makefile
conduit/vfs/Makefile
conduit/datatypes/Makefile
conduit/dataproviders/Makefile
conduit/gtkui/Makefile
conduit/hildonui/Makefile
conduit/platform/Makefile
conduit/modules/Makefile
conduit/modules/BackpackModule/Makefile
conduit/modules/BackpackModule/backpack/Makefile
conduit/modules/BansheeModule/Makefile
conduit/modules/BoxDotNetModule/Makefile
conduit/modules/BoxDotNetModule/BoxDotNetAPI/Makefile
conduit/modules/EvolutionModule/Makefile
conduit/modules/FileModule/Makefile
conduit/modules/FeedModule/Makefile
conduit/modules/FlickrModule/Makefile
conduit/modules/FacebookModule/Makefile
conduit/modules/FacebookModule/pyfacebook/Makefile
conduit/modules/FspotModule/Makefile
conduit/modules/iPodModule/Makefile
conduit/modules/SmugMugModule/Makefile
conduit/modules/SmugMugModule/SmugMugAPI/Makefile
conduit/modules/ShotwellModule/Makefile
conduit/modules/ShotwellModule/shotwell/Makefile
conduit/modules/ShutterflyModule/Makefile
conduit/modules/ShutterflyModule/shutterfly/Makefile
conduit/modules/RhythmboxModule/Makefile
conduit/modules/N800Module/Makefile
conduit/modules/NetworkModule/Makefile
conduit/modules/GConfModule/Makefile
conduit/modules/ZotoModule/Makefile
conduit/modules/Firefox3Module/Makefile
data/Makefile
data/conduit.desktop.in
data/conduit.pc
data/icons/Makefile
data/icons/hicolor/Makefile
data/icons/hicolor/16x16/Makefile
data/icons/hicolor/16x16/actions/Makefile
data/icons/hicolor/16x16/apps/Makefile
data/icons/hicolor/16x16/hildon/Makefile
data/icons/hicolor/16x16/status/Makefile
data/icons/hicolor/22x22/Makefile
data/icons/hicolor/22x22/apps/Makefile
data/icons/hicolor/24x24/Makefile
data/icons/hicolor/24x24/apps/Makefile
data/icons/hicolor/26x26/Makefile
data/icons/hicolor/26x26/apps/Makefile
data/icons/hicolor/32x32/Makefile
data/icons/hicolor/32x32/apps/Makefile
data/icons/hicolor/48x48/apps/Makefile
data/icons/hicolor/48x48/Makefile
data/icons/hicolor/scalable/Makefile
data/icons/hicolor/scalable/apps/Makefile
po/Makefile.in
help/Makefile
tools/Makefile
tools/nautilus-extension/Makefile
tools/eog-plugin/Makefile
tools/totem-plugin/Makefile
)

echo
echo $PACKAGE v$VERSION
echo
echo Prefix............... : $prefix
echo Browser Implementation: $BROWSER_IMPL
echo Dbus Services Dir.... : $DBUS_SERVICES_DIR
echo Nautilus Extension... : $enable_nautilus_extension
echo EOG Plugin........... : $enable_eog_plugin
echo Totem Plugin......... : $enable_totem_plugin
echo

