---
layout: home
title:  "Journeyman Guides: Some technical explorations"
---

These guides are writings meant for the
"[Journeyman](https://en.wikipedia.org/wiki/Journeyman)" audience: people who
know how and why to use a tool, but want a deeper understanding about a
particular aspect.  Developing a mental model of how a tool works (even
simplified!) allows one to reason through novel scenarios and find more
effective and efficient solutions. In these articles, I'll explore aspects of
some tools I use, building up these types of mental models.

Git is a powerful version control system, but the mental model can be complex
(what is a fast-forward merge?  What does `git reset --soft` do anyway?).  In
the [Git articles](/git), you try out these tools on simple repos, seeing
explicitly what happens at the commit level.  You'll understand why "detacted
head" mode isn't a problem, and how to set up your own remote repos.

Presto is a fast SQL query engine, but it's different than most technologies in
its class.  Understanding the philosophy and architecture of Presto allows you
to write more performant queries, and debug misbehaving ones.  In the
[Presto articles](/presto), you'll learn about Presto's approach to map-reduce,
joins, data sources, and data flow.  You'll understand why some join conditions
are more efficient than others, why the small table should be on the right,
when to use distributed joins, and how to structure your subqueries.
