---
short_title: "Joins"
title: "Presto Joins"
---

In Presto, most joins are done by making a hash table of the right-hand table
(called the _build table_), and streaming the left-hand table (called the
_prop table_) through this map.  It joins those pairs of the left and right
tables that satisfy the join condition specified in the `ON` clause.

First we will look at inner joins, in which rows are joined by an _equijoin_
condition.  Equijoins are one or more equalities between columns in the left and
right table, like `ON customer.id = order.customer_id`.  The columns matched
act as a _join key_, which we'll use to distribute the join operation. We'll
then expand our discussion to various sorts of outer joins, and other join
conditions.

_NB: Many optimizations and implementation details are left out of this
discussion, to focus on the core principles._

Basic Joins
===========
Let's take a basic example.  Assume we have two tables,
`cities (city_name, country_iso2)` and `countries (country_name, iso2)`, and the
query

```sql
SELECT city_name, country_name
FROM cities
JOIN countries
ON cities.country_iso2 = countries.iso2
```

Conceptually, Presto will take `countries` and build a hash table
```
iso2 -> [ROW(country_name, iso2), ...]
```
mapping the join key to the list of right-hand rows with that key. Iterating
through `cities`, it will look up the country rows via the join key
`country_iso2`, yielding a combined row
`ROW(cities.city_name, cities.country_iso2, countries.country_name, countries.iso2)`.

To do this, _Presto keeps the build table in memory_.  This is why it's important
to _put the smaller table on the right_.

In the example above, the build table has only one row for the 'iso2' join key.
Multiple cities per country are in the stream, and each matches in turn.  If
there were more than one build table entry per 'iso2', each matching left-hand
row would iterate through the list of build rows for join key, yielding multiple
joined rows.  Hence this method can support One-to-One, Many-to-One,
One-to-Many, and Many-to-Many joins.

Broadcast Joins
===============
If your right table can fit in memory on one machine, you can do this one one
machine.  If the streaming table isn't too large, this will even finish
quickly.  However, if your streaming table has billions of rows, it would take
a long time, but can be easily sped up via parallelization.  If each worker
machine has a copy of the build table, then the input streaming rows can be
easily split across machines, each machine working independently.  This is
called a _broadcast join_, because the build table is "broadcasted" across the
workers.  If the build table is much smaller than the prop table, this is
extremely fast and efficient, but requires the build table to be able to
fit into memory.

**Insert cool diagram**

Partitioned Joins
=================
If the build table cannot fit onto a single machine, we need to split it across
the workers.  This requires us to make sure we stream the rows with a given
join key to workers that have the portion of the build table with that same join
key.  If we have `N` workers, we can do this by hashing the join key, and
putting the entry with `hash(join_key) % N == k` on worker `k`.  We direct the
streaming rows in the same fashion, which ensures the build table rows with a
given join key get matched with all streaming rows of the same key.

**Insert cool diagram**

Skew
====
In the example above, some countries likely have more cities than others.  So
even if the countries are evenly split amongst the workers, some workers will have
many more rows than others.  Since the query must wait until the slowest worker
is complete, this will take longer than if the cities were evenly distributed.
This phenomenon is termed _skew_.  Another cause of skew is if there is some
special value of the join key that has a vastly disproportionate number of
rows; like `null` for a nullable column.

Inner vs Outer Joins
====================
If a streaming row does not find a match with a join key, it can either be
dropped (Inner Join), put passed through with `null` fields instead of the
matching right-hand fields (Left Outer Join).

In the case of a Right or Full Outer Join, a set of all matched right rows is
kept by each worker; at the end unmatched right rows are yielded with `null`
fields instead of the left-hand fields.

This last method is not easy to do in the case of Right or Full Outer Joins.
Thus, specifying either of these will force a Partitioned Join.

Join Predicates and Push Downs
==============================
So far, we've only talked about equijoins, but any predicate can be placed in
the `ON` query.  There are, in general, three types of predicates:

* **Equijoin predicates**: Matching a column in the left table with a column in
  the right table, e.g. `table1.a = table2.b`.
* **Single-table predicates**: A condition that applies to only one of the two
  tables, e.g. `table1.c < 10`.
* **Complex predicates**: Any other condition, generally of the form
  `f(table1, table2)`.

Equijoins, if present, allow the hash table join we described above.
Single-table predicates are _pushed down_ and applied as a filter to the
individual tables before the join.  Complex predicates have to be applied as the
rows are being joined.

If the join is an inner join, Presto tries to further optimize by pushing down
applicable predicates in the `WHERE` clause.  For example, the following
statements are equivalent:

```sql
SELECT t1.e, t2.f
FROM t1 JOIN t2
WHERE t1.a = t2.b
  AND t1.c < 10
  AND t2.d = 'a'
```

and

```sql
SELECT t1.e, t2.f
FROM (
  SELECT a, e
  FROM t1
  WHERE c < 10
) t1
JOIN (
  SELECT b, f
  FROM t2
  WHERE d = 'a'
) t2
ON t1.a = t2.b
```

Since for outer joins a row that does not match any predicate is yielded (filled
with `null`s), _WHERE-clause predicate pushdown does not happen for outer joins_.

Cross Joins
===========
_Cross Joins_ join every row of the left table with every row of the right
table.  Because of this reason, they cannot use Partitioned Joins, and so must
be a Broadcast Join.  This can easily result in an Out Of Memory error if the
build table is large.  Instead of the hash-table lookup, the join is a
_Nested Loop Join_, in which the streaming table is iterated over, and each
streaming row loops over each build table row.  This quickly becomes inefficient
if the build table is large.

Since a cross join is a form of inner join, Presto pushes down predicates in the
`WHERE` clause.  If these include equijoins, it converts the join to a
(non-cross) inner join, and any single-table predicates will filter the joined
tables.

```sql
SELECT t1.a, t2.b
FROM t1, t2
WHERE t1.c = t2.d
  AND t2.e = 1
  AND t1.a < t2.b
```

is equivalent to

```sql
SELECT t1.a, t2.b
FROM t1
JOIN (
  SELECT b, d
  FROM t2
  WHERE t2.e = 1
) t2
ON t1.c = t2.d
WHERE t1.a < t2.b
```

Chained Joins
=============
A Chained Join is multiple joins in a row:

```sql
SELECT *
FROM table1
JOIN table2 ON table1.a = table2.a
JOIN table3 ON table1.a = table3.a
```

Presto will do the joins one at a time.  First `table1` with `table2`, then the
resultant table with `table3`, and so on.


[Presto Overview]: index "Presto Overview"
[Presto Map-Reduce]: presto-map-reduce "Presto Map-Reduce"
[Presto Joins]: presto-joins "Presto Joins"
[Presto Connectors]: presto-connectors "Presto Connectors"
