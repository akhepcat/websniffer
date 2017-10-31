######################## analyseCalls.sh ########################
#!/bin/bash
# tpcdump file as argument

## first, identify distinct RTP streams in input
count=1
size=$(stat --printf="%s" $1)
time_s=$(( size / 789590 ))
time_m=$(( time_s / 60 ))
time_h=$(( time_m / 60 ))
time_ls=$(( time_s % 60 ))
printf "Will take approximately %02d:%02d:%02d to process 1st pass\n" $time_h $time_m $time_ls
date

fields=$(tshark -r $1 "udp.port >= 45000" -d "udp.port == 45000-65535,rtp" -T fields -e "rtp.ssrc" 2>/dev/null | grep -v "^$" | sort | uniq | cut -f 1)
for ff in $fields; do
  total=$(echo $fields | wc -w)
  echo "processing $count of $total" 1>&2
  count=$((count + 1))

  ## count the number of 'quiet' packets - this is, ahem, 'heuristic'
  #NSB=$(tshark -r $1 -d "udp.port==9000,rtp" "rtp.ssrc==${ff}" -T pdml 2>/dev/null | grep payload | cut -f10 -d'"' | sed -e 's/[d5][54761032]://g; s/[^:]//g' | wc -c)
  NSB=$(tshark -r $1 -d "udp.port == 45000-65535,rtp" "rtp.ssrc==${ff}" -T pdml 2>/dev/null | grep payload | cut -f10 -d'"' | sed -e 's/[d5][54761032]://g; s/[^:]//g' | wc -c)

  NONSILENCE=$(echo "scale = 3; print $NSB / 160" | bc);
  ## suck out the audio payload
  tshark -r $1 -d "udp.port == 45000-65535,rtp" "rtp.ssrc==${ff}" -T pdml 2>/dev/null | grep payload | cut -f10 -d'"' | grabAudio.pl > ${ff}.raw
  ## convert it to WAV
  sox -c 1 -r 8000 -L -A -t raw ${ff}.raw ${ff}.wav
  ## Get a timestamp for the first packet
  TD=$(tshark -r $1 -d "udp.port == 45000-65535,rtp" "rtp.ssrc==$ff" -tad | head -n1 | cut -f2,3 -d" ")
  echo -n "$TD ${ff} $NONSILENCE "
  ## and do some call analysis
  tshark -r $1 -d "udp.port == 45000-65535,rtp" "rtp.ssrc==$ff" -td 2>/dev/null | qual.pl;
done | sort -n
