# AR_DEPENDS([libNAME], [REQUIRED], [HEADERS],                   [HAS_DEBUG],                              [HEADER_ONLY])
#                         Y or N      list of headers to check     Y or N, assumed to be Y if not passed     Y or N, assumed to be N if not passed
AC_DEFUN([AR_DEPENDS],  [
                        # Add with args
                        # - Install dir
                        AC_ARG_WITH([$1InstallDir],
                        AS_HELP_STRING([--with-$1InstallDir=DIR],[directory of the $1 installation @<:@default=PREFIX@:>@]),
                        [if test x$withval = xno; then
                        $1InstallDir=""
                        else
                        $1InstallDir="$withval"
                        fi],
                        [if test x$prefix = xNONE; then
                        $1InstallDir=""
                        else
                        $1InstallDir="$prefix"
                        fi])
                        # - Include dir
                        AC_ARG_WITH([$1IncludeDir],
                        AS_HELP_STRING([--with-$1IncludeDir=DIR],[directory of the $1 headers @<:@default=$1InstallDir/include@:>@]),
                        [if test x$withval = xno; then
                        $1IncludeDir=""
                        else
                        $1IncludeDir="$withval"
                        fi],
                        [if test ! -z $$1InstallDir; then
                        $1IncludeDir="$$1InstallDir/include"
                        else
                        $1IncludeDir=""
                        fi])
                        # - Lib dir
                        AC_ARG_WITH([$1LibDir],
                        AS_HELP_STRING([--with-$1LibDir=DIR],[directory of the $1 libraries @<:@default=$1InstallDir/lib@:>@]),
                        [if test x$withval = xno; then
                        $1LibDir=""
                        else
                        $1LibDir="$withval"
                        fi],
                        [if test ! -z $$1InstallDir; then
                        $1LibDir="$$1InstallDir/lib"
                        else
                        $1LibDir=""
                        fi])
                        # Add include dir to -I path
                        if test ! -z $$1IncludeDir; then
                        CFLAGS+=" -I$$1IncludeDir"
                        CPPFLAGS+=" -I$$1IncludeDir"
                        OBJCFLAGS+=" -I$$1IncludeDir"
                        fi
                        if test x$5 != xY; then
                        # Add lib dir to -L path
                        if test ! -z $$1LibDir; then
                        LDFLAGS+=" -L$$1LibDir"
                        fi
                        fi
                        # Check given headers
                        ar_$1_support="no"
                        if test x$2 = xY; then
                        AC_CHECK_HEADERS([$3],ar_$1_support="yes",AC_MSG_ERROR(The $1 headers are required in order to build the library!
- Use --with-$1InstallDir or --with-$1IncludeDir to incidate a specific include path.))
                        else
                        AC_CHECK_HEADERS([$3],ar_$1_support="yes",AC_MSG_WARN(The $1 headers were not found: compiling without $1 support.))
                        fi
                        # Define HAVE name
                        define([AR_HAVE_NAME], [HAVE_]translit($1, "a-z", "A-Z"))
                        # Define AM variable HAVE_Name for Makefile.am tests
                        AM_CONDITIONAL(AR_HAVE_NAME, [test x$ar_$1_support = xyes])
                        # Define AC preprocessor variable HAVE_Name for Source tests
                        if test x$ar_$1_support = xyes; then
                        AC_DEFINE_UNQUOTED(AR_HAVE_NAME, [1], [$1 presence])
                        fi
                        # Add -l directives
                        if test x$5 != xY; then
                        if test x$ar_$1_support = xyes; then
                        LNAME=$(echo $1 | sed 's:^lib::' | tr @<:@:upper:@:>@ @<:@:lower:@:>@)
                        if test x$debugit = xyes && test x$4 != xN; then
                        LNAME+="_dbg"
                        fi
                        LDFLAGS+=" -l$LNAME"
                        fi
                        fi
                        ])