+++
title = "A Primer on Computer Memory"
weight = 0
date = 2021-01-05

[taxonomies]
tags = ["systems"]
categories = ["tech"]
+++

While I've long known a computer runs by manipulating bits, I didn't have a
good mental model of where those bits are stored and how they are accessed.
I've had to build that understanding over the years, which has helped greatly
as I've optimized training pipelines for neural nets, or developed data
structures for high-performance computing. Talking to colleagues in the
industry, I've found many of them are also uncertain about some foundational
details. This article will build a mental model of computer memory, so that
you can reason about the computer's memory model, and why certain things are
fast and others slow.

<!-- more -->

First I'll talk about chunking _bits_ into _bytes_ and _words_. Second, I'll
talk about _registers_ and how all operations are ultimately done on those.
Next I'll talk about _RAM_, the special registers that deal with it, and what
_allocation_ and _deallocation_ mean. This will allow us to describe the
_stack_, and how data is transferred to and from function calls. The
limitations of the stack will introduce the _heap_, and some more strategies
for _allocation_ and _deallocation_. I'll briefly discuss _disks_ and
secondary storage. _Virtual Memory_ will be a powerful construct that allows
us to blur the boundaries between disks and RAM, and it sets up the
difference between _kernel space_ and _user space_ and how kernels manage the
memory of multiple processes. These processes might use _inter-process
communication_, which can be expensive. _Threads_ are an alternative that are
cheaper but have their own tradeoffs. Lastly, I'll talk about _CPU caches_,
which are critical to how modern CPUs are so fast.

These pieces will build up the _memory hierarchy_, which are layers of
progressively larger and slower types of memory.  This hierarchy consists --
from fastest to largest -- of registers, CPU caches, RAM, and disks.  Efficient
computation keeps frequently and imminently needed data in the lower levels of
the hierarchy, using the higher levels as storage.

Readers who know this material will find many places where I ignore lots of
details, some of which may be considered important. I'll intentionally
simplify the mental model of memory to give people an intuition as to what's
happening, but this necessitates being a bit fast and loose. I encourage
interested readers to dig deeper into the details from other sources.  I've
listed some I particularly like at the end.

## Bits, Bytes, and Words

Bits are things that can be in two positions, which we traditionally call 0
or 1. In modern computers, they may be tiny capacitors, tiny magnetic
regions, or more. The details of a bit won't concern us, but you should know
that there are trade-offs involved in the choice of bit-material: speed,
cost, volatility, and more. If you wonder why we don't just build all of our
memory with the super-fast stuff, know that there is a reason (and it's not
just cost!).

The smallest number of bits that modern computers can reasonably access is 8,
called a byte. To check an individual bit, the computer would need to load a
byte then check the bit (by something like an AND operation).

Computers based on single bytes fell out of favor some time ago. The
architecture started assuming multi-byte chunks as a primitive memory size:
first 2 bytes, then 4 bytes, then 8 bytes on most modern architectures. This
natural chunk size is called a _word_. Let's simplify our discussion (at a
small cost in accuracy) by assuming that all memory movements, computations,
etc are done in units of a word.[^cache-lines]

[^cache-lines]: Actually, movement between RAM and the CPU is done in units
of cache-lines, and from disk to RAM in units of pages.  We'll discuss these,
but it won't affect our mental model.

## ALUs, Registers, and CPUs

The fundamental computation unit of a computer is called the _Arithmetic
Logical Unit_, or _ALU_. Its job is to combine either one or two input words
to produce an output word. For example, it might negate an integer, add two
integers to produce their sum, or XOR two words.[^other-alu-ops]. These words
are stored in _registers_, which are very fast word-sized pieces of memory
that are very close to the ALU. Often, the ALU will combine two registers and
store the output in one of those two registers, although this is not always
the case.

Which two registers are used, and what should be done with them, is
controlled by the _Central Processing Unit_, or _CPU_. While most registers
are general purpose (with descriptive names like A, B, C, D...), some have
special purposes. One of those is the _Instruction Register_ (_IR_) which
holds a value which tells the CPU which operation it should perform and on
which registers. Another is the _Program Counter_ (_PC_), which holds a word
that is the memory address in _RAM_ (see below) of the next instruction. Very
roughly, the CPU will load the word at the address of the Program Counter
into the Instruction Register, increment the Program Counter, then perform
that operation in the Instruction Register on the specified registers. This
sequence is called a _cycle_, and it's the fundamental unit of time for a
computer.

