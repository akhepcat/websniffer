#!/usr/bin/perl
use strict;
use warnings;
use File::Basename;
my $myself = "cgi-bin/" . basename($0);


my($hostname,$mounted,$halted,$archiving,$kept,$file,$i,$var,$action,$status);
my %cgivars;
my %customers;
my ($timedaysup,$hoursup, $rest, $uptime, $head, $time, $up, $days, $filter, $server, $ruser, $rhost);

# my (%customers);

print "Content-type: text/html\n\n";

if (defined($ENV{"SERVER_NAME"}) && length($ENV{"SERVER_NAME"}) > 3) {
  $server = $ENV{"SERVER_NAME"};
} else {
  $server = $hostname;
}

if (defined($ENV{"REMOTE_ADDR"}) && length($ENV{"REMOTE_ADDR"}) > 3) {
  $rhost = $ENV{"REMOTE_ADDR"};
} else {
  $rhost = "unknown";
}
if (defined($ENV{"REMOTE_USER"}) && length($ENV{"REMOTE_USER"}) > 2) {
  $ruser = $ENV{"REMOTE_USER"};
} else {
  $ruser = "anonymous";
}


my($METHOD) = "GET";

$hostname = `hostname -s`; chomp ($hostname);
$uptime=`uptime`;
chomp($uptime);

($timedaysup,$hoursup, $rest) = split ( /,/, $uptime );
($head, $time, $up, $days, $rest) = split(/ /, $timedaysup);

$uptime="$days $rest" . $hoursup;

my $m_point="/data";
$mounted = `mount | grep "$m_point"`; chomp($mounted);
my $fsstat = `LANG=en_US touch $m_point 2>&1 | grep -ci Read-only`;

if ( ( ! -r "/data/.sniffer/halt" ) && 
     ( ( ! -r "/data/.sniffer/archiving" ) && ( ! -r "/data/.sniffer/startup" ) && ( ! -e "/data/.sniffer/pids" || -z "/data/.sniffer/pids") ) ) {
     `touch /data/.sniffer/halt`;
}

$archiving=((-r "/data/.sniffer/archiving")?1:0);
$halted=((-r "/data/.sniffer/halt")?1:0);
if (-r "/data/.sniffer/startup") {
  $status=`cat /data/.sniffer/startup`; chomp($status);
} else {
  $status="&nbsp;";
}

if (-r "/root/bin/slr-cap" ) {
  $filter=`grep "^FILTER" /root/bin/slr-cap`; chomp($filter);
  $filter =~ s/.*=//g; 
  $filter =~ s/\"//g; 
  $filter =~ s/.*\///g;
  $filter =~ s/.*\.//g;
}
  
if (-r "/root/bin/sipcapper" ) {
   open(FILTERS, "/root/bin/sipcapper -L |");
   while (<FILTERS>) {
      chomp;
      if (m/^(\S+) - (.*)/) {
          $customers{$1} = $2;
      }
   }
}

my $eth1up=`ethtool eth1 | grep -i 'detected.*yes' | wc -c`;
my $eth2up=`ethtool eth2 | grep -i 'detected.*yes' | wc -c`;
my $ok2cap="";
if ( $eth1up + $eth2up == 0 ) {
  $ok2cap="<font color='red'>No available interfaces for capture</font>";
  $eth1up="<font color='red'>DOWN</font>";
  $eth2up=$eth1up;
} else {
  $eth1up=(($eth1up == 0)?"<font color='brown'>n/a</font>":"<font color='green'>UP</font>");
  $eth2up=(($eth2up == 0)?"<font color='brown'>n/a</font>":"<font color='green'>UP</font>");
}
 
if (-r "/data/.sniffer/action") {
  $action=`cat /data/.sniffer/action`; chomp($action);
  &do_status($action);
  exit 0;
}

if ( &cgi_request() ) {
  %cgivars = &getcgivars;

} else {
  &display_form($halted);
  exit 0;
}
 
if (defined($cgivars{"action"})) {
  $cgivars{"action"} =~ s/\0//;
}


