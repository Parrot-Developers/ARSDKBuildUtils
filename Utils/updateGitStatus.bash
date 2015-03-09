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
EXIT_ON_FAILED=''
REPO_REVISION=''

function ARHello
{
    echo "Start updating status for repo $REPODIR" | tee -a $ARLOGF
}

function ARQuit
{
    if [ $RETCODE -eq 0 ]; then
        echo "Finished updating status for repo $REPODIR" | tee -a $ARLOGF
    elif [[ $EXIT_ON_FAILED = "exitOnFailed" ]]; then
        echo "==============================================================================================="
        echo "Error while updating for repo $REPODIR, is not sync to remote ($REPO_REVISION)" | tee -a $ARLOGF
        echo "==============================================================================================="
        echo "$RETCODE"
        exit $RETCODE
    else
        echo "Do you want to skip $REPODIR ?"
        select yn in "Yes" "No" "Retry" "Stash/Stash-Pop" "Show-Diff" "Reset"; do
            case $yn in
                Yes )
                    echo "Skipping $REPODIR" | tee -a $ARLOGF
                    RETCODE=0
                    break
                    ;;
                Retry )
                    echo "Trying again" | tee -a $ARLOGF
                    $ME $REPODIR $REPO_URL $REPO_REVISION $EXIT_ON_FAILED
                    RETCODE=$?
                    break
                    ;;
                Stash/Stash-Pop )
                    echo "Stashing your changes" | tee -a $ARLOGF
                    if ! git stash; then
                        echo "Error while stashing !" | tee -a $ARLOGF
                        RETCODE=1
                        break
                    fi
                    $ME $REPODIR $REPO_URL $REPO_REVISION $EXIT_ON_FAILED
                    RETCODE=$?
                    if [ $RETCODE -ne 0 ]; then
                        break
                    fi
                    if ! git stash pop; then
                        echo "Stash pop failed ... Go fix it manually !" | tee -a $ARLOGF
                        RETCODE=1
                    fi
                    break
                    ;;
                Show-Diff )
                    echo "Showing diff in the repo" | tee -a $ARLOGF
                    if ! git diff; then
                        echo "Error while showing diff !" | tee -a $ARLOGF
                        RETCODE=1
                        break
                    fi
                    $ME $REPODIR $REPO_URL $REPO_REVISION $EXIT_ON_FAILED
                    RETCODE=$?
                    break
                    ;;
                Reset )
                    RETCODE=0
                    echo "Are you sure you want to reset $REPODIR ???" | tee -a $ARLOGF
                    select ryn in "Yes" "No"; do
                        case $ryn in
                            Yes )
                                if ! git reset --hard; then
                                    echo "Error while resetting !" | tee -a $ARLOGF
                                    RETCODE=1
                                fi
                                break
                                ;;
                        esac
                    done
                    if [ $RETCODE -eq 0 ]; then
                        $ME $REPODIR $REPO_URL $REPO_REVISION $EXIT_ON_FAILED
                        RETCODE=$?
                    fi
                    break
                    ;;

            esac
            echo "Error while updating status for repo $REPODIR" | tee -a $ARLOGF
            break
        done
    fi
    exit $RETCODE
}

function usage
{
    echo "Usage:"
    echo $0 "REPODIR REMOTE_URL REPO_REVISION"
    echo " - REPODIR is the path to the repository root directory"
	echo " - REMOTE_URL is the requested remote URL"
    echo " - REPO_REVISION is the revision to checkout."
    echo "    It can be a branch name, a tag name, a commit sha1"
    echo "    or 'DEV' (i.e. don't touch the repo)"
    echo "    or 'CURR_BRANCH' (i.e. just check and pull, do not checkout anything)"
    echo "    If it's a branch name, the branch will be pulled"
    echo " - EXIT_ON_FAILED (optionnal). Put 'exitOnFailed' to force"
    echo "    the script to stop on any error, without prompt"
    exit 1
}

HERE=$(pwd)
ME=$(which $0)
MYDIR=$(echo $ME | sed 's:\(.*\)/.*:\1:')

# Test if the parameters are correct
if [ -z $1 ] || [ -z $2 ] || [ -z $3 ]; then
    echo "Missing args to check git repository status" | tee -a $ARLOGF
    usage
fi

REPODIR=$1
REPO_URL=$2
REPO_REVISION=$3
if [ -n $4 ]; then
    EXIT_ON_FAILED=$4
    echo "==$EXIT_ON_FAILED =="
fi

ARHello

if [ ! -d $REPODIR ]; then
    echo "Repository $REPODIR does not exists" | tee -a $ARLOGF
    RETCODE=1
    ARQuit
fi

NEEDS_CHECKOUT="YES"
NEEDS_PULL="YES"

if [ x$REPO_REVISION = xDEV ]; then
    echo "Don't touch repo $REPODIR (revision = DEV)" | tee -a $ARLOGF
    ARQuit
