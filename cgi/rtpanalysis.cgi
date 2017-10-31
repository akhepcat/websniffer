#!/bin/bash

cat<<EOF
Content-type: text/html

EOF
#<html>
#<head>
#<title>RTP Reporting stat generator</title>
#  <meta http-equiv="Refresh" content="15;/report.html" >
#  <meta http-equiv="Pragma" content="no-cache">
#  <meta http-equiv="Cache-Control" content="no-cache">
#</head>
#<body>
#EOF

if [ -z "$QUERY_STRING" ];
then
    echo "Invalid filename detected"
    exit 1
fi

q="${QUERY_STRING##*filename=}"
fn="${q%%&*}"
file=$(basename $fn)

#echo "<h2>Generating report for $file</h2><br>"

myfile="/data/$file"
size=$(stat --printf="%s" $myfile)

if [ 0 -ge $size ];
then
    echo "Invalid filename detected"
    exit 1
fi

time_s=$(( size / 2702516 ))
time_m=$(( time_s / 60 ))
time_h=$(( time_m / 60 ))
time_ls=$(( time_s % 60 ))
timestamp=$( printf "%02d:%02d:%02d" $time_h $time_m $time_ls )
now=$(date '+%H:%M:%S')

REPORT=$(mktemp /tmp/rtpstat.XXXXXXXXXX) || exit 1
sed "s/NOWNOW/$now/; s/HHCMMCSS/$timestamp/" /var/www/report-template.html > /var/www/report.html

#echo "running report generator<br>"
#echo "</body>"
#echo "<html>"

cat /var/www/report.html

tshark -q -n -r ${myfile} -z rtp,streams -z sip,stat -z h225,counter -z mgcp,rtd -z h225,srt >${REPORT}

cat>/var/www/report.html<<EOF
<html>
<body>
<pre>
EOF
cat ${REPORT} >> /var/www/report.html

#rm -f ${REPORT}