if (! (  (defined($cgivars{"filename"}) && defined($cgivars{"action"})) ||
         (defined($cgivars{"action"}) && ($cgivars{"action"} eq "purge" || $cgivars{"action"} eq "purgeforsure" || $cgivars{"action"} =~ m/^filter/ )) || 
          defined($cgivars{"startstop"})
   )  ) {

  &display_form($halted);

} else {

  if ( defined($cgivars{"action"}) && $cgivars{"action"} eq "delete" ) {
    &do_server("delete");

  } elsif ( defined($cgivars{"action"}) && $cgivars{"action"} eq "deleteforsure" ) {
      &do_server("deleteforsure");

  } elsif ( defined($cgivars{"action"}) && $cgivars{"action"} eq "purge" ) {
    &do_server("purge");

  } elsif ( defined($cgivars{"action"}) && $cgivars{"action"} eq "purgeforsure" ) {
      &do_server("purgeforsure");

  } elsif ( defined($cgivars{"action"}) && $cgivars{"action"} eq "archive" ) {
    &do_server("archive");

  } elsif ( defined($cgivars{"action"}) && $cgivars{"action"} eq "report" ) {
    &do_server("report");

  } elsif ( defined($cgivars{"action"}) && $cgivars{"action"} eq "moveforsure" ) {
    &do_server("moveforsure");

  } elsif ( defined($cgivars{"action"}) && $cgivars{"action"} =~ m/^filter/ ) {
    &do_server($cgivars{"action"});

  } elsif ( defined($cgivars{"startstop"}) && $cgivars{"startstop"} eq "stop" ) {
    &do_server("stop");

  } elsif ( defined($cgivars{"startstop"}) && $cgivars{"startstop"} eq "start" ) {
    &do_server("start");

  } else {
      &HTMLdie("Invalid contents of cgi variable");
  }
}

exit;

##########################################################