To keep things interesting, some the operations can change the value of the
Program Counter to jump around the program. This enables loops, if-then-else,
and other control flow statements.

[^other-alu-ops]: There are other bits that are inputs and outputs to the
ALU, like carry bits for addition, or various outcomes when you compare two
words. They aren't critical to understanding the memory model.

## RAM and the memory registers

The amount of memory that can be held in the registers is too small to
contain the necessary information for any non-trivial program. For that, we
need _Random Access Memory_, which is a large pool of memory that is
relatively slow (compared to registers) and far from the CPU. The program (a
sequence of instructions) is stored in RAM. I mentioned above how the Program
Counter and Instruction Register are used to read and execute instructions
from RAM, and something similar is done for data.

To get values to and from RAM, we use two special registers call the _Memory
Address Register_ (_MAR_) and the _Memory Data Register_ (_MDR_). The Memory
Address Register contains the address in RAM that we'll be reading or
writing, and the Memory Data Register will contain the value that we'll
write, or it will be the destination of the value that we'll read. Then the
CPU can move the values to/from the Memory Data Register from/to the general
purpose registers, allowing the ALU to effectively operate on data in RAM.

In addition to the special part of RAM that contains the program
instructions, the constant values of the program are stored in a special
_static_ block of memory that exists for the length of the process. When you
write the expression `global int x = 5;` the value `5` is stored in the
static block, and accessed by its memory location.

While a process could use RAM as an unstructured space of memory, it would
need to keep track of which locations are in use and which could be used for
new storage. This problem is called _allocation_, and it is hard. It would
also need to keep track of when and where it can free memory that it was
using, but no longer needs. This is called _deallocation_, and it is also
hard. It gets much harder when you have multiple processes running
simultaneously, which modern computers generally do!

To reduce this problem to a manageable complexity, first we'll discuss how a
single process structures its memory, then how an operating system keeps
processes from stepping on each other's data.

## The Stack

A way of managing allocations and deallocations is a _call stack_ (or just
_stack_). This is a more structured method for memory management that is the
basis of all modern computing. As its name implies, the stack is a region of
memory that grows by pushing values on to the end, and popping values off of
that same end. In most computer architectures, the stack starts at an address
and grows _down_, to lower memory addresses[^stack-direction].

A _subroutine_ is a block of instructions (like a function) that is separated
from the main routine, in execution and in data. The main routine can call
subroutines, but subroutines can also call subroutines. At any given point,
the process is in a subroutine at some level of nesting, with the subroutine
that called it above it, and so on until the main routine.

Subroutines allow us to organize the stack into blocks called _stack frames_.
When a subroutine starts, it adds the memory location of the calling
instruction to the stack, and any arguments to the function
call[^stack-header]. This is considered the start of the stack frame, and a
special register called the _frame pointer_ will store the memory address of
the start of the frame. Another special register called the _stack pointer_
will also start with the address just after the frame pointer, which points
to the first free memory of the stack frame. As a variable local to the
function is allocated, the stack pointer is decremented by the size of the
variable, and the value of the variable is written at the position of the
stack pointer.

When this variable needs to be referenced, it can be referenced by the stack
pointer minus some offset. When the function returns, the stack pointer can be
reset to the frame pointer, deallocating the entire frame in a single
operation. The calling instruction can be easily read, and control returned
to it. The return value, if any, of the subroutine can be stored in a
register to be used by the calling process.

Note that the stack generally has a maximum size. If a process tries to
allocate too much memory on the stack (perhaps due to runaway recursion), this
limit might be exceeded, and the process will halt with a _stack overflow_
error.

[^stack-direction]: In some microcontrollers (like the 8051), the stack grows
  up.

[^stack-header]: Other things can go in the stack frame. For example, Java puts
  stack trace information, so that as an exception bubbles up, it can contain
  useful information for debugging. This comes at a cost in the memory size of
  a stack frame.  Also, the compiler generally pre-allocates space for local 
  variables when it creates the stack frame.

## The Heap

Certain structures are not well suited for the stack. Consider an array that
can grow, for example as a base of a Vector or List. When it is created, a
fixed chunk of memory is reserved for it (to hold, say, 512 elements). If it
needs to grow to more than its initial capacity will allow, it will need more
memory. On the stack, it's quite possible that something else will have been
allocated right after it, which means it cannot grow without displacing
something. Structures that have unknown or changing size requirements
necessitate another form of memory management.