elif [ x$REPO_REVISION = xCURR_BRANCH ]; then
    echo "Using current branch/tag as target reivision" | tee -a $ARLOGF
    NEEDS_CHECKOUT="NO"
fi

cd $REPODIR

NEED_ADD_REMOTE=NO
SKIP_REMOTE_TEST=NO
NEED_SET_REMOTE=NO

if ! git remote -v 2>&1 | grep origin >/dev/null 2>&1; then
	echo "Missing remote origin"
    echo "Do you want to add origin remote ($REPO_URL) ?"
    select yn in "Yes" "No"; do
        case $yn in
			Yes )
				NEED_ADD_REMOTE=YES
				break
				;;
			No )
				SKIP_REMOTE_TEST=YES
				break
				;;
		esac
	done
fi

if [ x$NEED_ADD_REMOTE = xYES ]; then
	if ! git remote add origin $REPO_URL 2>&1 >/dev/null; then
		echo "Error while adding remote origin"
		RETCODE=1
		ARQuit
	fi
fi

if [ x$SKIP_REMOTE_TEST = xNO ]; then
	CURRENT_REMOTE=$(git remote -v | grep origin | grep fetch | sed 's:[^[:blank:]]*[[:blank:]]*\([^[:blank:]]*\)[[:blank:]]*.*:\1:')

	if [ ! x"$CURRENT_REMOTE" = x"$REPO_URL" ]; then
		echo "Origin does not point to $REPO_URL, but instead to $CURRENT_REMOTE"
		echo "Do you want to change it to $REPO_URL ?"
		select yn in "Yes" "No"; do
			case $yn in
				Yes )
					NEED_SET_REMOTE=YES
					break
					;;
				No )
					break
					;;
			esac
		done
	fi

	if [ x$NEED_SET_REMOTE = xYES ]; then
		if ! git remote set-url origin $REPO_URL 2>&1 >/dev/null; then
			echo "Error while setting origin URL to $REPO_URL"
			RETCODE=1
			ARQuit
		fi
	fi
fi

if ! git status 2>&1 >/dev/null; then
    echo "Error while updating repo status" | tee -a $ARLOGF
    RETCODE=1
    ARQuit
fi

if ! git diff-files --quiet; then
    echo "The repo $REPODIR has local changes" | tee -a $ARLOGF
    RETCODE=1
    ARQuit
fi

if ! git diff-index --cached --quiet HEAD; then
    echo "The repo $REPODIR has local changes" | tee -a $ARLOGF
    RETCODE=1
    ARQuit
fi

if [ x$NEEDS_CHECKOUT = xYES ]; then
    CURR_SHA1=$(git rev-parse HEAD)
    if [ $CURR_SHA1 = $REPO_REVISION ]; then
        echo "Already on good sha1" | tee -a $ARLOGF
        NEEDS_CHECKOUT="NO"
        NEEDS_PULL="NO"
    else
        TAGS_HERE=$(git tag --points-at HEAD)
        for TAG in $TAGS_HERE; do
            if [ "$TAG" = "$REPO_REVISION" ]; then
                echo "Already on good tag (or at least on the sha1 pointed by the tag)" | tee -a $ARLOGF
                NEEDS_CHECKOUT="NO"
                NEEDS_PULL="NO"
            fi
        done
    fi
fi

if [ x$NEEDS_CHECKOUT = xYES ]; then
    if ! git fetch; then
        echo "Unable to fetch $REPODIR" | tee -a $ARLOGF
        RETCODE=1
        ARQuit
    fi
    if ! git fetch --tags; then
        echo "Unable to fetch --tags $REPODIR" | tee -a $ARLOGF
        RETCODE=1
        ARQuit
    fi
    if ! git checkout $REPO_REVISION; then
        echo "Unable to checkout $REPO_REVISION for $REPODIR" | tee -a $ARLOGF
        echo " --> Working tree might have changed !" | tee -a $ARLOGF
        RETCODE=1
        ARQuit
    fi
fi

if [ x$NEEDS_PULL = xYES ]; then
	if git symbolic-ref -q HEAD; then
		REMOTE=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
		if [ x$REMOTE != x'@{u}' ]; then
        # On a branch, with a tracking remote one
			CNT=$(git rev-list $REMOTE..HEAD -n 1 | wc -l)
			if [ $CNT -ne 0 ]; then
				echo "Local commits found on a remote tracking branch" | tee -a $ARLOGF
				echo " --> Don't pull because a merge conflict could happen" | tee -a $ARLOGF
				RETCODE=1
				ARQuit
			fi
		fi
		echo "On a branch, pulling" | tee -a $ARLOGF
		if ! git pull; then
			echo "Unable to pull the branch" | tee -a $ARLOGF
			RETCODE=1
			ARQuit
		fi
	fi
fi

cd $HERE
ARQuit
