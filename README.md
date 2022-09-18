# axfr-tools

This toolkit is aimed at those who want to see or gather historical records for a given domain.  The concept behind it is that if a zonefile from 2010 exists; even if that organization subsequently updates their Nameserver to prevent Zonefile Transfers in 2015, odds are the organization will not change those pre-existing records.  This can be very useful for someone such as a Pentester tasked with testing various facets of the domain.  It can save precious time with regards to footprinting.

### The database consists of 5 tables:
1. axfr
  - dm (Domain the record was pulled for)
  - own (Ownership record)
  - ttl (Time to Live)
  - rr (Resource Record Type)
  - data (The data)

2. dm2ns
  - dm (axfr'd Domain)
  - ns (Nameserver the domain used, that allowed an axfr)

3. domains
  - dm (Domain that allowed for an axfr)

4. nameservers
  - ns (Nameserver that allowed an axfr for >= 1 Domain)

5. scanned
  - dm (Domain that has been scanned for axfr)

###### As an example dataset, the  <a href="https://scans.io/study/hanno-axfr">Hanno Böck</a> dump has been ported to axfr-tools and made available for usage as <b>MASTER.sqlite</b>.  Due to the file size limitations on github.com, this file may be downloaded from <a href="http://ethicalreporting.org/axfr-tools/MASTER.sqlite.gz">here</a>.

The port was made possible via the following:
```bash
## Grab the dump
wget https://scans.io/data/hanno/axfr-scan-20150417.tar.xz

## Decompress
xz -d axfr-scan-20150417.tar.xz

## De-tar
tar xf axfr-scan-20150417.tar

## Jump into
cd axfr

## Rip the files to a directory based on the domain
for i in *; do dest=$(grep 'DiG 9.9.5-3ubuntu0.2-Ubuntu' "$i" | awk '{print $9}'); mkdir -p "$dest"; mv "$i" "$dest"; done

## Rename files in the directory based on the nameserver for each file
for i in *; do cd "$i"; for x in *; do dest=$(grep 'DiG 9.9.5-3ubuntu0.2-Ubuntu' "$x" | awk '{print $10}' | cut -d\@ -f2 | sed 's/\.$//'); mv "$x" "$dest"; done; cd ..; done

## Jump out and rename
cd ..
mv axfr DIG_INFOs

## Make Tgt list
ls DIG_INFOs > nTgts.lst

## Run axfr -b
./axfr -b

## Rename and compress
mv zones.sqlite MASTER.sqlite && gzip -9 MASTER.sqlite

## Hash it
md5sum MASTER.sqlite.gz > MASTER.sqlite.gz.md5sum

```

<br></br>
##### That's nice...  What can I do with it?
Run some queries of course!

- "Give me a list of the number of rows for a given domain in the axfr table"
  - ./axfr -q domainCount

- "Give me a list of the number of domains a given nameserver returned results for"
  - ./axfr -q nameserverCount

- "Create me a directory, containing the zonefiles for domains from a given nameserver"
  - ./axfr -q nameserverDump

<br></br>
##### How do I build my own, or add on to your example dataset?
dig-em is a bash script that performs the "brute" work of obtaining the zonefiles for various domains.  dig-em has a lot of functions in it, and as time goes forward, they will all be ported over to axfr itself.  For the purposes of this README, we're only going to concern ourselves with <b>dig-em -h</b> and <b>dig-em -f</b>, and how to use them for axfr.

- dig-em -h
  - Perform a zonefile transfer attempt against a single domain
  - If successful, the results will be placed in a folder, in the directory in which the command was run, entitled the name of the domain targeted
  - To add these results to the DB, create a directory called DIG_INFOs and place this folder in it.

- dig-em -f
  - Perform a zonefile transfer attempt against a list of domains
  - If successful, the results will be placed in a folder called DIG_INFOs
  - As dig-em progresses along, for "dead domains" that resolve to nothing, a file called NoNS.lst is created
    - NoNS.lst is important to axfr and must be removed from DIG_INFOs prior to use

<br></br>
##### After running dig-em and obtaining the desired zonefiles, you will be left with the folder DIG_INFOs and the possibility of a file, NoNS.lst.  If you don't have NoNS.lst, disregard these next few steps

- NoNS.lst steps
  - NoNS.lst consists of domains that should be removed from the target list provided to axfr -b
  - This step has been automated via: axfr -c
  - axfr -c has many uses and this is not the "main usage" for it, but it comes in handy via the following:
    - Assume the file you fed <b>dig-em -f</b> was called domains.lst
    - Before running <b>axfr -b</b> to addon or build the initial DB, we want to remove nonsense.
    - A domain that doesn't resolve, is, nonsense.
    - ./axfr -c
      - List of domains previously scanned?
        - NoNS.lst
      - List of domains to scan?
        - domains.lst
      - Output File? [nTgts.lst]
        - The default is fine, and <b>axfr -b</b> will "expect" it to be named as such
Now you should have a file called nTgts.lst.  If your file you fed dig-em differs from this, simply rename that file as such.  

<br></br>
##### Time for building or adding to the DB.

With any proper methodology, a test run should always be done first.  Make a quick copy of your DB if you plan to add to it.  Since I included the link for MASTER.sqlite, let us assume you will add to that DB.

Place the copy of MASTER.sqlite folder in the same / directory as DIG_INFOs.  Do: <b>./axfr -b</b>.  Follow along with the prompts.  If you were lucky, and got 100% clean zonefiles, it will let you know, if not, it will let you know.  I'll update this readme with how to handle bad imports a little bit later on.  Assuming you received 100% clean, then simply delete that test run, and point <b>axfr -b</b> at the real MASTER.sqlite.

Enjoy!
