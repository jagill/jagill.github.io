+++
title = "Git Reset"
weight = 2
date = 2017-03-02

[taxonomies]
tags = ["git"]
categories = ["tech"]
+++

An important part of version control is the ability to go back to previous 
states -- particularly if your recent changes messed something up!  Git
has the powerful `reset` command, but it has a bewildering array of
slightly-but-crucially-different modes.  People generally start out memorizing
a couple `reset` commands for common tasks, but still have questions like
"what does `git reset --soft` do anyway?".  In this article, we'll build up
a mental model of how Git views changes, which will allow us to unlock the full
power of `reset`.

<!-- more -->

`git-reset` has several options, and using it effectively requires
understanding some fundamental concepts in git: HEAD, the index, and the
working tree. Underlying all of these is the familiar concept of the
filetree; this is just the files and directories under the root of the git
repo.

## The four stages of commitment

An important conceptual model to have in our mind is the four stages changes go
through in the `git commit` process.  We'll find that the the various options
of `git reset` differ primarily in how they move around these four stages of
commitment.  These are the file tree, the working tree, the index, and HEAD.

* The file tree is just the changes that are on disk; this is the familiar
  non-git concept.
* The working tree is those changes to the file tree that git knows about.  Any
  changes to the file tree in a file that is tracked by git are automatically
  known, and thus on the working tree.
* The index is those changes that are staged to be included in the next commit.
  Changes are generally moved from the working tree to the index by `git add`.
* HEAD is the commit you are currently on.

We'll give examples for those four in a second, but let's talk about `git diff`
and `git status`.  When you use `git diff`, it shows the differences between
the index and the working tree.  Thus it does not show staged changes.  Using
`git diff --staged` (alias: `git diff --cached`) shows the differences between
HEAD and the index.

The command `git status` will show you what files have
changes in the index (staged changes, under "Changes to be committed:"),
changes in the working tree but not in the index (unstaged cahnges, under
"Changes not staged for commit:"), and files that are not known to git
(under "Untracked files:").  Note that it's quite possible for a given file
to have both staged and unstaged changes (see below).

In this tutorial when we use `git status` or `git diff`, we abbreviate the
output for brevity.  The actual output you see will be more verbose.

## The index and working tree

First let's review the index and the working tree, which are necessary to
understand git reset.  If you feel very comfortable with them, feel free to
breeze through this section, just setting up the commits.  We'll use those
commits in the discussion of git-reset below.

## The index

The index is a staging area where changes are held before they are committed.
Let's see it in action in a simple scenario.

```sh
$ mkdir git-reset && cd git-reset
$ git init
Initialized empty Git repository in /Users/jag/tmp/git-reset/.git/
$ echo "A1" > a.txt
$ git status
Untracked files:
	a.txt
$ git diff
```

In terms of the four stages, we have:
```
A1 < filetree
NULL < HEAD, index, worktree
```

(An initialized git repo starts with no commits, so HEAD is not defined).

At this point, we have a single untracked file.  By definition, this file is
in the filetree, but git has no knowledge of it yet.   That's why `git diff`
does not tell us about the changes to `a.txt`. As soon as git knows
about it, it is considered in the _working tree_; and git helpfully tells us
to add it:

```sh
$ git add a.txt
$ git status
Changes to be committed:
	new file:   a.txt
$ git diff
```

So now git knows about it, but why did `git diff` still return nothing?
Because the `a.txt` is actually in the _index_.  The index is like a
'commit-in-waiting'; by adding changes you are building up what will be the
next commit.  We can check the diff with the `--staged` option:

```sh
$ git diff --staged
new file mode 100644
--- /dev/null
+++ b/a.txt
+A1
```

In terms of our four stages, we have:
```
A1 < index, worktree, filetree
NULL < HEAD
```

There's a lot of information here, but we can see that it's a new file, and
the contents are the expected 'A1'.  Let's commit it.

```sh
$ git commit -m 'A1'
[master (root-commit) 5b2c703] A1
 1 file changed, 1 insertion(+)
 create mode 100644 a.txt
$ git status # Nothing here after commit
$ A1=`git rev-parse HEAD`
```

