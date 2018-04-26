---
short_title:  "Data Flow"
title:  "Presto Data Flow"
---

WIP
----

When a client submits a query to Presto, it actually connects to a _coordinator_
which parses the query, plans the computation, and coordinates the flow of
data from the connectors to the workers, and between workers.  The client can
then periodically call back to the coordinator, to retrieve status information
and any results that have been finished.

Client
======
The client only talks to the coordinator, via HTTP POST requests.  The client
initiates the operation with the query text. The response (in JSON) contains a
query handle, which the client uses in subsequent requests to check the status
or download partial results. When the client downloads results, the coordinator
will flush them from memory, freeing up buffer space for more results.

In fact, if the client does not retrieve results before the coordinator's buffer
is filled, all of the upstream processes will pause once their buffers are
filled. Thus it is critical that the client performs timely retrieval of the
results. The client receives results in pages (approximately 1MB each), and can
request up to 16 pages in one request.

If the submitted query is an `INSERT` (or other non-`SELECT`) statement, the
results are just an acknowledgement, and the operation won't block waiting for
the client.

Coordinator
===========
The coordinator acts as the brains of the operation.


Workers
=======

Connectors and Slices
=====================

Fragments and Shuffles
======================

Pushing Down Predicates
=======================
