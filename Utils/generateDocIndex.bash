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
	echo "Start generating $OUTPUT_FILE for target $TARGET" | tee -a $ARLOGF
}

function ARQuit
{
    if [ $RETCODE -eq 0 ]; then
		echo "Finished generating $OUTPUT_FILE for target $TARGET" | tee -a $ARLOGF
    else
		echo "Error while generating $OUTPUT_FILE for target $TARGET" | tee -a $ARLOGF
    fi
	exit $RETCODE
}

# Help function
function usage
{
    echo "Usage:"
    echo $0 "DOCDIR TARGET"
    echo " - DOCDIR is the root directory of the library documentations"
	echo " - TARGET is the name of the target for which the doc was generated"
    exit 1
}

# Generic directories
HERE=$(pwd)
ME=$(which $0)
MYDIR=$(echo $ME | sed 's:\(.*\)/.*:\1:')

# Check for missing args
if [ -z $1 ] || [ -z $2 ]; then
	echo "Missing args to generate doc index" | tee -a $ARLOGF
    usage
fi

# Assign args to better names
DOCDIR=$1
TARGET=$2

# Create index.html
OUTPUT_FILE=$DOCDIR/index.html

# Test file for Javadoc dirs
JAVADOC_TEST_FILE=$DOCDIR/index-all.html

ARHello

if [ -f $JAVADOC_TEST_FILE ]; then
	echo "Operating on a javadoc directory : do not modify index.html" | tee -a $ARLOGF
	ARQuit
fi

echo "<html>" > $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "<style type=\"text/css\">" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "A:link {text-decoration: none}" >> $OUTPUT_FILE
echo "A:visited {text-decoration: none}" >> $OUTPUT_FILE
echo "A:active {text-decoration: none}" >> $OUTPUT_FILE
echo "A:hover {text-decoration: underline; color: red;}" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "p {margin-left:20px;}" >> $OUTPUT_FILE
echo "body { margin-left:5%; margin-right:5%; margin-top:5%; background-color:#F0F0F0; font-family:arial;}" >> $OUTPUT_FILE
echo ".title { background-color:red; height:50px; color:white; background-color:gray; padding-top:10px; text-align:center; font-size:40; ; margin-bottom:50px;}" >> $OUTPUT_FILE
echo ".titlewhite { color:white;}" >> $OUTPUT_FILE
echo ".titlered { color:red; } " >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo ".library { font-size:30; margin-top:20px; margin-bottom:20px;  background-color:#FFFFFF; text-align:center}" >> $OUTPUT_FILE
echo ".subtitle { font-size:20; font-style:italic; margin-bottom:20px; text-align:center}" >> $OUTPUT_FILE
echo ".footer { background-color:#000000; margin-top:20px;margin-bottom:20px; color:white; width:100%; height:50px;}" >> $OUTPUT_FILE
echo ".footer1 { text-align:right; width:80%; float:left; font-size:20; }" >> $OUTPUT_FILE
echo ".footer2 { text-align:left; width:20%;font-size:45; padding-left:10px;}" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "</style>" >> $OUTPUT_FILE
echo "<body>" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "<h1>" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "<div class=\"title\">" >> $OUTPUT_FILE
echo "<span class=\"titlewhite\">ARSDK 3.0 Documentation for $TARGET</span>" >> $OUTPUT_FILE
echo "</div>" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE
echo "<div class=\"subtitle\">" >> $OUTPUT_FILE
echo "Click on a library below to open its documentation" >> $OUTPUT_FILE
echo "</div>" >> $OUTPUT_FILE
echo "" >> $OUTPUT_FILE

cd $DOCDIR
LIBRARIES=$(ls -d -- */ | sed 's:/::')
cd $HERE
for LIB in $LIBRARIES; do
	LINK=./$LIB/index.html
	if [ ! -f $DOCDIR/$LINK ]; then
		LINK=./$LIB/html/index.html
	fi
	if [ -f $DOCDIR/$LINK ]; then
		echo "<div class=\"library\">" >> $OUTPUT_FILE
		echo "" >> $OUTPUT_FILE
		echo "<a href=$LINK target=_blank>$LIB</a>" >> $OUTPUT_FILE
		echo "" >> $OUTPUT_FILE
		echo "</div>" >> $OUTPUT_FILE
	fi
done

echo "" >> $OUTPUT_FILE
echo "</body>" >> $OUTPUT_FILE
echo "</html>" >> $OUTPUT_FILE

echo "Generated $OUTPUT_FILE for target $TARGET" | tee -a $ARLOGF

ARQuit