The last line just stores the current commit hash in a variable we'll use
later.  The details aren't important, but if you want to know more you can
`git help rev-parse`.

The four stages are now all pointing to the same commit:
```
A1 < HEAD, index, worktree, filetree
```

## The working tree

We can think of HEAD, the index, and the working tree as accumulating the
changes we are making to the file tree.  Now that we have commited A1,
HEAD, the index, and the working tree are all up-to-date with the file tree.

Now that `a.txt` is known to git, changes to it show up in the working tree.

```sh
$ echo 'A2' >> a.txt
$ git status
Changes not staged for commit:
	modified:   a.txt
$ git diff
--- a/a.txt
+++ b/a.txt
 A1
+A2
```

Now our picture looks like:

```
A2 < worktree, filetree
A1 < HEAD, index
```

Adding `a.txt` moves the changes from the working tree to the index:
```
$ git add a.txt
$ git status
Changes to be committed:
	modified:   a.txt
$ git diff
$ git diff --staged
--- a/a.txt
+++ b/a.txt
 A1
+A2
```

Now our picture looks like:
```
A2 < index, worktree, filetree
A1 < HEAD
```

The changes no longer appear in `git diff`, just in `git diff --staged`.  If we
change `a.txt` again, the new changes are not in the index, just the working tree.

```sh
$ echo 'A3' >> a.txt
$ git status
Changes to be committed:
	modified:   a.txt
Changes not staged for commit:
	modified:   a.txt
$ git diff
--- a/a.txt
+++ b/a.txt
 A1
 A2
+A3
$ git diff --staged
--- a/a.txt
+++ b/a.txt
 A1
+A2
```

Our stages are:
```
A3 < worktree, filetree
A2 < index
A1 < HEAD
```

Notice that `git diff --staged` has not changed, but the new changes are in
`git diff`.  Now if we commit, we just commit the things in the index.

```sh
$ git commit -m 'A2'
[master cdd1bff] A2
 1 file changed, 1 insertion(+)
$ git status --short
Changes not staged for commit:
	modified:   a.txt
$ A2=`git rev-parse HEAD`
```

The index changes are gone, but the working tree is left unchanged.  Note that
the file tree is unchanged; we've just been catching the commits up to the index.

```
A3 < worktree, filetree
A2 < HEAD, index
A1
```

Lastly, let's commit the last changes so that we are positioned to explore
`git reset`.

```sh
$ git add a.txt
# A3 < index, worktree, filetree
# A2 < HEAD
$ git commit -m 'A3'
[master 813395c] A3
 1 file changed, 1 insertion(+)
$ A3=`git rev-parse HEAD`
```

Now everything is pointed at A3!

```
A3 < HEAD, index, worktree, filetree
A2
A1
```

## The many flavors of git reset

The `reset` command takes a bewildering number of forms and options.  We'll
attempt to demystify these.  The fundamental principal is that `git reset`
moves HEAD to the commit specified, and the options control what happens
to the index, working tree, and file tree.

## hard reset

Let's start with `git reset --hard`.  This is the simplest to understand,
because it moves all four stages to the designated commit.

```sh
$ git log --oneline --decorate
813395c (HEAD -> master) A3
cdd1bff A2
5b2c703 A1
$ git reset --hard $A2
$ git log --oneline --decorate
cdd1bff (HEAD -> master) A2
5b2c703 A1
$ cat a.txt
A1
A2
```

Now we have
```
A3
A2 < HEAD, index, worktree, filetree
A1
```

Using `git reset --hard COMMIT` tells git to make all files that it knows
about into the form expected by `COMMIT`.  Note that it doesn't touch any
untracked files.

## Soft and Mixed

Make sure you are on the `A3` commit:

```sh
$ git reset --hard $A3
```

Our four stages are:
```
A3 < HEAD, index, worktree, filetree
A2
A1
```

When you `git reset --soft COMMIT`, it resets `HEAD` to point to `COMMIT`, but
leaves the index, working tree, and file tree unchanged.

```sh
$ git reset --soft $A2
Changes to be committed:
	modified:   a.txt
$ git diff --staged
--- a/a.txt
+++ b/a.txt
 A1
 A2
+A3
$ git log --oneline --decorate
cdd1bff (HEAD -> master) A2
5b2c703 A1
```

