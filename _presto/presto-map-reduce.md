---
title:  "Presto Map-Reduce"
short_title:  "Map-Reduce"
order: 2
---

Viewed from afar, the query engine consumes one or more input streams of rows,
and produces a single output stream of rows.  In this note, we focus on the
basic case where there is one input stream that gets converted to the output
stream.  This is conceptually similar to the Map-Reduce paradigm, where rows get
filtered, transformed, exploded, or aggregated into new rows.  For performance,
Presto constructs these to be as parallelizable as possible.

_NB: Many optimizations and implementation details are left out of this
discussion, to focus on the core principles._

Mapping Operations
==================
Mapping operations take a single row, and produce 0, 1, or many rows. These are
very parallelizable -- since the operations takes only one row, you can simply
split the rows among different workers.

* **Filter**: A filter operation takes a predicate and applies it to each row.
  If the predicate returns true it yields the row, otherwise it yields nothing.
  These correspond to `WHERE` and `HAVING` clauses.

* **Projection**: A projection operation takes a map function and applies it to
  each row.  It yields the transformed row.  This can drop, rename, combine, or
  transform columns.  The column expression in the `SELECT` statement encodes
  the projection operation.

* **Unnest**: An unnest operation takes a row, and yields `N` rows.  In
  Presto, this is from a `CROSS JOIN UNNEST` statement that will expand an array
  or map into rows for each entry.

Given a sequence of mapping operations, Presto combines them into a _fragment_.
Multiple workers can perform this fragment, parallelizing the stream processing.

For example, let's consider the table `orders`:

```
| order_id  | all_item_quantities
+-----------+---------------------
| order_id1 | MAP(ARRAY[price1, price2, ...], ARRAY[quantity1, quantity2, ...])
+-----------+---------------------
| ...       | ...
```

and the query

```sql
SELECT order_id, item_quantity * item_price AS item_total
FROM orders
CROSS JOIN UNNEST(all_item_quantities) AS t (item_price, item_quantity)
WHERE item_quantity > 1
```

The incoming rows would be of the form `ROW(order_id, all_item_quantities)`.
Presto would first apply an unnest operator

```
r -> ROW(order_id=r.order_id, item_price=price1, item_quantity=quantity1),
     ROW(order_id=r.order_id, item_price=price2, item_quantity=quantity2),
     ...
```

The produced rows would be of the form `ROW(order_id, item_price, item_quantity)`.
Next, Presto will apply a filter operation with predicate

```
r -> r.item_quantity > 1
```

and then a map operation

```
r -> ROW(order_id=r.order_id, item_total=r.item_quantity * r.item_price)
```

These operators would all be composed into a single fragment.

Reducing Operations
===================
While mapping operations can be easily parallelized, reducing operations (like
`GROUP BY`) require more effort to make efficient.  Luckily, Presto does most of
this work.  This section will first describe the simple-but-inefficient method,
and then successive optimizations that Presto does for us.

If there is a `GROUP BY` clause, multiple rows (with the same group key) will be
aggregated into one.  In the simplest case, where there are no aggregation
functions (like `SUM()`, `COUNT()`, etc), the worker will just store the row in
memory, yielding only one instance.  This is equivalent to `SELECT DISTINCT`.

If there is an aggregation function, the worker must remember the current
aggregation data.  The amount of data stored depends on the function; for some
(like `SUM`) this is a single number, while for others (like `ARRAY_AGG`) it is
a field for each row aggregated over.

A non-efficient but correct model would be to partition the rows amongst workers
using the hash of the group key; this ensures a mostly equal distribution, which
all rows for a given key going to the same worker. This worker can then fully
aggregate, knowing it has seen all the relevant rows.  However, using
_partial aggregation_ we can do this much more efficiently.

Consider the following query:
```sql
SELECT user_id, SUM(order_amount) AS total_spent
FROM orders
GROUP BY user_id
```

Assume the first phase is split amongst two mapping workers `M1` and `M2`
(perhaps `orders` is actually a complex subquery), and there are two grouping
workers `G1` and `G2`, where `G1` will handle all odd `user_id`s and `G2` will
handle all even `user_id`s.  The inefficient way would be for each mapping
worker to send each row to either `G1` or `G2`, depending on the `user_id`.
However, `M1` and `M2` could locally store a hash table `{user_id:
partial_sum}`.  Then, once they have consumed all the rows, they can send these
partial sums to the appropriate grouping worker.  This is far less data than
sending the individual rows!  `G1` and `G2` can then do a simple sum of the
partial sums for each `user_id` they get.

Futhermore, the mapping workers don't have to wait until they have consumed all
rows; they can send partial sums whenever they are running low on memory! The
grouping workers will get a (relatively slow) stream of partial sums, which they
will aggregate to the final sums.

Often, a more complex function can be made partially aggregable with an
intermediate representation.  Consider the arithmetic mean operator `avg`.
Presto cannot simply average different slice of data and then average the
averages. Instead, Presto partially aggregates into a structure `{key:, sum:,
count:}`, and then aggregates the partial aggregations.  Any function that can
be represented in this way can be efficiently aggregated in parallel.

Intermediate Representation Example
===================================
Consider another example: `SELECT COUNT(DISTINCT x)`.  The naive method would be
to have a single node at the end, collecting all values of `x` into a set, then
evaluating the size of the set.  The first optimization is that the upstream
worker nodes could maintain their own partial set.  The final node would union
all these sets, returning the size as above.  Although parallelizable, the
storage requirements still scale as `O(num_outputs)`.

Presto implements `COUNT(DISTINCT X)` as
```sql
SELECT COUNT(*) FROM (
  SELECT x
  FROM t
  GROUP BY x
)
```
With this, Presto partitions the inner query across workers by hashing `x`.
Each worker stores the set of distinct `x` for a partition, counts it, then
passes the count to the final aggregator.  While the total storage is still
`O(num_outputs)`, it's distributed over many machines.

However, if a small approximation is acceptable, vastly more performant options
are available.  The function `approx_distinct` uses a fast, constant-space,
and parallelizable intermediate representation called
[HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog).
Each upstream worker node can accumate their intermediate representation, and
the final node can combine these to the final estimate.

Sorting Operations
==================
SQL also has the `ORDER BY` clause.  In the current implementation, a single
worker needs to hold all the rows in memory, which it then sorts.  This means
that `ORDER BY` on large datasets may lead to an out of memory error.



[Presto Overview]: index "Presto Overview"
[Presto Map-Reduce]: presto-map-reduce "Presto Map-Reduce"
[Presto Joins]: presto-joins "Presto Joins"
[Presto Connectors]: presto-connectors "Presto Connectors"
