# websniffer

This is a very basic web-based control for a websniffer.  It supports up to two capturing interfaces.
Captures are done in a ring, so that files never exceed a max size, and are sized so as to not
quite fill up the entire drive.  Other than that, it'll capture and rotate in perpetuity.

This is currently used for capturing mgcp/sip voice streams, but you can adapt it fairly easily.  

Lots could be done to clean this up, but i'll leave that to you, dear visitor.  

* bin/do-action		- this is the main applet.  it should be called every minute by cron  

* bin/archive		- called by do-action, this moves capture files out of the ring into permanent storage  
* bin/squeezeme		- called by do-action, this compresses archived capture files  

* bin/sipcapper		- a script that's used to set the capture filter based on customer name  
* bin/slr-cap		- called by do-action, this script performs the actual capture, based on the ACL provided by sipcapper  

* cgi/rtpanalysis.cgi	- a CGI inteface into voice analysis of captured data  
* cgi/websniff.cgi	- the CGI interface for controlling the packet capture and data file management  


These files were not created by me, and I have lost the attribution for them.  
Please contact me if they're yours!  

* bin/analyseCalls.sh	- this is a manual method of parsing captured files for voice quality issues, and calls the following two scripts:  
 -- bin/qual.pl  
 -- bin/grabAudio.pl  

