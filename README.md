# axfr-tools

This toolkit is aimed at those who want to see or gather historical records for a given domain.  The concept behind it is that if a zonefile from 2010 exists; even if that organization subsequently updates their Nameserver to prevent Zonefile Transfers in 2015, odds are the organization will not change those pre-existing records.  This can be very useful for someone such as a Pentester tasked with testing various facets of the domain.  It can save precious time with regards to footprinting.

### The database consists of the following tables:
`axfr`

| column | description |
| --- | --- |
| dm | Domain the record was pulled for |
| own | Ownership record |
| ttl | Time to Live |
| rr | Resource Record Type |
| data | The data |

`dm2ns`

| column | description |
| --- | --- |
| dm | axfr'd Domain |
| ns | Nameserver the domain used, that allowed an axfr |

`domains`

| column | description |
| --- | --- |
| dm | Domain that allowed for an axfr |

`issues`

| column | description |
| --- | --- |
| dm | Domain with an issue |
| ns | NS with an issue |
| err | Description of the issue |

`nameservers`

| column | description |
| --- | --- |
| ns | Nameserver that allowed an axfr for >= 1 Domain |

`scanned`

| column | description |
| --- | --- |
| dm | Domain that has been scanned for axfr |

## Obtaining zonefiles

- `axfr -d example.com`
  - Perform a zonefile transfer attempt against a single domain
  - If successful, the results will be placed in example.sqlite3

- `axfr -f example.txt 2`
  - Perform a zonefile transfer attempt against a list of domains using 2 threads
  - If successful, the results will be placed in example.sqlite3

## Useful queries
- "Give me a list of the number of rows for a given domain in the axfr table"
  - `./axfr -q domainCount`

- "Give me a list of the number of domains a given nameserver returned results for"
  - `./axfr -q nameserverCount`

- "Create me a directory, containing the zonefiles for domains from a given nameserver"
  - `./axfr -q nameserverDump`


## Comparing scans and creating a new target list called nTgts.lst
Why scan the same domain twice?
```
sqlite3 ./example.sqlite3 "SELECT * FROM scanned;" > scanned.lst
./axfr -c
  - List of domains previously scanned?
    - scanned.lst
  - List of domains to scan?
    - domains.lst
  - Output File? [nTgts.lst]
    - <hit enter or type something else to change the filename>
```