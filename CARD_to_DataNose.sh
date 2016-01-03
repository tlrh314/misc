#!/bin/bash
# File: CARD_to_DataNose.sh
# Author: Timo L. R. Halbesma <T.L.R.Halbesma@UvA.nl>
# Version: 0.01 (Initial)
# Date created: Sun Jan 03, 2016 12:19 PM
# Last modified: Sun Jan 03, 2016 07:06 pm
#
# Description: Shell script to write (cleaned up, to csv converted) Excel
#                  output from CARD export to DataNose.
#
# Requires Datanose webservice to be up-and-running

set -o errexit

BasePath=$(pwd)
TimeStamp=$(date +%s)  # UNIX timestamp
LogPath="${BasePath}/CARD_to_DataNose_${TimeStamp}"
BaseUrl="http://1.3.3.7:1337"
Now=$(date +"%Y-%m-%dT%H:%M:%S%z")  # ISO 8601
LogLevel="info"

# Write output to stdout && save a copy to $LogFile
# Redirect stdout ( > ) into a named pipe ( >() ) running "tee"
exec > >(tee "${LogPath}.log")
# Pipe stderr to the logfile too.
exec 2>&1

function post_to_datanose() {
    if [ "$LogLevel" == "debug" ]; then
        echo "  Running function '${FUNCNAME}'"
    fi

    # POST request to Datanose.
    # Status: {0: 'Present', 1: 'Reason', 2: 'Absent'}
    url="$BaseUrl/attendance"
    ToPost="DateTime=$1&CourseID=$2&StudentID=$3&Status=0"

    if [ "$LogLevel" == "debug" ]; then
        echo "    post string: '$ToPost'"
    fi

    status=$(curl --silent -d "$ToPost" $url)
    # status="true"  # test without actually posting
    if [ "$status" == "true" ]; then
        # Writing to Datanose succeeded!
        if [ "$LogLevel" == "debug" ]; then
            echo "    SUCCESS: DataNose POST request succeded."
        elif [ "$LogLevel" == "info" ]; then
            # echo "SUCCESS: '$ToPost'"
            echo "SUCCESS"
        fi
    else
        if [ "$LogLevel" == "debug" ]; then
            echo "    ERROR: DataNose POST request failed."
        elif [ "$LogLevel" == "info" ]; then
            # echo "ERROR: '$ToPost'"
            echo "ERROR"
            echo "$ToPost" >> "${LogPath}.err"
        fi
    fi

    # GET request to check Student's (entire) attendance record.
    if [ "$LogLevel" == "debug" ]; then
        DataCheck="$url/?courseID=$2&studentID=$3"
        echo -e "    $(curl --silent --request GET $DataCheck)\n"
    fi
}


function check_student_enrolment() {
    if [ "$LogLevel" == "debug" ]; then
        echo "  Running function '${FUNCNAME}'"
    fi

    url="${BaseUrl}/enrolment/?CourseID=$1&StudentID=$2"

    status=$(curl --silent --request GET $url)

    echo "${status}"
}


function test_connection() {
    if [ "$LogLevel" == "debug" ]; then
        echo "  Running function '${FUNCNAME}'"
    fi

    CourseID="1337"
    StudentID="1337"
    url="${BaseUrl}/attendance/?courseID=$CourseID&studentID=$StudentID"

    {  # try
        status=$(curl --silent -w %{http_code} --connect-timeout 10 --request GET $url -o curl_out.txt) &&

        if [ "$LogLevel" == "debug" ]; then
            echo "    Connection test exit status: $status" &&
            echo -e "    Connection test output:\n    $(cat curl_out.txt)"
        fi
        rm curl_out.txt
    } || {  # except
        echo "    Connection test failed. DataNose Webservice is not responding!"
        echo "    Either relax timeout time and try again, or give up and cry..."
    }
}

function parse_CARD_csv_and_export_to_DataNose () {
    CourseID="$1"
    if [ "$LogLevel" == "debug" ]; then
        echo "  Running function '${FUNCNAME}'"
        echo -e "    CourseID=$CourseID"
    fi

    file="${BasePath}/CARD_Data_${CourseID}_final.csv"

    if [ ! -f "$file" ]; then
        echo "    ERROR: file not found. Check path!"
    fi

    index=0
    while read csvline; do
        AllLines[$index]="$csvline"
        index=$(($index+1))
    done < "$file"

    header=${AllLines[@]:0:1}
    # echo "    $header"
    header_split=(${header//,/ })

    for line in "${AllLines[@]:1}"; do
        # echo "    $line"
        line_split=(${line//,/ })
        StudentID=${line_split[0]}
        UvANetID=${line_split[1]}
        last_year=${line_split[2]}

        if [ "$StudentID" == "" ]; then
            echo "    WARNING: swapping StudentID"
            StudentID="${UvANetID}"
        fi

        echo -n "Student '${StudentID}' enrolled for course '${CourseID}': "
        check_student_enrolment $CourseID $StudentID

        for ((i=3;i<${#line_split[@]};i++)); do
            DateTime="${header_split[$i]}"
            AttendanceStatus="${line_split[$i]}"

            if [ "$AttendanceStatus" == "0" ]; then
                echo "    ${DateTime}, ${CourseID}, ${StudentID}, Absent. DONE"
            elif [ "$AttendanceStatus" == "1" ]; then
                echo -n "    ${DateTime}, ${CourseID}, ${StudentID}, Present, "
                post_to_datanose "${DateTime}" "${CourseID}" "${StudentID}"
            fi
        done
    done

}

function fix_errors () {
    url="$BaseUrl/attendance"
    while read ToPost; do
        echo -n "$ToPost",
        echo $(curl --silent -d "$ToPost" $url)
    done < fixable.err
}



function main() {
    if [ "$LogLevel" == "debug" ]; then
        echo -e "Running script '$(basename "$0")'\n$Now\n"
        echo -e "Logging to:    ${LogPath}.log\n"
        echo "Running function '${FUNCNAME}'"
    fi

    parse_CARD_csv_and_export_to_DataNose "1337" 
    echo 
    echo
    echo

    if [ "$LogLevel" == "debug" ]; then
        test_connection
        echo
    fi

    if [ "$LogLevel" == "debug" ]; then
        post_to_datanose "2014-01-08T11:00:00" "HANK" "1337"
        post_to_datanose "2014-01-08T11:00:00" "1337" "1337"
        echo
    fi

}

# main
fix_errors
exit $?