sub do_server()
{
my($action) = @_;
my($file);
my(@files);

  if (defined($cgivars{"filename"})) {
    foreach $file (split(/\0/,$cgivars{"filename"}) ) {
      push @files, $file;
    }
  }
  
  print qq|<html><head><title>$hostname - web sniffer management</title>\n|;

  if ( $action eq "deleteforsure" || $action eq "purgeforsure" || $action eq "moveforsure" || $action =~ m/filter/ || defined($cgivars{"startstop"}) ) {
    print qq|  <meta HTTP-EQUIV="Refresh" CONTENT="15;https://$server/$myself" >
  <meta HTTP-EQUIV="Pragma" CONTENT="no-cache">
  <meta HTTP-EQUIV="Cache-Control" content="no-cache">\n|;
  }

  print qq|</head>
  <body>
  <h2>$hostname - web sniffer control</h2>
  This application is the property of GCI and contains sensitive information.
  <br><br>
  <a href="https://$server/$myself">Back to the main page</a><br>
  <br>
  <p>Welcome, $ruser from $rhost!</p>
  |;


  if ($action eq "delete") {
    print qq|<form method="$METHOD" action="https://$server/$myself">\n
       You have chose to delete the following files:&nbsp;
<input type="submit" value="deleteforsure" name="action" /><br><br>\n |;

    foreach $file (@files) {
      print qq|<input type="hidden" name="filename" value="$file" />\n|;
      print qq|$file<br>\n|;
    }

    print qq|</form>\n|;

  } elsif ($action =~ m/filter/ ) {
    my($a,$f) = split(/ /, $action);
    if($f =~ m/allcusts/) {
       print qq|You are removing the capture filter<br><br>\n |;
    } else {
       print qq|You are changing the filter to: '$f'<br><br>\n |;
    }
    print qq|<!-- do-action = "$action" -->\n|;

    `echo "$action" > /data/.sniffer/action`;
    `/bin/bash /root/bin/do-action`;

    print "The filter has been updated.  You will be redirected to the main page within 15 seconds.<br><br>\n";

  } elsif ($action eq "purge") {
    print qq|<form method="$METHOD" action="https://$server/$myself">\n
       You have chose to delete ALL existing capture files:&nbsp;
<input type="submit" value="purgeforsure" name="action" /><br><br>\n |;

    print qq|</form>\n|;

  } elsif ($action eq "archive") {
    print qq|<form method="$METHOD" action="https://$server/$myself">\n
       You have chose to archive the following files:&nbsp;
<input type="submit" value="moveforsure" name="action" /><br><br>\n |;

    foreach $file (@files) {
      print qq|<input type="hidden" name="filename" value="$file" />\n|;
      print qq|$file<br>\n|;
    }

    print qq|</form>\n|;

  } elsif ($action eq "report") {
    print qq|<form method="$METHOD" action="https://$server/cgi-bin/rtpanalysis.cgi">\n
       You have chose to generate an RTP report on the following files:&nbsp;
<input type="submit" value="Generate" name="action" /><br><br>\n |;

    foreach $file (@files) {
      print qq|<input type="hidden" name="filename" value="$file" />\n|;
      print qq|$file<br>\n|;
    }

    print qq|</form>\n|;

    print qq|<h2>only the first file listed will have a report generated.</h2>\n|;
    
  } elsif ( $action eq "purgeforsure" ) {
    chdir("/data");

   @files = glob("eth*.cap");
   foreach $file (@files) {
      if ( -r "$file" ) {
           unlink($file) || print qq|<strong>Error removing $file</strong>|;
      }
   }

    print "All capture files have been deleted.  You will be redirected to the main page within 15 seconds.<br><br>\n";
    
  } elsif ( $action eq "deleteforsure" ) {
    print "The following files have been deleted.  You will be redirected to the main page within 15 seconds.<br><br>\n";
    
    foreach $file (@files) {
      print $file . "&nbsp;";

      if ( -r "/data/$file" ) {
           unlink("/data/$file") || print qq|<strong>Error removing</strong>|;
      } elsif ( -r "/root/keep/$file" ) {
           unlink("/root/keep/$file") || print qq|<strong>Error removing</strong>|;
      } else {
           print qq|<strong>Can't locate in archive.</strong>|;
      }
      print "<br>\n";
   }

  } elsif ( $action eq "moveforsure" ) {
    print "The following files have been queued for archiving.  You will be redirected to the main page within 15 seconds.<br><br>\n";
    
    foreach $file (@files) {
      print $file . "&nbsp;";

      if ( -r "/data/$file" ) {
           rename("/data/$file", "/data/keep/$file") || print qq|<strong>Error moving</strong>, $!|;
      } elsif ( -r "/root/keep/$file" ) {
           print qq|<strong>Ignoring</strong> - already archived.|;
      } else {
           print qq|<strong>Can't locate in filesystem.</strong>|;
      }
      print "<br>\n";
    }    
    
  } elsif ($action eq "start") {
    print qq|You may experience a delay of up to a minute before the sniffer starts.<br>\n
    You will be redirected back to the main page after the sniffer within 15 seconds.|;
    `echo "start" > /data/.sniffer/action`;

  } elsif ($action eq "stop") {
    # stopping
    print qq|The sniffer should be stopped within the next minute. You will be redirected back to the main page within 15 seconds.\n|;
    `echo "stop" > /data/.sniffer/action`;

  } else {
    print "Invalid action request. You have been logged<br>\n";
    print qq|</body></html>\n|;
    exit 0
  }

  print qq|  <hr>
</body>
|;

}