We've moved `HEAD` back to the A2 commit.  Notice that `a.txt` is in the index.

We have
```
A3 < index, worktree, filetree
A2 < HEAD
A1
```

Instead, if we had used `git reset --mixed`, we'd have left the changes in the
working tree.  (Note that `--mixed` is the default level, so `git reset` is
equivalent to `git reset --mixed`).

```sh
$ git reset --hard $A3
$ git reset --mixed $A2
Unstaged changes after reset:
M	a.txt
$ git status
Changes not staged for commit:
	modified:   a.txt
$ git diff
--- a/a.txt
+++ b/a.txt
 A1
 A2
+A3
$ git log --oneline --decorate
cdd1bff (HEAD -> master) A2
5b2c703 A1
```

We have
```
A3 < worktree, filetree
A2 < HEAD, index
A1
```

Now let's combine the two, to show their difference more clearly.  From the
above state, we can use `git reset --soft`:

```sh
$ git reset --soft $A1
$ git status
Changes to be committed:
	modified:   a.txt
Changes not staged for commit:
	modified:   a.txt
$ git diff
--- a/a.txt
+++ b/a.txt
 A1
 A2
+A3
$ git diff --staged
--- a/a.txt
+++ b/a.txt
 A1
+A2
$ git log --oneline --decorate
5b2c703 (HEAD -> master) A1
```

We have
```
A3 < worktree, filetree
A2 < index
A1 < HEAD
```

Now that we understand the difference between `--soft`, `--mixed`, and
`--hard`, let's get back to A3:

```sh
$ git reset --hard $A3
```

## reset vs checkout

While both `git reset` and `git checkout` change where HEAD is pointing, they
do this in fundamentally different ways.  `git checkout` moves HEAD to
point to the given branch (or commit-ish), without moving any branches.
`git reset` instead moves the active branch (pointed to by HEAD) to the supplied
commit-ish, dragging HEAD along with it.  In other words, `git checkout` switches
what you are working on, while `git reset` modifies what you are working on.

```sh
$ git checkout --branch dev
$ git log --oneline --decorate --all
* 1fd9bf6 (HEAD -> dev, master) A3
* ad01fba A2
* 3162ad7 A1

$ echo B1 >> b.txt
$ git add b.txt
$ git commit -m "B1"
$ git log --oneline --decorate --all
* b0e3450 (HEAD -> dev) B1
* 1fd9bf6 (master) A3
* ad01fba A2
* 3162ad7 A1

$ git checkout master
$ git log --oneline --decorate --all
* b0e3450 (dev) B1
* 1fd9bf6 (HEAD -> master) A3
* ad01fba A2
* 3162ad7 A1
```

Notice that the `dev` branch does not change, only the position of HEAD.
Contrast this with when you `reset`:

```sh
$ git checkout dev
$ git log --oneline --decorate --all
* b0e3450 (HEAD -> dev) B1
* 1fd9bf6 (master) A3
* ad01fba A2
* 3162ad7 A1

$ git reset master
$ git log --oneline --decorate --all
* 1fd9bf6 (HEAD -> dev, master) A3
* ad01fba A2
* 3162ad7 A1

$ git reset b0e3450
$ git log --oneline --decorate --all
* b0e3450 (HEAD -> dev) B1
* 1fd9bf6 (master) A3
* ad01fba A2
* 3162ad7 A1
```

When you reset, you move the branch as well.

## Summary

We've seen the four stages of commitment, namely filetree, working tree, index,
and HEAD.  The `reset` command conceptually moves those four stages; this in
turn might affect the content of files or whether changes are staged or
committed.  It can be useful to undo work, or to get the filetree/index in
the appropriate state.

It differs at a fundamental from the `checkout` command, even though
sometimes their effects look similar. The checkout command doesn't affect the
underlying commits, only where HEAD is pointing; you cannot lose committed
data, only move along the commit DAG. The `reset` command changes state at a
more fundamental level (especially the `--hard` option); you can undo work
and modify the commit DAG, even removing commits from it.