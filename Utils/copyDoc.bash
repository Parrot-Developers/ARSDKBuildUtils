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

RETCODE=0

function ARHello
{
	echo "Start copying documentation for target $TARGET, from directory $DOCDIR, to directory $OUTPUT" | tee -a $ARLOGF
}

function ARQuit
{
    if [ $RETCODE -eq 0 ]; then
		echo "Finished copying documentation for target $TARGET, from directory $DOCDIR, to directory $OUTPUT" | tee -a $ARLOGF
    else
		echo "Error while copying documentation for target $TARGET, from directory $DOCDIR, to directory $OUTPUT" | tee -a $ARLOGF
    fi
	exit $RETCODE
}

# Help function
function usage
{
	echo "Usage:"
	echo $0 "TARGET"
    echo " - TARGET is the name of the target used to generate the documentation"
    exit 1
}

# Generic directories
HERE=$(pwd)
ME=$(which $0)
MYDIR=$(echo $ME | sed 's:\(.*\)/.*:\1:')

# Check for missing args
if [ -z $1 ]; then
	echo "Missing args to copy documentation" | tee -a $ARLOGF
    usage
fi

# Assign args to better names
TARGET=$1
DOCDIR=$MYDIR/../Targets/$TARGET/Build/Doc/

# Output directory
ROOT_OUTPUT=$MYDIR/../../Docs/SDK/
OUTPUT=$ROOT_OUTPUT/$TARGET

ARHello

# 1> Check if the new doc is here
if [ ! -d $DOCDIR ]; then
	echo "$DOCDIR does not exist" | tee -a $ARLOGF
	echo "No documentation to copy for target $TARGET" | tee -a $ARLOGF
	ARQuit
fi

# 2> Remove old doc
rm -rf $OUTPUT

# 3> Copy new doc
mkdir -p $ROOT_OUTPUT
cp -r $DOCDIR $OUTPUT

# 4> Remove tag files
find $OUTPUT -name '*.tag' -delete

# 5> Generate root index.html
ROOT_INDEX=$MYDIR/../../Docs/SDK/index.html

echo "<html>" > $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo "<style type=\"text/css\">" >> $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo "A:link {text-decoration: none}" >> $ROOT_INDEX
echo "A:visited {text-decoration: none}" >> $ROOT_INDEX
echo "A:active {text-decoration: none}" >> $ROOT_INDEX
echo "A:hover {text-decoration: underline; color: red;}" >> $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo "p {margin-left:20px;}" >> $ROOT_INDEX
echo "body { margin-left:5%; margin-right:5%; margin-top:5%; background-color:#F0F0F0; font-family:arial;}" >> $ROOT_INDEX
echo ".title { background-color:red; height:50px; color:white; background-color:gray; padding-top:10px; text-align:center; font-size:40; ; margin-bottom:50px;}" >> $ROOT_INDEX
echo ".titlewhite { color:white;}" >> $ROOT_INDEX
echo ".titlered { color:red; } " >> $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo ".platform { font-size:30; margin-top:20px; margin-bottom:20px;  background-color:#FFFFFF; text-align:center}" >> $ROOT_INDEX
echo ".subtitle { font-size:20; font-style:italic; margin-bottom:20px; text-align:center}" >> $ROOT_INDEX
echo ".footer { background-color:#000000; margin-top:20px;margin-bottom:20px; color:white; width:100%; height:20px;}" >> $ROOT_INDEX
echo ".footer1 { text-align:center; width:80%; float:left; font-size:10; }" >> $ROOT_INDEX
echo ".footer2 { text-align:left; width:20%;font-size:10; padding-left:10px;}" >> $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo "</style>" >> $ROOT_INDEX
echo "<body>" >> $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo "<h1>" >> $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo "<div class=\"title\">" >> $ROOT_INDEX
echo "<span class=\"titlewhite\">ARSDK 3.0 Documentation</span>" >> $ROOT_INDEX
echo "</div>" >> $ROOT_INDEX
echo "" >> $ROOT_INDEX
echo "<div class=\"subtitle\">" >> $ROOT_INDEX
echo "Click on a platform below to open its documentation" >> $ROOT_INDEX
echo "</div>" >> $ROOT_INDEX
echo "" >> $ROOT_INDEX

cd $ROOT_OUTPUT
ALL_TARGETS=$(ls -d -- */ | sed 's:/::')
cd $HERE
for TAR in $ALL_TARGETS; do
	echo "<div class=\"platform\">" >> $ROOT_INDEX
	echo "" >> $ROOT_INDEX
	echo "<a href=./$TAR/index.html target=_blank>$TAR</a>" >> $ROOT_INDEX
	echo "" >> $ROOT_INDEX
	echo "</div>" >> $ROOT_INDEX
done

echo "<div class=\"footer1\">" >> $ROOT_INDEX
echo "Documentation may be similar across different platforms" >> $ROOT_INDEX
echo "</div>" >> $ROOT_INDEX

echo "" >> $ROOT_INDEX
echo "</body>" >> $ROOT_INDEX
echo "</html>" >> $ROOT_INDEX

ARQuit