sub display_form()
{
  my($halted)= @_;
  my($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$atime,$mtime,$ctime,$blksize,$blocks,$size1,$size2);
  my($kept,$file,$i,$v);
  my(@eth1s,@eth2s);

  my $select = qq|<input type="checkbox" name="filename"|;

print qq|<html>
<head>
  <title>$hostname - web sniffer archive</title>\n|;

print qq|<style type="text/css">
.red_text
{    
        color:#ff0000;
        font-size:14px;
}
.black_text
{    
        color:#000000;
        font-size:14px;
}
</style>

<script type="text/javascript">
function doFilter( id ) {
  var node = document.getElementById( id );
  // Check to see if valid node and if node is a SELECT form control
  if( node && node.tagName == "SELECT" ) {
    // Go to web page defined by the VALUE attribute of the OPTION element
    var data = node.options[node.selectedIndex].value;
    var action = "filter ";
    var submit = action.concat(data);
    document.getElementById("filter").value=submit;
    var myform = document.getElementById("myform");
    myform.submit();
  } // endif
}

</script>
\n|;

if ( length($mounted) && ! $halted ) {
  print qq|<meta HTTP-EQUIV="Refresh" CONTENT="60;https://$server/$myself" >
  <meta HTTP-EQUIV="Pragma" CONTENT="no-cache">
  <meta HTTP-EQUIV="Cache-Control" content="no-cache">\n|;
}

print qq|</head>
<body>
  <h2>$hostname - web sniffer archive</h2>
  These files are the property of GCI and contain sensitive information. Do not distribute.
  <p>Welcome, $ruser from $rhost!</p>
  <br>Uptime: $uptime
  <br><br>\n|;

if ( length($mounted) && ! $halted ) {
print qq|
  This page will automatically refresh every 60 seconds.
  <br>\n|;
}

if ( $fsstat == 1 ) {
  print qq|<hr><center><br><h2><font color="red">The data disk is currently read-only in an error-state.<br>
  No new captures will be collected.<br>
  Please report this to the admin.</font></h2><br></center>\n|;
}

if ( ! length($mounted) ) {
  print qq|<hr><br><h2>No capture files are available, as the datastore is not mounted,<br>
  or the disk is currently offline.</h2><br>\n|;
} else {
  print "<hr><pre>\n" . `df -k /data` . "</pre>\n";
  my(%cols);

  print qq|<hr>
  <form id="myform" method="$METHOD" action="https://$server/$myself">
  <table width="100%" columns="7">
    <tr><td align="center" colspan="7">|;
  if ($halted) {
    print qq|<input type="submit" value="start" name="startstop" />\n|;
  } else {
    print qq|<input type="submit" value="stop" name="startstop" />\n|;
  }
  print qq|<strong>Live Capture Files</strong></td></tr>\n|;

  if ( length($filter) ) {
    print qq|<tr><td align="center" colspan="7">Filtering enabled on customer:</td></tr>\n|;
  }
  print qq|<tr><td colspan="7" style="width: 100%; text-align:center; vertical-align:middle;"><select id="Fselect">\n|;
  my($f);
  foreach $f (sort keys %customers) {
     if ($f eq $filter) {
          print qq|<option value="$f" selected>$customers{$f}</option>\n|;
     } else {
          print qq|<option value="$f">$customers{$f}</option>\n|;
     }
  }
  print qq|</select>\n|;
  print qq|<input type="button" value="Change Filter" onclick="doFilter('Fselect')"/>\n|;
  print qq|</td></tr>\n|;
  print qq|<tr><td><input type='hidden' id='filter' name='action' value='' /></td></tr>\n|;

  if ( $halted ) {
    print qq|<tr><td align="center" colspan="7"><strong><font color="red">Capture is currently halted.</font></strong></td></tr>\n|;
    print qq|<tr><td align="center" colspan="7">$ok2cap</td></tr>\n|;
    print qq|<tr><td align="center" colspan="7">$status</td></tr>\n|;
  }


  if ( $archiving ) {
    print qq|<tr><td align="center" colspan="7"><strong><font color="red">Background archiving in progress.</font></strong></td></tr>\n|;
  }

  print qq|<tr><td align="center" colspan="7">
  <input type="submit" value="delete" name="action" />\n
  <input type="submit" value="purge" name="action" />\n
  <input type="submit" value="archive" name="action" />\n
  <!-- input type="submit" value="report" name="action" / -->\n|;

  print qq|</td></tr>\n|;
  print qq|<tr><td width="2%">&nbsp;</td><th width="30%" align="center">eth1($eth1up)</th><td width="15%">&nbsp;</td><td width="*" >&nbsp;</td><td width="2%">&nbsp;</td><th width="30%" align="center">eth2($eth2up)</th><td width="15%">&nbsp;</tr>\n|;

  chdir("/data");

  @eth1s = glob("eth1*");

  $i=0;
  foreach $file (sort @eth1s) {
      if (!defined($file) || (! length($file) > 0) ) {
         $file="";
      }
      $cols{$i}{"col1"} = $file;
      $i++;
  }

  $i=0;
  @eth2s = sort glob("eth2*");
  foreach $file (sort @eth2s) {
      if (!defined($file) || (! length($file) > 0) ) {
         $file="";
      }
      $cols{$i}{"col2"} = $file;
      $i++;
  }


  foreach $i (sort(keys %cols)) {
      if (!defined($cols{$i}{"col1"}) || ( ! length($cols{$i}{"col1"}) ) ) {
         print qq|<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp</td><td>&nbsp</td>|;
      } else {
         ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size1,$atime,$mtime,$ctime,$blksize,$blocks) = stat($cols{$i}{"col1"});
         $v = $select . qq| value="| . $cols{$i}{"col1"} . qq|" />|;
         if ( $mtime == $ctime ) { $v = "<span style='color: red;'>***</span>"; };
         print qq|<tr>
<td>$v</td><td align="center"><a href="https://$server/websniff/$cols{$i}{"col1"}">$cols{$i}{"col1"}</a></td>
<td>| . (int($size1 / 1024 / 1000 )/1000). qq| Gb</td>
<td>&nbsp;</td>|;
      }
      
      if (!defined($cols{$i}{"col2"}) || ( ! length($cols{$i}{"col2"}) ) ) {
         print qq|<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp</td>|;
      } else {
         ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size2,$atime,$mtime,$ctime,$blksize,$blocks) = stat($cols{$i}{"col2"});
         $v = $select . qq| value="| . $cols{$i}{"col2"} . qq|" />|;
         if ( $mtime == $ctime ) { $v = "<span style='color: red;'>***</span>"; };
         print qq|<td>$v</td><td align="center"><a href="https://$server/websniff/$cols{$i}{"col2"}">$cols{$i}{"col2"}</a></td>
<td>| . (int($size2 / 1024 / 1000 )/1000) . qq| Gb</td>
</tr>\n|;
      }
  }

}

