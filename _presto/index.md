---
title:  "Second Look: Presto"
short_title:  "Second Look: Presto"
order: 0
---

Presto is a popular and highly performant SQL query engine that connects to a
variety of datastores.  While it works well out of the box, understanding it
more deeply can pay dividends when optimizing queries or debugging problems.
These articles are aimed at developers who use Presto, but want to understand
how the magic happens.

_This is not an introductory tutorial_, nor is it aimed at DBA-level
optimization.  The goal is to give a simplified but reasonably accurate mental
model of how things work under the hood.  We avoid details that would obfuscate
the high-level understanding.  Conversely, we assume the reader has some
experience working with Presto.

Core Concept 1: SQL Query Engine, not Datastore
===============================================
Presto, at its heart, has no concept of disks or where data is stored.  It
delegates that to _connectors_, which read data from (and write to) popular
datastores such as MySQL, Hive, etc.  The connectors stream rows into Presto,
which process them, streaming the results out to clients or other connectors.
This has the important effects:

1. All datasources are equivalent to Presto, and you can write _federated
   queries_ which combine multiple databases and even datastores.

2. Presto has no native concept of indices, primary keys, partitions, or other
   things that make storage and access more efficient.  Logic for these must
   reside in the connector.


Core Concept 2: In-memory and streaming
=======================================
Presto is blazingly fast compared to Hive, Pig, etc, because it does not perform
any disk IO while processing a query.  It streams data, transforming each row,
and passing data to other machines via sockets.

This has several important consequences:
1. Since there is no disk IO, Presto is _fast_.

2. Since it cannot store data to disk, Presto is _memory limited_.

3. Presto only reads enough data to fill the pipeline; if one step stops,
   everything upstream stops too.

4. Since it streams data, it cannot inspect data for optimization.  Each stage
   sees each row only once.


Articles
========
In the following articles, we explore a different section of Presto
architecture.
1. [Presto Connectors]
2. [Presto Map-Reduce]
3. [Presto Joins]
4. [Presto Data Flow]

Acknowledgements
================
These articles would have been impossible without the help of Presto team members
Maria Basmanova ([@mbasmanova](https://github.com/mbasmanova)),
Rebecca Schlussel ([@rschlussel](https://github.com/rschlussel)), and
Andrii Rosa ([@arhimondr](https://github.com/arhimondr)).

[Presto Overview]: index "Presto Overview"
[Presto Map-Reduce]: presto-map-reduce "Presto Map-Reduce"
[Presto Joins]: presto-joins "Presto Joins"
[Presto Connectors]: presto-connectors "Presto Connectors"
[Presto Data Flow]: presto-data-flow "Presto Data Flow"
