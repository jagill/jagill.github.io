---
short_title:  "Data Flow"
title:  "Presto Data Flow"
---

When a client submits a query to Presto, it connects to a _coordinator_ which
parses the query, plans the computation, and coordinates the flow of data from
the connectors to the workers and between workers.  The client can then
periodically call back to the coordinator, to retrieve status information and
any results that have been finished.

The coordinator acts as the brains of the operation.  It will parse the query,
plan the operations, construct the computation DAG, and requisition workers. It
will feed the input data from the connector into the upstream workers, retrieve
results from the downstream workers, and give status information and results to
the client.

Workers pull data from upstream workers, perform their computation, and give
data to the downstream workers.  Workers will pause working if their output
buffer is not being consumed.  Workers are grouped into _stages_; workers in
one stage pull data from workers in the upstream stage, but don't talk to other
workers in their stage.

Client
======
The client only talks to the coordinator, via HTTP POST requests.  The client
initiates the operation by submitting the query text. The response (in JSON)
contains a query handle, which the client uses in subsequent requests to check
the status or download partial results. When the client downloads results, the
coordinator will flush them from memory, freeing up buffer space for more
results.

In fact, if the client does not retrieve results before the coordinator's buffer
is filled, the coordinator will stop retrieving results from the final stage
workers, and all of the upstream processes will pause once their buffers are
filled. Thus it is critical that the client performs timely retrieval of the
results. The client receives results in pages (approximately 1MB each), and can
request up to 16 pages in one request.

If the submitted query is an `INSERT` (or other non-`SELECT`) statement, the
results are just an acknowledgement, and the operation won't block waiting for
the client.

Coordinator
===========
When the coordinator receives the query text (called the _statement_) from the
client, it parses it into the _query_.  The query determines _stages_ that can
be done without transferring data between workers, for example mapping
operations followed by a partial aggregation (see [Presto Map-Reduce]). The
coordinator requisitions workers for each stage and sets up _exchanges_ of data
between them.

The coordinator gets an estimate of how many splits of data there are from the
connector, monitors the capacity of the workers of the initial stage, and feeds
splits to any worker that has capacity.  It also monitors workers of the final
stage, grabbing completed results and storing them for the client to retrieve.

Workers
=======
Workers act as nodes in a computation DAG.  They pull data from upstream
workers, process it, and store the results in an output buffer for downstream
workers to fetch.  If there is room in the output buffer, they repeat this
process.  If the output buffer is full (because the downstream workers aren't
pulling), the worker pauses computation until the buffer has room again.

Data is exchanged in _pages_, which default to 1 MB.  Workers open long-lived
HTTP POST connections with their upstreams to fetch pages.  Once a page is
pulled, the upstream worker can delete it from its output buffer.  Presto has a
configurable max page size which defaults to 16 MB; as there must be at least
one row per page, this means the max row size is equal to the max page size.

Query Planning
==============
When the coordinator parses the query, it creates a tree of _operators_, like
`Filter` or `InnerJoin`.  Presto combines sequential operators that can
run on one worker into a _stage_. Between stages, data is _exchanged_; the
exchange may distribute data to any worker with capacity
(_round robin exchange_), or to a particular worker based on the hash of a key
(_repartitioned exchange_).

A given stage will have one or more _pipelines_, which are local sequences of
operators.  For example, a stage with only mapping and filtering operators will
have a single pipeline that combines those operators.  But a `JOIN` stage may
have three pipelines: one to read in the build table and build a hashmap, one to
read the left table, and one to stream the left table through the hashmap and
produce the output.  Between pipelines of a given stage are _local exchanges_,
which are analogous to the exchanges between stages.

Each stage is parallelized over multiple workers; the "instance" of the stage on
a worker is called a _task_.  For example, if there were `N` workers in a `JOIN`
stage, the `k`th worker would be responsible for all rows such that
`hash(join_key) % N == k`. On a given worker, each pipeline is parallelized into
_drivers_, which divide up the work for the pipeline.  A driver for a pipeline
of mapping operations might just grab any available data, but a driver that is
streaming a left table through a hashmap would futher split the hash table and
streaming rows by hashing.  Thus, the Pipeline/Process/Driver parallelization is
analogous to that of the Stage/Worker/Task.

[Presto Map-Reduce]: presto-map-reduce "Presto Map-Reduce"