Enter the _heap_. This is a large region of memory (generally the vast
majority of the memory available to the process) which can be reserved
piecemeal anywhere that it is not in use. Access to the heap is controlled by
the _allocator_: the process requests a chunk of memory of a given size, the
allocator is responsible for returning an address of memory that is the start
of a chunk of the requested size that is not in use. This means the allocator
has to know which regions of the heap are in use, and quickly find a region not
in use of the requested size. This is much slower and less efficient than
stack allocation, which just requires incrementing the stack pointer!

In order for a process to not run out of heap memory, it will need to free the
heap memory it is no longer using: this is called _deallocation_. Knowing what
variables are no longer in use is hard! So is freeing them efficiently, and in
a way that doesn't leave the heap too fragmented to allocate the memory for any
large variables.

To allocate and deallocate efficiently, the implementations of each are very
intertwined. One of the most foundational and impactful choices when creating
a programming language is the choice of heap memory management. Some, like C
and older editions of C++, require the programmer to manually mark a variable
as no longer in use. Bugs can cause cryptic crashes, memory corruption, and
security vulnerabilities. Some, like Java or Python, use a garbage collector,
freeing the programmer from that responsibility, but use up system resource
and cause occasional garbage-collection hangs. Other languages rely heavily
on the compiler: Objective-C, Swift, and modern C++ insert reference counts,
so that the compiler knows when a variable is no longer being used, and can
insert a deallocation call. Rust variables have an enforced concept of
ownership, and when a variable has no active owner, the compiler can add a
deallocation call here as well.

## ROM 
To start up a computer, a bootstrap program needs to run. After some initial
actions, this bootstrap program loads the main program (generally the
operating system) into RAM. Since RAM is reset when the computer is turned
off, where does this bootstrap program live? There is a special kind of
non-volatile memory called _Read Only Memory_ (_ROM_) which persists its data
even without power.

## Disks and Virtual Memory

Using RAM to contain the program and the data has a couple limitations:

1. When a computer is off, its RAM loses all its data,
2. The program must be small enough to fit into RAM, and
3. The data must be small enough to fit into the rest of the RAM.

Most of the time programs and persistent data live on disks, which we call
_secondary storage_ (RAM is also called _primary storage_). Much as RAM is
much slower but much larger than the registers, disk drives are typically
much slower but much larger than RAM. The kernel (see below) and drivers
abstract the details of how the data is stored and accessed from the process.
For our purposes, we can view secondary storage as an effectively infinite,
yet quite slow, form of memory.

To allow the process to access secondary storage, the kernel provides an
abstraction called _virtual memory_. Virtual memory is a level of indirection
between the memory the process sees, and the physical RAM and secondary
storage. We'll call RAM _physical memory_, and divide it up into chunks of
size 4 kB called _frames_. Each process will be allocated a _logical memory_
space, which is divided into _pages_ (the same size as frames). The process
refers to memory using a logical address (a page number and an offset within
the page), and the _Memory Management Unit_ (_MMU_) of the CPU translates
this into a physical address, and the process transparently accesses the
physical memory. The MMU does this by maintaining a _page table_, which
records if a page has a frame allocated, and if so, which one. This has two
major benefits.

The first benefit is that the logical memory space can be larger than
available (or allotted) physical memory, by using secondary storage. A
portion of the secondary storage is allocated for virtual memory, large
enough to hold the memory allocated. When a page is requested and it maps to
a frame, the frame is accessed as normal. If it doesn't map to a frame, but
there is an unassigned frame, then the unassigned frame is assigned to the
page, and again the process uses the memory as normal. But if there is no
frame available, the kernel (see below) choose a frame that's "quiet" and
_swaps_ it out by saving it to disk, reassigning the frame from its original
page to the new page. When this happens, it's called a _page fault_, and it's
much more expensive than accessing memory normally. If only a small number of
pages are accessed at a given time, there will be few page faults and
execution will be almost as fast as if everything was in RAM. If operating
systems can predict which pages will be used, they can pre-fetch them, so
that the process doesn't notice. However, if pages must be swapped
frequently, then the CPU will be idle a significant amount of time, waiting
for disk reads/writes. This is called _thrashing_, and leads to very poor
performance.

