# axfr-tools

This toolkit is aimed at those who want to see or gather historical records for a given domain.  The concept behind it is that if a zonefile from 2010 exists; even if that organization subsequently updates their Nameserver to prevent Zonefile Transfers in 2015, odds are the organization will not change those pre-existing records.  This can be very useful for someone such as a Pentester tasked with testing various facets of the domain.  It can save precious time with regards to footprinting.

## The database consists of the following tables
`axfr`

| column | description |
| --- | --- |
| dm | Domain the record was pulled for |
| rec | Resource record |
| ttl | Time to Live |
| rt | Resource Record Type |
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
| err | Exception |
| dsc | Description of the exception |

`nameservers`

| column | description |
| --- | --- |
| ns | Nameserver that performed an axfr |

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

## Statistical queries
```
SELECT COUNT(*) FROM axfr;
SELECT COUNT(*) FROM scanned;
SELECT COUNT(*) FROM domains;
SELECT COUNT(*) FROM dm2ns;
SELECT COUNT(*) FROM nameservers;
```

## Gleaning info about internal DNS
```
CREATE TABLE internal_dns AS SELECT * FROM axfr WHERE rr = 'A' AND ( DATA LIKE '10.%' OR DATA LIKE '172.16.%' OR DATA LIKE '172.17.%' OR DATA LIKE '172.18.%' OR DATA LIKE '172.19.%' OR DATA LIKE '172.20.%' OR DATA LIKE '172.21.%' OR DATA LIKE '172.22.%' OR DATA LIKE '172.23.%' OR DATA LIKE '172.24.%' OR DATA LIKE '172.25.%' OR DATA LIKE '172.26.%' OR DATA LIKE '172.27.%' OR DATA LIKE '172.28.%' OR DATA LIKE '172.29.%' OR DATA LIKE '172.30.%' OR DATA LIKE '172.31.%' OR DATA LIKE '172.32.%' OR DATA LIKE '192.168.%');

CREATE TABLE exposed_dms AS SELECT * FROM axfr WHERE dm IN (SELECT DISTINCT(dm) FROM internal_dns);

CREATE TABLE vuln_dms AS SELECT DISTINCT(DM) FROM internal_dns ORDER BY 1 ASC;

CREATE TABLE exposed_dm_qty AS SELECT COUNT(*), dm FROM exposed_dms GROUP BY dm ORDER BY 1 DESC;
```

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

## Growing the dataset
To combine collected zones overtime the merger module was created.  Simply call `axfr -m` with the names of two databases you wish to combine into one.  As the output is hardcoded `example.sqlite3` is the created combination and as such must not be an input file.  Assuming you have foo.sqlite3 and bar.sqlite3 as your inputs do:
```
axfr -m foo.sqlite3 bar.sqlite3
```
example.sqlite3 is created and will retain the data from both foo and bar using a UNION approach so as to cut down on duplications.

## Recommended system settings
The following settings are recommended for the best possible success for retrieving zonefiles.

/etc/security/limits.conf
```
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
* soft stack 65536
* hard stack 65536
```

/etc/sysctl.conf
```
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.core.somaxconn = 4096
net.core.netdev_max_backlog = 4096
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_syncookies = 1
net.core.rmem_default = 524288
net.core.rmem_max = 16777216
net.core.wmem_default = 524288
net.core.wmem_max = 16777216
```

## Tips for success
Testing using the recommended system settings has shown that up to 20 threads can be run across one processor with an average of 8GB system RAM.  This means that on a system with 4 processors you can run 4 instances of axfr with each running up to 20 threads and have a high liklihood that no domains will be missed due to bottlenecks.  Results of course may vary and users are encouraged to provide their feedback in the form of raising an Issue or creating a PR.