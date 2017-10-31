#!/usr/bin/perl
## translate the ascii-hex payload from tshark to actual binary data
while(<>) {
   $line = $_;
   chop $line;
   foreach $char ( split(/:/,$line)) {
       print chr(hex($char));
   }
}