###############################
#   Check for 'kept' files in the 'root' directory
#

$kept =  glob("/root/keep/eth*");

if ( defined($kept) && length($kept) > 15 ) {
  my(%cols);
  print qq|
    <tr><td align="center" colspan="7"><hr></td></tr>
    <tr><td align="center" colspan="7"><strong>Archived Capture Files</strong></td></tr>
    <tr><td>&nbsp;</td><th align="center">eth1</th><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><th align="center">eth2</th><td>&nbsp;</tr>
|;

  chdir("/root/keep");

  @eth1s = glob("eth1*");

  $i=0;
  foreach $file (sort @eth1s) {
      $cols{$i}{"col1"} = $file;
      $i++;
  }
  $i=0;
  @eth2s = sort glob("eth2*");
  foreach $file (sort @eth2s) {
      $cols{$i}{"col2"} = $file;
      $i++;
  }

  foreach $i (sort(keys %cols)) {
      if (!defined($cols{$i}{"col1"}) || ( ! length($cols{$i}{"col1"}) ) ) {
         print qq|<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp</td><td>&nbsp</td>|;
      } else {
         ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size1,$atime,$mtime,$ctime,$blksize,$blocks) = stat($cols{$i}{"col1"});
         $v = $select . qq| value="| . $cols{$i}{"col1"} . qq|" />|;
         print qq|<tr>
<td>$v</td><td align="center"><a href="https://$server/keep/$cols{$i}{"col1"}">$cols{$i}{"col1"}</a></td>
<td>| . (int($size1 / 1024 / 1000 )/1000). qq| Gb</td>
<td>&nbsp;</td>
|;
      }
      
      if (!defined($cols{$i}{"col2"}) || ( ! length($cols{$i}{"col2"}) ) ) {
         print qq|<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp</td>|;
      } else {
         ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size2,$atime,$mtime,$ctime,$blksize,$blocks) = stat($cols{$i}{"col2"});
         $v = $select . qq| value="| . $cols{$i}{"col2"} . qq|" />|;
         print qq|<td>$v</td><td align="center"><a href="https://$server/keep/$cols{$i}{"col2"}">$cols{$i}{"col2"}</a></td>
<td>| . (int($size2 / 1024 / 1000 )/1000) . qq| Gb</td>
</tr>\n|;
      }

  }


}

print qq|</table>\n</form>\n|;

print qq|
  <hr>
  These files are the property of GCI and contain sensitive information. Do not distribute.
  <hr>
  <p><a href="/gci.net-CAcert.crt">GCI CA root certificate</a> and 
     <a href="/gci.net-SIGNcert.crt">GCI CA signing certificate</a> - Import both of these into your browser to stop SSL certificate warnings</p>
</body>
|;

}