The second benefit is that each running process can have its own logical
memory space, and the MMU will ensure that each process can only access the
allowed part of the physical memory. When one process is less active, it can
be partially or entirely swapped out, freeing more memory for processes that
are running hotter. This way, each process just sees a contiguous dedicated
block of memory, and can allocate and deallocate as if it were the only
process running.

An optimization is possible for processes that share the same program: each
process's pages that map to the program's instructions can point to the same
frames in RAM, so multiple copies of the same program don't need to be
loaded. Similarly, if multiple processes depend on the same library, that
library can be loaded just once in memory.

## Kernel Space and User Space

A modern computer tends to run hundreds of processes at a given time. The
_kernel_ controls these processes: starting, stopping, giving access to CPUs
and RAM. The kernel reserves a big portion of RAM for itself, called _kernel
space_. No other process can touch this RAM. When a process is started, it is
allocated a virtual memory space. This virtual memory is all the process is
allowed to access, and no other process (except the kernel) is allowed to
access it. The kernel is responsible for mapping the virtual memory to RAM,
and swapping pages to disk (discussed last section). This means that
processes can access their memory as if it was a contiguous block dedicated
to them, and the kernel will prevent other processes from writing to and
reading from it.

Kernels ultimately control access to resources. They allocate a certain
amount of RAM to the process, schedule execution on the CPU, and control
access to any IO, like a disk or the network. A process can request access to
this via a _system call_; process execution stops as the kernel performs the
requested action, then returns control to the process with the desired
result. This blocking makes a system call expensive.

Kernels can go even further by stopping processes and restarting them. When
it stops a process it can swap out the entirety of a stopped process's
memory, freeing that RAM for other processes. If it does this, it must also
save the contents of the registers to be restored.

## Inter-process communication

Since in general processes don't share memory, _inter-process communication_
involves the sending process to serialize objects, and write then to a pipe
or other communication channel. The receiver reads from this channel, and
writes a copy of the data to its own memory. This is expensive for large
amounts of data. Since the data is copied, one process will not change data
underneath another process, and the copies may diverge as the two processes
manipulate them.

_Shared memory_ can be used instead of copying the data. Shared memory is a
region of physical memory that multiple processes can access: pages of their
logical memory map to it. This allows very quick inter-process communication,
since only the pointer needs to be transferred. However, shared memory
suffers from the same issues as any other concurrent data access: multiple
processes can simultaneously attempt to access the data. In the best case,
this leads to slowness over lock contention, but it can also lead to data
corruption and undefined behavior.

## Threads

_Threads_ are often described as "lightweight processes". The kernel
allocates resources to the process, but will schedule execution to the
thread. A process's main execution is the _main thread_; a basic process has
only this one thread. However, a process can request additional _kernel
threads_ from the kernel. Each thread will have shared access to the program
data, the heap, and any file/etc resources, but will have its own stack. This
makes starting a new thread cheaper than a new process, because no additional
resources (RAM, etc) have to be procured. It also makes _inter-thread
communication_ very cheap, because (like in the case of shared memory), the
threads have to only pass pointers. As with any shared memory, this is also
dangerous: controlling shared access to data is extremely challenging. Some
solutions synchronize access to data, so that only one thread has access to
it at a time. This will slow down execution, as one thread will have to wait
for another, but it also can lead to deadlock, grinding the threads to a
halt.

The kernel will split CPU time for threads. In the best case, when there are
as many CPUs as threads, each thread can have a dedicated CPU. More often,
the kernel will slice time on CPUs, scheduling and suspending threads
(including threads from different processes). When a thread is suspended, the
associated registers (including stack pointers, program registers, etc) will
have to be saved, to be restored when the thread is re-scheduled. A common case
is when a thread makes a blocking system call: it must wait, so another thread
will use its compute resources.

In addition to kernel threads, the process can create _user threads_ (or _green
threads_), which are unknown to the kernel and managed entirely by the process.
These are very fast to create, and can be optimized for the process's specific
needs. However, the process must perform the complicated management of threads,
including allocating stacks. Since the kernel only allocates CPU time to kernel
threads, user threads all have to share their process's access to the CPU.

## CPU Caches

Computing on data in a register takes 1 cycle (~1 nanosecond). Accessing RAM
takes the equivalent time to ~100 cycles. So every time a CPU needs to fetch
data from (or write data to) RAM, it has to idle for about 100 cycles. With
the architecture we described above, we won't get the benefits of the CPU
speedups of the last decade.

