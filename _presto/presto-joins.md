---
short_title: "Joins"
title: "Presto Joins"
---

In Presto, joins are done by making a hash table of the right-hand table (called
the _build table_), and streaming the left-hand table through this map.  It
joins those pairs of the left and right tables that satisfy the join condition
specified in the `ON` clause.

First we will look at inner joins, in which rows are joined by a condition
(like `ON customer.id = order.customer_id`), which contains a _join key_.
We'll then expand our discussion to various sorts of outer joins, and other
join conditions.

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
`iso2 -> ROW(country_name, iso2)`.
Iterating through `cities`, it will look up the country row via the join key
`country_iso2`, yielding a combined row
`ROW(cities.city_name, cities.country_iso2, countries.country_name, countryies.iso2)`.

To do this, _Presto keeps the build table in memory_.  This is why it's important
to _put the smaller table on the right_.

The above handles the case of One-to-One joins or Many-to-One joins (where the
left table has the "many").  Next consider the case where the right
table has `N > 1` rows for a key (One-to-Many and Many-to-Many joins).  Each
streaming row with this key match each right-side row, and "unnests" into
`N` rows.  Conceptually, the hash table can store a list of rows, which are
iterated over.

Broadcast Joins
===============
If your right table can fit in memory on one machine, you can do this one one
machine.  If the streaming table isn't too large, this will even finish
quickly.  However, if your streaming table has billions of rows, it would take
a long time, but can be easily sped up via parallelization.  If each worker
machine has a copy of the hash table, then the input streaming rows can be
easily split across machines, each machine working independently.  This is
called a _broadcast join_, because the hash table is "broadcasted" across the
workers.  This is extremely fast and efficient, but requires the right-hand
table to be able to fit into memory.

**Insert cool diagram**

Hash Joins
==========
If the build table cannot fit onto a single machine, we need to split it across
the workers.  This requires us to make sure we stream the rows with a given
join key to workers that have the portion of the build table with that same join
key.  If we have N workers, we can do this by hashing the join key, and putting
the entry with `hash(join_key) % N == k` on worker `k`.  We direct the
streaming rows in the same fashion, which ensures that streaming rows with a
given join key go to machines that have the build table entries with the same
keys.

**Insert cool diagram**

Skew
====
In the example above, some countries likely have more cities than others.  So
even if the countries are evenly split amongst the workers, some workers will have
many more rows than others.  Since the query must wait until the slowest worker
is complete, this will take longer than if the cities were evenly distributed.
This phenomenon is termed _skew_.  Another cause of skew is if there is some
special value of the join key that has a vastly disproportionate number of
rows; like `null` for a nullable column.  In the case of aggregations (see
[Presto map-reduce]), it's possible skew will cause certain worker nodes to run
out of memory, as they have to remember far more rows than their compatriots.

Inner vs Outer Joins
====================
If a streaming row does not find a match with a join key, it can either be
dropped (Inner Join), put passed through with `null` fields instead of the matching
right-hand fields (Left Outer Join).

In the case of a Right or Full Outer Join, a set of all matched right rows
is kept by each worker; at the end unmatched right rows are yielded with
`null` fields instead of the left-hand fields.

This last method is not easy to do in the case of Right or Full Outer Joins.
Thus, specifying either of these will force a Hash Join.

Equijoins and other conditions
==============================
So far, we've only talked about `JOIN` conditions of the form `table1.a = table2.b`,
which are called _equijoins_.  However, any predicate can be placed in the `ON`
query.  If the predicate only involves one table (like `table1.c < 10`), it gets
applied to that table as a filter before the equijoin is applied.  More general
predicates are checked against each potential left-right joined row (that
matches the equijoins); if the joined row does not satisfy the predicate, it's
viewed as a non-match.  For inner joins, that row is dropped; for outer joins,
it's treated as discussed in the previous section.

Cross Joins and Predicate Push Down
===================================
_Cross Joins_ join every row of the left table with every row of the right
table.  Because of this reason, they cannot be partitioned via a Hash Join, and
so must be a Broadcast Join.  This can easily result in an Out Of Memory error
if the build table is large. However, Presto will push down predicates in a
succeeding `WHERE` statement into the join.  Equijoin conditions will convert it
into an inner join.  Predicates on a single table are pushed down to filter
the table before joining.  Other conditions are applied after the join.
For example,

```sql
SELECT t1.a, t2.b
FROM t1, t2
WHERE t1.c = t2.d
  AND t2.e = 1
  AND SOME_FUNCTION(t1, t2)
```

is equivalent to

```sql
SELECT t1.a, t.b
FROM t1
JOIN (
  SELECT b, d
  FROM t2
  WHERE t2.e = 1
) t
ON t1.c = t.d
WHERE SOME_FUNCTION(t1, t)
```


[Presto Overview]: index "Presto Overview"
[Presto Map-Reduce]: presto-map-reduce "Presto Map-Reduce"
[Presto Joins]: presto-joins "Presto Joins"
[Presto Connectors]: presto-connectors "Presto Connectors"
