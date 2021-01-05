+++
title = "Presto Overview"
weight = 0
date = 2018-05-01

[taxonomies]
tags = ["presto"]
categories = ["tech"]
+++

Presto is a fast SQL query engine, but it's different than most technologies
in its class. Understanding the philosophy and architecture of Presto allows
you to write more performant queries, and debug misbehaving ones. In these
articles, you'll learn about Presto's approach to map-reduce, joins, data
sources, and data flow. You'll understand why some join conditions are more
efficient than others, why the small table should be on the right, when to
use distributed joins, and how to structure your subqueries.

<!-- more -->

These articles are aimed at developers who use Presto, but want to understand
how the magic happens. _This is not an introductory tutorial_, nor is it
aimed at DBA-level optimization. The goal is to give a simplified but
reasonably accurate mental model of how things work under the hood. We avoid
details that would obfuscate the high-level understanding. Conversely, we
assume the reader has some experience working with Presto, or at least SQL.

This is part 1 of 5 of a series on Presto:
1. [Presto Overview]
2. [Presto Connectors]
3. [Presto Map-Reduce]
4. [Presto Joins]
5. [Presto Data-Flow]

Core Concept 1: SQL Query Engine, not Datastore
-----------------------------------------------
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
---------------------------------------
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



Acknowledgements
----------------
These articles would have been impossible without the help of Presto team members
Maria Basmanova ([![GitHubUser] mbasmanova](https://github.com/mbasmanova)),
Rebecca Schlussel ([![GitHubUser] rschlussel](https://github.com/rschlussel)), and
Andrii Rosa ([![GitHubUser] arhimondr](https://github.com/arhimondr)).

[Presto Overview]: @/presto-overview.md "Presto Overview"
[Presto Map-Reduce]: @/presto-map-reduce.md "Presto Map-Reduce"
[Presto Joins]: @/presto-joins.md "Presto Joins"
[Presto Connectors]: @/presto-connectors.md "Presto Connectors"
[Presto Data-Flow]: @/presto-data-flow.md "Presto Data Flow"
[GitHubUser]: /GitHub-Mark-64px.png