_CPU caches_ are small amounts of fast memory near the CPU to cache recently
used data. Modern architectures use a _cache hierarchy_ of successively larger
and slower caches. The most common hierarchy has three levels, called _L1_,
_L2_, and _L3_. Typical access times and cache sizes are given below.

| Level    | Cycles | Size   |
|----------|-------:|-------:|
| Register | 1      | 8 B    |
| L1       | 4      | 64 kB  |
| L2       | 10     | 256 kB |
| L3       | 40     | 8 MB   |
| RAM      | 100    | 10 GB  |
| SSD      | 10^5   | 1 TB   |

Current processors will often have separate L1 caches for instructions and
data. Also, each level cache will be shared by a different number of cores,
CPUs, etc, and the chip needs to keep track of when to evict data from the
cache, as well as when data might have been modified elsewhere and must be
invalidated. This is a rich and complicated subject, way beyond our scope
here.

Caches are populated with _cache lines_, which are typically
aligned[^aligned-access] 64 byte regions. Accessing any data in the line will
cause the whole line to be cached. If you read a word at the beginning of a
cache line, you can access the rest of the line almost for free. So if you
have an array of 8-byte integers contained in a contiguous block of memory, you
could iterate over it 8 times faster than if the integers were scattered in
memory (if they were boxed Java Longs, for example). Furthermore, the CPU will
try to predict the next data to be read, and pre-fetch that cache line, which
could lead to a 100x speedup.

The term for related data being together in RAM is termed _data locality_. The
effect of caches is so significant that modern data structure and algorithm
design considers data locality (and related concerns) to be on par with big-O
complexity calculations. Loops over flat arrays may beat iterating over object
pointers even if traditional algorithmic analysis says otherwise. The term for
algorithms that are designed to efficiently use cache hierarchies are termed
_cache-oblivious_ algorithms. The non-intuitive name is because _cache-aware_
algorithms are designed for a specific cache hierarchy (with sizes and delays
known), and cache-oblivious algorithms are designed to work well in any
hierarcy.

[^aligned-access]: A chunk of data that is `b` bytes is said to be aligned if
  its address is a multiple of `b`. Aligned data is much faster for the CPU to
  load and use. Thus 8 byte integers should be stored at address like `n * 8`,
  but not `n * 8 - 4`. 64 byte cache lines therefore start at addresses that
  are a multiple of 64.

## Summary

Computation is done on variables in the _registers_, which are very small,
very fast chunks of memory in the CPU. The system has a much larger, but much
slower, region of memory called _RAM_, which must be moved to and from the
registers in order to be worked on. RAM is typically divided into the _stack_
and the _heap_. The stack where variables local in scope to a
subroutine/function are stored; allocation and deallocation are fast and will
not cause memory leaks. The heap is a larger area of memory that much be
managed more explicitly. Allocating on the heap requires knowing what parts of
the heap are in use, and finding space. Different languages deallocate
differently, including manually (C, C++), garbage collecting (Java, Python,
etc), and having the compiler insert the commands automatically (Rust, ARC in
ObjC).

Multiple processes are managed by the kernel, which allocates resources like
RAM and CPU time.  It prevents processes from interfering with each other's
memory using virtual memory, which also allows secondary storage (like disks)
to be used as an extension of RAM.  A process can have multiple threads, which
are "lightweight processes" that share the same memory space, but can parallelize
computation by slicing up time on multiple CPUs.

Because CPUs are so much faster than accessing RAM, a hierarchy of
fast-but-small _cpu caches_ (e.g., _L1_, _L2_, _L3_) are put in or near the
CPU. Data is cached in proximate chunks, so accessing data near previously
accessed data is faster than accessing distant memory.

## Learn More

[J Clark Scott: But How Do It Know?](https://www.amazon.com/But-How-Know-Principles-Computers/dp/0615303765)

[Jacob Schrum on Virtual Memory, and other things](https://www.youtube.com/channel/UCCKhH1p0tj1frvcD70tEyDg/videos)

[Bradlee Speice: Allocations in Rust](https://speice.io/2019/02/understanding-allocations-in-rust.html)

[Why software developers should care about CPU caches](https://medium.com/software-design/why-software-developers-should-care-about-cpu-caches-8da04355bb8a)

[Scott Meyers: CPU Caches and Why You Care](https://youtu.be/WDIkqP4JbkE)
