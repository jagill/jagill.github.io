---
title: "Git Remote Branches"
short_title: "Remote Branches"
order: 3
---

Git Remote Branches
===================
Now that you understand [git commits](git-dag.md), let's talk about remote
branches, which is how we unlock the power of distributed version control.
There are a couple important concepts that we will talk more about later,
but the terminology of local and remote branches and repos can be a bit
confusing, so let's introduce them now:

* _local branch_: A local branch is the branch you are used to.  It lives
  on your machine, and you can commit to it via the normal workflow.
* _remote repository_: A remote repository (usually just called _remote_) is a
  repository different than your local repository that your local repo is
  tracking.  It may have local branches, just like your local repo.  You can
  pull from a remote repo, which will bring the local branches of the remote
  repo into the remote branches of your local repo (we'll explain that later).
* _remote branch_: A remote branch is a local copy of a branch on a remote
  repo. It will be shown in `git branch --all` as `REMOTE/BRANCH`.  These
  track the local branches of remote repos.

**NB**: We've abbreviated the output of the `fetch` and `push` subcommands
for clarity.

Remote Repositories
-------------------

Every git repo -- including the local one on your machine -- is a complete
repo, with all the commit history back to the root commit[1].  This includes the
branches (which are just pointers to a given commit).  The branches consist
of at least `master`, but often several others.  A fundamental operation in
git is to clone a repository, which makes a local repository by copying all of
the commit history from another repository (eg, one on GitHub).  Usually this
"remote" repo is on another machine, but you can clone any repo with a valid
git URL, including one on your own machine.  We'll do that for the tutorial,
but normally this repo would be somewhere else.  Let's make the "remote" repo.

```sh
tmp/ $ mkdir git-remote
tmp/ $ cd git-remote
git-remote/ $ git init --bare remote
git-remote/ $ ls
remote/
```

We've created a special kind of repo called a "bare" (or "headless") repo.
It does not have a `HEAD` pointer, so it's not a place you can directly
do work or commit to, but it can get commits from other places (as we will
do shortly).

Now let's clone it to a "local" repo.  This will make a "downstream" repo; one
that will track the changes in the "upstream" (remote) repo.
```sh
git-remote/ $ git clone remote local1
Cloning into 'local1'...
done.
git-remote/ $ ls
local1/  remote/
```

In the `git clone` command, `remote` is the URL of the "parent" repo (in this
case, just a directory), and `local1` is the path of the local repo.  Notice
that it makes a directory named `local1`.  Let's make a commit and push it to
the remote.

```sh
git-remote/ $ cd local1
local1/ $ echo 'A1' > a.txt
local1/ $ git add a.txt
local1/ $ git commit -m 'A1'
local1/ $ git log --oneline --decorate --all
cdf451e (HEAD -> master) A1
local1/ $ git push
To /tmp/git-remote/remote
 * [new branch]      master -> master
local1/ $ git log --oneline --decorate --all
* cdf451e (HEAD -> master, origin/master) A1
```

Note that after we pushed, a new branch appeared, `origin/master`.  This is a
`remote` branch, which tracks a local branch on a remote repository.
What happened in the remote repo?

```sh
local1/ $ cd ../remote
remote/ $ git log --oneline --decorate --all
cdf451e (HEAD -> master) A1
```

The commit is now in the remote branch, as is the `master` branch.  Let's clone
it to a new local branch.

```sh
remote/ $ cd ..
git-remote/ $ git clone remote local2
Cloning into 'local2'...
done.
git-remote/ $ cd local2
local2/ $ git log --oneline --decorate --all
* cdf451e (HEAD -> master, origin/master, origin/HEAD) A1
```

The new repo has all the commits that the remote repo has.  Let's make a change
here, and see what happens on `local1`.

```sh
local2/ $ echo A2 >> a.txt
local2/ $ git commit a.txt -m "A2"
[master c65a734] A2
 1 file changed, 1 insertion(+)
local2/ $ git push
To /tmp/git-remote/remote
   cdf451e..c65a734  master -> master
local2/ $ cd ../remote
* c65a734 (HEAD -> master) A2
* cdf451e A1
remote/ $ cd ../local1
local1/ $ git log --oneline --decorate --all
* cdf451e (HEAD -> master, origin/master) A1
```

While the changes are in the `remote` repo, they are not yet in `local1`.  We
can `fetch` these changes:

```sh
local1/ $ git fetch
local1/ $ git log --oneline --decorate --all
* c65a734 (origin/master) A2
* cdf451e (HEAD -> master) A1
```

Now we have the new commit, but our local `master` doesn't point to it.  We see
the remote branch `origin/master` points to the new commit; we can `merge` that
into our local `master`:

```sh
local1/ $ git merge origin/master
Updating cdf451e..c65a734
Fast-forward
 a.txt | 1 +
 1 file changed, 1 insertion(+)
local1/ $ git log --oneline --decorate --all
* c65a734 (HEAD -> master, origin/master) A2
* cdf451e A1
```

Now our branches, as well as our commits, are the same on `local1` and `local2`.
Since this operation is performed so frequently, there's a shortcut command for
it: `git pull`.  It will perform a `git fetch`, then a
`git merge origin/CURRENT_BRANCH`.  If your current branch doesn't have a
remote tracking branch, it will return an error.

The `fetch`/`merge`/`pull` distinction is an important one, so we'll emphasize
it here:

* `git fetch` fetches all the commits from the remote repo to the local repo,
  and updates the remote branches.
* `git merge` can merge a remote branch into a local one.
* `git pull` is a shortcut that fetches and then merges a remote tracking branch
  into the current local one.

Multiple Branches
-----------------
One common point of confusion arises when people want to push a local branch to
a remote repo.  Conceptually, you often want to create a new branch on `origin`
with the same name as your local branch, and have your local branch track this
branch.  The default option in git does not do this, which sometimes leads to
confusion.  Let's do it the wrong way first.

```sh
local1/ $ git checkout -b dev
Switched to a new branch 'dev'
local1/ $ echo B1 > b.txt
local1/ $ git add b.txt
local1/ $ git commit -m "B1"
[dev ade622a] B1
 1 file changed, 1 insertion(+)
 create mode 100644 b.txt

local1/ $ git branch -vv # This should any upstream branches
* dev    ade622a
  master c65a734 [origin/master] A2

local1/ $ git push
fatal: The current branch dev has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin dev

local1/ $ git push origin dev # Notice we did not include --set-upstream
To /tmp/git-remote/remote
 * [new branch]      dev -> dev

local1/ $ git pull
There is no tracking information for the current branch.
Please specify which branch you want to merge with.
See git-pull(1) for details

    git pull <remote> <branch>

If you wish to set tracking information for this branch you can do so with:

    git branch --set-upstream-to=origin/<branch> dev

local1/ $ git branch -vv # Notice still no upstream branch
* dev    ade622a
  master c65a734 [origin/master] A2

local1/ $ git push --set-upstream origin dev
Branch dev set up to track remote branch dev from origin.

local1/ $ git branch -vv # There's the upstream branch!
* dev    ade622a [origin/dev] B1
  master c65a734 [origin/master] A2

local1/ $ git pull
Already up-to-date.
```

Notice that we can't push without arguments, because git does not know what to
do with this new branch.  We can tell it specifically which remote and which branch
to push to, but unless we tell it to set that remote branch as an upstream
tracking branch, it doesn't know that we want to keep those branches in sync.

As a side note, `git branch [-v, --v]` is a useful tool to display what git knows
about your branches.

Now that the `dev` is tracking `origin/dev`, commits by either local repo can
be transferred to the other.

```sh
local1/ $ cd ../local2
local2/ $ git branch -a
* master
  remotes/origin/HEAD -> origin/master
  remotes/origin/master
local2/ $ git fetch
From /Users/jag/tmp/git-remote2/remote
 * [new branch]      dev        -> origin/dev
local2/ $ git branch -a
* master
  remotes/origin/HEAD -> origin/master
  remotes/origin/dev
  remotes/origin/master
local2/ $ git log --oneline --decorate --all
* ade622a (origin/dev) B1
* c65a734 (HEAD -> master, origin/master, origin/HEAD) A2
* cdf451e A1
local2/ $ git checkout dev
Branch dev set up to track remote branch dev from origin.
Switched to a new branch 'dev'
local2/ $ git log --oneline --decorate --all
* ade622a (HEAD -> dev, origin/dev) B1
* c65a734 (origin/master, origin/HEAD, master) A2
* cdf451e A1
```

Now we can work on branch `dev` in `local2`.

```sh
local2/ $ echo B2 >> b.txt
local2/ $ git commit b.txt -m 'B2'
[dev 73a9efd] B2
 1 file changed, 1 insertion(+)
local2/ $ git push
To /Users/jag/tmp/git-remote2/remote
   ade622a..73a9efd  dev -> dev
local2/ $ cd ../local1
local1/ $ git log --oneline --decorate --all
* ade622a (HEAD -> dev, origin/dev) B1
* c65a734 (origin/master, master) A2
* cdf451e A1
local1/ $ git pull
From /Users/jag/tmp/git-remote2/remote
   ade622a..73a9efd  dev        -> origin/dev
Updating ade622a..73a9efd
Fast-forward
 b.txt | 1 +
 1 file changed, 1 insertion(+)
local1/ $ git log --oneline --decorate --all
* 73a9efd (HEAD -> dev, origin/dev) B2
* ade622a (origin/temp) B1
* c65a734 (origin/master, master) A2
* cdf451e A1
```

Now people working in two different local branches can coordinate through a
remote branch.

Multiple Remotes
----------------
The flow we just described is called the 'centralized' workflow, because
all commits are going through a single, central, remote repository.  However,
git was designed first and foremost to be a distributed system, allowing
people to manage commits from many remotes.

One of the main ways that people use this is for pull requests.  If someone
wishes to contribute to your repository, they will often fork it, push changes
to their remote repository, and let you review the changes before you decide
to merge them into your branch.  Let's do that for our two users, `local1`
and `local2`.

First let's create and set up another remote, called `remote2`.

```sh
local2/ $ cd ..
git-remote/ $ git clone --bare remote/ remote2/
Cloning into bare repository 'remote2'...
done.
git-remote/ $ cd local2
local2/ $ git remote
origin
local2/ $ git remote add remote2 ../remote2
local2/ $ git remote
origin
remote2
local2/ $ git fetch remote2 # fetch by default uses origin
From ../remote2
 * [new branch]      dev        -> remote2/dev
 * [new branch]      master     -> remote2/master
```

We've cloned another remote off of our original remote repository, and added it
as a remote for `local2`.  Let's push a change to the `dev` branch of `remote2`,
so that `local1` can review the changes.

```sh
local2/ $ git checkout dev
local2/ $ echo B3 >> b.txt
local2/ $ git commit b.txt -m 'B3'
[dev c992ab9] B3
 1 file changed, 1 insertion(+)
local2/ $ git push remote2 dev
To ../remote2
   73a9efd..c992ab9  dev -> dev
local2/ $ git log --oneline --decorate --all
* c992ab9 (HEAD -> dev, remote2/dev) B3
* 73a9efd (origin/dev) B2
* ade622a B1
* c65a734 (remote2/master, origin/master, origin/HEAD, master) A2
* cdf451e A1
```

Notice that we have remote branches for both remote repos.  When we pushed, we
needed to explicitly set the remote and the branch to push to, because the
local branch `dev` is set to track `origin/dev`, which is supplied as a default
if we just use `git push`.  Since we don't want to push to the default, we need
to be explicit.

Let's go to `local1` and pull these changes to another branch, review the diffs,
and merge them.

```sh
local2/ $ cd ../local1
local1/ $ git remote add remote2 ../remote2
local1/ $ git fetch remote2
From ../remote2
 * [new branch]      dev        -> remote2/dev
 * [new branch]      master     -> remote2/master
local1/ $ git log --oneline --decorate --all
* c992ab9 (remote2/dev) B3
* 73a9efd (HEAD -> dev, origin/dev) B2
* ade622a (origin/temp) B1
* c65a734 (remote2/master, origin/master, master) A2
* cdf451e A1
```

So now we have the new code in the remote branch `remote2/dev`.  Let's make
a branch that tracks it, so that we can see the changes.

```sh
local1/ $ git branch dev2 remote2/dev
Branch dev2 set up to track remote branch dev from remote2.
local1/ $ git lola
* c992ab9 (remote2/dev, dev2) B3
* 73a9efd (HEAD -> dev, origin/dev) B2
* ade622a (origin/temp) B1
* c65a734 (remote2/master, origin/master, master) A2
* cdf451e A1
local1/ $ git checkout dev2
Switched to branch 'dev2'
Your branch is up-to-date with 'remote2/dev'.
```

First, we create a local branch `dev2` which tracks the remote branch `remote2/dev`, and then checked it out.  If we wanted to modify it
and push those changes upstream, we could.  Or, we can merge it into
our local version of `dev`, and push those changes upstream to
`origin/dev`:

```sh
local1/ $ git checkout dev
Switched to branch 'dev'
Your branch is up-to-date with 'origin/dev'.
local1/ $ git merge dev2
Updating 73a9efd..c992ab9
Fast-forward
 b.txt | 1 +
 1 file changed, 1 insertion(+)
local1/ $ git push
To /Users/jag/tmp/git-remote2/remote
   73a9efd..c992ab9  dev -> dev
```

Now these changes can be seen by `local2`, as normal.

Summary
-------
We've seen that each repo is a complete record of the codebase.  Local repos
are where people make modifications, and remote repos are places that changes
can be distributed to others.  The most common model is the centralized model,
where everyone shares a single remote repo.  Another model is distributed, and
in the extreme case every person has their own remote repo that they can push
changes to, and that others can pull from.

A local repo has both local branches, and remote branches which track the
"local" branches of the remote repos.  A branch can "track" another branch,
which means when the upstream (tracked) has changes, "pull" will merge
those changes into the downstream (tracking) branch, and a "push" will merge
changes from the downstream branch to the upstream.
