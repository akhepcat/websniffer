#!/usr/bin/perl

while (<>) {
   $line = $_;
## strip out unwanted spaces
   $line =~ s/  / /g;
   $line =~ s/^ //;
## separate the fields
   ( $pkt, $delta, $sip, $dummy, $dip, $dummy, $dummy, $dummy, $dummy, $dummy, $dummy, $ssrc, $dummy, $seq, $dummy, $time ) = split(/[ ,=]+/, $line);
## save the inter-packet arrival time in an array
   push(@deltas,$delta);
## and keep the final RTP sequence number
   $lastseq = $seq;
   }
## compare number of packets seen to sequence number for loss..
$pkts = @deltas - 1;
$loss = $lastseq - $pkts;

## get the mean inter-packet gap
foreach $delta ( @deltas ) {
   $dsum += $delta;
}
$dmean = $dsum / $pkts;

## and calculate the standard deviation for the whole set
## ( not sure if this is the right calculation )
foreach $delta ( @deltas ) {
   $dsquared += ( $delta - $dmean ) * ( $delta - $dmean );
}
$jitter = sqrt($dsquared / $pkts);

print "$sip $dip $pkts $loss $dmean $jitter\n";
