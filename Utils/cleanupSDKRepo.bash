#!/bin/bash
: <<'END'
    Copyright (C) 2014 Parrot SA

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions
    are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in
      the documentation and/or other materials provided with the 
      distribution.
    * Neither the name of Parrot nor the names
      of its contributors may be used to endorse or promote products
      derived from this software without specific prior written
      permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
    FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
    COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
    INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
    BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
    OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
    AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
    OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
    SUCH DAMAGE.
END

#
# This script is not designed to be directly called !
#

RETCODE=0

function ARHello
{
	echo "Start cleanup for repos $ALL_REPOS" | tee -a $ARLOGF
}

function ARQuit
{
    if [ $RETCODE -eq 0 ]; then
		echo "Finished cleanup for repos $ALL_REPOS" | tee -a $ARLOGF

    else
		echo "Error during cleanup for repos $ALL_REPOS" | tee -a $ARLOGF
    fi
	exit $RETCODE
}

ALL_REPOS=$*

ARHello

if [ -z $2 ]; then
	echo "Must specify at least one directory !" | tee -a $ARLOGF
	RETCODE=1
	ARQuit
fi

for repo in $ALL_REPOS; do
	if [ ! -d $repo ]; then
		echo "$repo is not a directory !" | tee -a $ARLOGF
		RETCODE=1
		ARQuit
	fi
	cleanupFiles=$(find $repo -name 'cleanup')
	for cfile in $cleanupFiles; do
		cdir=$(dirname $cfile)
		here=$(pwd)
		cd $cdir
		echo "Running cleanup in $cdir"
		./cleanup
		cd $here
	done
done
