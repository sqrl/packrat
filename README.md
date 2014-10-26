Packrat
=======

A networked file cache, implemented in python. Like the eponymous rodent,
packrat will discard older files in favor of newer, shinier ones.


Running Instructions
====================

Copy `${PACKRAT_ROOT}/etc/packrat.ini.example` to
`${PACKRAT_ROOT}/etc/packrat.ini` and Tweak parameters. Invoke packrat
with `make run`. This will create a virtual environment with packrat's
dependencies and start the server.


Web API
=======

*TODO*


Outstanding Issues
==================

 * `packrat.ini` is presently ignored.
 * Caching policy is currently LRU. Some optimizations could be made
 by discarding slightly younger but larger files.
 * Caching is currently in memory.
 * Files will first be stored in a single directory, which is not the
 most scalable solution.
 * Currently single threaded for easier concurrency logic.
