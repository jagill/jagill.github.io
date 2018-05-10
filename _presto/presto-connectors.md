---
title:  "Presto Connectors"
short_title:  "Connectors"
order: 1
---

Presto is a SQL query engine, one that ultimately understands how to consume one
or more input streams of rows and produce an output stream of rows.  At its
core, it doesn't understand things like datastores, disk IO, primary keys, and
partitions.  To be practically useful, it needs to be able to connect to
datastores, which it does via _connectors_.  A connector is specific to a
particular datastore (say, MySQL, Hive, Cassandra, etc), and is what understands
concepts such as disk IO, partitions, etc.

Presto Storage Model
====================
While Presto doesn't know about datastores, it has a set of abstractions that it
expects a connector to respect.

* **Row**: A row is a named tuple, and is the basic unit of data.
* **Split**: A split is one or more rows, yielded as a unit for performance.  A
  table will contain one or more splits.
* **Table**: A table is the basic storage concept in Presto.  They consist of
  a number of (unordered) rows grouped into one or more splits.  They are
  familar concepts in SQL databases and Hive, although they can be applied to
  CSV files or anything else that can generate rows.
* **Schema**: Collections of tables are grouped into schemas.  A schema is
  equivalent to a database in the SQL or Hive world, but it could also be a
  directory of CSV files.  Anything that can be a logical collection of
  tables can be a schema.
* **Catalog**: A catalog is a collection of schemas.  A database cluster is
  an example.  Each catalog has one connector, so the schemas must be of the
  same datastore type.

A warehouse that had both MySQL and Hive clusters would need (at minimum) two
catalogs, one for MySQL and one for Hive.  While each catalog has one connector,
it's possible that two catalogs can use the same connector type to access the
same datastore type. Consider the case where there are separate clusters for
user-facing MySQL databases and warehouse MySQL databases.  You could make two
catalogs, `user-mysql` and `warehouse-mysql`, each of which uses the MySQL
connector, initialized with different parameters.

A fully-qualified table name is of the form `{catalog}.{schema}.{table}`, like
`hive.warehouse.dim_orders` or `mysql.user_data.addresses`.  A given Presto
session can set default catalogs and schemas, allowing just the table name to be
used.

Connectors
==========
When Presto wants data from a table, it looks up the connector specified for the
catalog.  The connector is specific to a given datasource, for example the MySQL
connector or the Hive connector.

A table is grouped into data chunks called _splits_.  Presto queries the
connector, which reports how many splits are available.  This is used to plan
the query and determine parallelization.  The connector reads the table, sending
the splits to the appropriate workers to be processed.

Delegating Predicates
=======================
The most naive connector would read the entire table, yielding all splits.
However, if the query has filter predicates like `WHERE country = 'DE'`, Presto
can _delegate_ the predicate to the connector.  The connector can filter these
rows before sending them to the workers, reducing unneeded network IO and
computation.  Futhermore, if the connector has understanding of things such as
primary keys, indices, partitions, etc, it can use the optimizations build into
the datastore to be even more efficient.

One effect of this is that two conditions that might be logically equivalent may
be result in dramatically different performance.  If the predicate is of a form
that is understood by the connector, it can do the work before Presto ever sees
the unwanted rows.

Presto pushes down all the viable predicates (generally just equalities) to the
connector.  The connector's use of them is best effort; it must return a
superset of the results that would pass the where clause, but it may return any
superset. Thus, Presto will apply the predicates again to all rows it receives.

Federated Queries
=================
A very important consequence of the connector model is that Presto treats all
rows equally, for any datasource.  In particular, this means that a single query
can get rows from different databases, or even different data sources (MySQL and
Hive, for example).

**INSERT EXAMPLE**

Writing output
==============
Commonly, the results of a query are inserted into another table with an
`INSERT INTO` statement.  Presto will stream its output rows into the output
connector, which is responsible for writing the data in a format appropriate to
the datastore.  Similar to the comment on federated queries above, the output
connector can be from a different catalog (and thus different data source) than
the input connector(s).  This makes Presto a very efficient way to scrape or
replicate tables between different data sources.


[Presto Overview]: index "Presto Overview"
[Presto Map-Reduce]: presto-map-reduce "Presto Map-Reduce"
[Presto Joins]: presto-joins "Presto Joins"
[Presto Connectors]: presto-connectors "Presto Connectors"