sub do_status()
{
my($action) = @_;

print qq|<html>
<head>
  <title>$hostname - web sniffer status</title>\n|;

#if ( $action eq "stop" ) {
  print qq|  <meta HTTP-EQUIV="Refresh" CONTENT="15;https://$server/$myself" >
  <meta HTTP-EQUIV="Pragma" CONTENT="no-cache">
  <meta HTTP-EQUIV="Cache-Control" content="no-cache">\n|;
#}

print qq|</head>
<body>
  <h2>$hostname - web sniffer status</h2>
  This application is the property of GCI and contains sensitive information.
  <br><br>
|;

  if ($action =~ m/start/) {
    # starting
    print qq|You may experience a delay of up to a minute before the sniffer starts.<br>\n|;
  } elsif ($action =~ m/stop/) {
    # stopping
    print qq|The sniffer should be stopped within the next minute.<br>\n|;
  }

    print qq|This informational page will refresh every 15 seconds until redirected back to the main page.\n|;

  print qq|<hr>
</body>
|;

}


sub getcgivars {
    my($in, %in) ;
    my($name, $value) ;


    # First, read entire string of CGI vars into $in
    if ( ($ENV{'REQUEST_METHOD'} eq 'GET') ||
         ($ENV{'REQUEST_METHOD'} eq 'HEAD') ) {
        $in= $ENV{'QUERY_STRING'} ;

    } elsif ($ENV{'REQUEST_METHOD'} eq 'POST') {
        if ($ENV{'CONTENT_TYPE'}=~ m#^application/x-www-form-urlencoded$#i) {
            length($ENV{'CONTENT_LENGTH'})
                || &HTMLdie("No Content-Length sent with the POST request.") ;
            read(STDIN, $in, $ENV{'CONTENT_LENGTH'}) ;

        } else { 
            &HTMLdie("Unsupported Content-Type: $ENV{'CONTENT_TYPE'}") ;
        }

    } else {
        &HTMLdie("Script was called with unsupported REQUEST_METHOD.") ;
    }
    
    # Resolve and unencode name/value pairs into %in
    foreach (split(/[&;]/, $in)) {
        s/\+/ /g ;
        ($name, $value)= split('=', $_, 2) ;
        $name=~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge ;
        $value=~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge ;
        $in{$name}.= "\0" if defined($in{$name}) ;  # concatenate multiple vars
        $in{$name}.= $value ;
    }

    return %in ;

}

sub cgi_request()
{
   my($yesno);
   $yesno = 0;

   if (defined($ENV{'REQUEST_METHOD'})) {
#        print qq|<!-- REQUEST_METHOD="$ENV{'REQUEST_METHOD'}" -->\n|;
        $yesno++;
        if (length($ENV{'REQUEST_METHOD'}) > 1) {
#                print qq|<!-- length(REQUEST_METHOD)="| . length($ENV{'REQUEST_METHOD'}) . qq|" -->\n|;
                $yesno++;
        } else {
                $yesno--;
        }
   }

   if (defined($ENV{'REQUEST_METHOD'}) && $ENV{'REQUEST_METHOD'} eq "GET" ) {
     if (defined($ENV{'QUERY_STRING'})) {
#        print qq|<!-- QUERY_STRING="$ENV{'QUERY_STRING'}" -->\n|;
        $yesno++;
        if (length($ENV{'QUERY_STRING'}) > 1) {
#                print qq|<!-- length(QUERY_STRING)="| . length($ENV{'QUERY_STRING'}) . qq|" -->\n|;
                $yesno++;
        } else {
                $yesno--;
        }
     } else {
        $yesno--;
     }
   }

   if (defined($ENV{'REQUEST_METHOD'}) && $ENV{'REQUEST_METHOD'} eq "POST" ) {
     if (defined($ENV{'CONTENT_TYPE'})) {
#        print qq|<!-- CONTENT_TYPE="$ENV{'CONTENT_TYPE'}" -->\n|;
        $yesno++;
        if ($ENV{'CONTENT_LENGTH'} > 1) {
#                print qq|<!-- length(CONTENT_TYPE)="$ENV{'CONTENT_LENGTH'}" -->\n|;
                $yesno++;
        } else {
                $yesno--;
        }
     } else {
        $yesno--;
     }
   }
   return ($yesno>3?1:0);
}

sub HTMLdie {
    my($msg,$title)= @_ ;
    $title= "CGI Error" if $title eq '' ;
    print <<EOF ;
<html>
<head>
<title>$title</title>
</head>
<body>
<h1>$title</h1>
<h3>$msg</h3>
</body>
</html>
EOF

    exit ;
}

# end
