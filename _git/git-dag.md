---
short_title:  "Git Commit Dag"
title:  "Git Commit Dag"
---


Git commits as a DAG
====================
The fundamental object that we'll be talking about is a commit[1].  A commit
is the current state of the file tree, along with some metadata.  Some of this
metadata is an author, and a message the author includes to explain the
changes since the last commit.  Another extremely important bit of metadata
is the commit's parent commits.  Most commits have a single parent, which is
the previous state of the file tree.  Sometimes, such as in a merge, a commit
has multiple parents, since it inherits from and reconciles two or more
different states.  A fancy way of saying this is that a git repo forms a
Directed Acyclic Graph (or DAG), with the commits as nodes, and the parent
relationship being an arrow.

Before we get started, let's make some aliases that will make visualization
easier.  Enter the following commands:
```sh
$ git config --global alias.lol "log --graph --decorate --pretty=oneline --abbrev-commit"
$ git config --global alias.lola "log --graph --decorate --pretty=oneline --abbrev-commit --all"
```

Also, make sure you have the latest version of git (as of this writing, 2.5.0).
On OS X, I suggest installing git via [Homebrew](http://brew.sh/).

### Our first commit
Let's make this concrete.  Make a new directory called `git-dag-tutorial`,
enter it, and then initialize the git repository:
```sh
$ mkdir git-dag-tutorial
$ cd git-dag-tutorial
$ git init
$ git status
On branch master

Initial commit

nothing to commit (create/copy files and use "git add" to track)
```

You now have an empty repository; it doesn't even have a commit yet.  Let's
make our first commit.
```sh
$ echo 'A0' > a.txt # Make a file just containing 'A0'
$ git add a.txt
$ git commit -m 'A0'
[master (root-commit) c32f318] A0
 1 file changed, 1 insertion(+)
 create mode 100644 a.txt
$ git lol
* c32f318 (HEAD -> master) A0
$ A0=`git rev-parse HEAD`
```
The repo now has as a single commit,  and this commit is the only one that does
not have a parent.  This is an important property of a repo -- there is only
one 'root' commit, so if you trace back the ancestry of any commit, you will
eventually end up here.

The command `git lol` will show us the current commit (called `HEAD`), and its
parent(s) recursively until we reach the root commit.  Try it now.  We only
have one commit, so it will just show that.  The first column is of the form
`c32f318...`; the crazy hex number is called the commit hash.  It will
be different for everybody, so in the last line we just saved it in the
environment variable `A0`.  Also, try `git show HEAD`; notice that it shows you
that same commit, with some more information on it.

We are also on a branch.  Type `git branch`, and notice it outputs `* master`.
This means we are on the master branch.  A branch is really just a pointer to
a given commit that keeps up as we create new commits.  Try `git show master`;
notice that it gives the same commit.  Actually, we were being inaccurate above;
in reality HEAD doesn't point to our first commit A0, it points to `master` which
then points to A0.  This is shown in the output of `git lol`; a single commit,
with a hash that we'll represent by A0, that is pointed to by branch `master`.
`HEAD` in turns points to `master`.

It's important to understand the difference between when `HEAD` pointing to
`master` which points to A0, and when both `HEAD` and `master` point to A0
separately.  We can get to the latter state by:

```sh
$ git checkout $A0 # This will use the last commit above.
$ git lol
* c32f318 (HEAD, master) A0
```

`git checkout` roughly means "move `HEAD` to the given place, and change the
filesystem to match `HEAD`."
Notice that when you did the checkout, you got a scary message about being in
'detached HEAD' state.  Many people are afraid of this cryptic message, but you now
know what it means.  We can easily escape it by typing `git checkout master`,
which puts us back in our earlier, safer, state.  Do that now:

```sh
$ git checkout master
```

### Branching
Let's add to our file.
```sh
$ echo 'A1' >> a.txt # Add the line 'A1'; make sure you have double brackets!
$ git commit a.txt -m 'A1'
[master 0c5a853] A1
 1 file changed, 1 insertion(+)
$ git lol
* 0c5a853 (HEAD -> master) A1
* c32f318 A0
```

The order means that A0 is the parent of A1.
Notice that `master` has moved up to the new commit A1, dragging `HEAD` up with
it.  Had we been in the 'detached HEAD' mode above when we made our commit,
our graph would look like:
```ssh
$ git lol
* 0c5a853 (HEAD) A1
* c32f318 (master) A0
```

In this case, if we committed in the detached `HEAD` state, we would have
left branch `master` behind.  Being on a branch means the branch moves with us.

Now let's experiment with branching!

```sh
$ git branch dev
$ git branch
  dev
* master
$ git lol
* 0c5a853 (HEAD -> master, dev) A1
* c32f318 A0
```

The first command makes a branch, pointed at our current commit, and the second
command shows the branches, putting an `*` before the branch `HEAD` is pointing
to.  Notice that in the log, we see that both `master` and `dev` point to A1,
and `HEAD` points to `master`.

Now let's switch branches:
```sh
$ git checkout dev
$ git branch
* dev
  master
$ git lol
* 0c5a853 (HEAD -> dev, master) A1
* c32f318 A0
```
`HEAD` is now pointing to branch `dev`.

Now let's make another commit:
```sh
$ echo 'B2' > b.txt
$ git add b.txt
$ git commit -m 'B2'
$ git lol
* 4e7b4c1 (HEAD -> dev) B2
* 0c5a853 (master) A1
* c32f318 A0
```

Checking `git lol` shows three commits; the most recent we'll call B2.
Notice `master` is still pointed at A1, while `dev` (and `HEAD`) is pointed
at B2.  Let's go back to master to see where we are:
```sh
$ git checkout master
$ ls
$ git lol
* 0c5a853 (HEAD -> master) A1
* c32f318 A0
```
Notice that there is only the file `a.txt`, and the log only shows A1 and A0,
which is what we expect.  When we are
pointing at a commit, we can only get information about its ancestors, not
its descendants.  This is an important enough point that we'll put it in
bold: **A commit knows everything about its ancestors, and nothing about
its descendants** [2].

We can see the graph with all the branches by
```sh
$ git lola
* 4e7b4c1 (dev) B2
* 0c5a853 (HEAD -> master) A1
* c32f318 A0
```

Let's make an additional commit on `master`.
```sh
$ echo 'A2' > a.txt
$ git commit a.txt -m 'A2'
$ git lol
* 93f50b6 (HEAD -> master) A2
* 0c5a853 A1
* c32f318 A0
```

We can see how `master` and `dev` relate:
```sh
$ git lola
* 93f50b6 (HEAD -> master) A2
| * 4e7b4c1 (dev) B2
|/
* 0c5a853 A1
* c32f318 A0
```

Our branches have diverged!  The parent of both A2 and B2 is A1, but A2 and B2
don't know anything about each other.

### Merging
How does merging fit into this picture?  Merging two branches makes a commit
that has the tip of each branch as parents.

```sh
$ git merge dev
$ git lol
*   eb328ca (HEAD -> master) A3
|\
| * 4e7b4c1 (dev) B2
* | 93f50b6 A2
|/
* 0c5a853 A1
* c32f318 A0
```
Notice that `dev` is still pointing to B2, but `master` now points to a commit
A3 that has both A2 and B2 as parents.  Now that `dev` has been merged into
`master`, `master` knows all about `dev` and its history.

What's up with `dev`?

```sh
$ git checkout dev
$ git lol
* 4e7b4c1 (HEAD -> dev) B2
* 0c5a853 A1
* c32f318 A0
$ git merge master
$ git lol
*   eb328ca (HEAD -> dev, master) A3
|\
| * 4e7b4c1 B2
* | 93f50b6 A2
|/
* 0c5a853 A1
* c32f318 A0
```

Notice that this merge didn't make a new commit, it just moved `dev` to point
at A3; this is called a 'fast-forward' merge.  This is another very important
point: **By default, if a merge can be accomplished by moving a branch to an
existing commit that satisfies the merge, it will do this.**

You can also add the `--no-ff` flag to a merge, which forces it to not
fast-forward.  Had we done that, the commits would be
```sh
*   d85fcb6 (HEAD -> dev) B3
|\
| *   eb328ca (master) A3
| |\
| |/
|/|
* | 4e7b4c1 B2
| * 93f50b6 A2
|/
* 0c5a853 A1
* c32f318 A0
```
This makes the commit tree more complex, but keeps an explicit record of the
merge.

### Conclusion
Now you understand, at a commit level, what's happening when you branch and
merge.  It might be fruitful to experiment with committing, branching,
merging, detaching `HEAD`, `git reset`, and more, checking with `git lol` and
`git lola` to see the commit tree.

### Footnotes

[1] Commits are made up of blobs and trees, which are more fundamental, but
we'll not go down to that level.

[2] In fact, a commit that has nothing pointing to it is
considered garbage, and will be cleaned up and deleted by git in about 30 days.
