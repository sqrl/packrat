Packrat
=======

A networked file cache, implemented in Python. Like the eponymous rodent,
packrat will discard older files in favor of newer, shinier ones.


Running Instructions
====================

Copy `${PACKRAT_ROOT}/etc/packrat.ini.example` to
`${PACKRAT_ROOT}/etc/packrat.ini` and Tweak parameters. Invoke packrat
with `make run`. This will create a virtual environment with packrat's
dependencies and start the server.


Web API
=======

Assuming that packrat is running on http://127.0.0.1:5050, the following
is a a web API for packrat.

 * `GET http://127.0.0.1:5050/` Shows a status page and a web interface
 for uploading a file.
 * `GET http://127.0.0.1:5050/<key>` Retrieves a previously uploaded file.
 The file will be sent as a `Content-Disposition: attachment` and a file
 name with which it was uploaded.
 * `POST http://127.0.0.1:5050/<key>` Attempts to post a file.  The
 request must be sent with a `enctype` of `multipart/form-data` and the
 file must be included as `form-data` with name `file`.  It will return
 a json document whose 'success' field will be true if successful.  If
 unsuccessful, the 'error' and 'message' fields contain more information.
 * `GET http://127.0.0.1:5050/exists/<key>` Checks for the existence of
 a key in the cache. Returns a json result of the form
 `{ "present": true|false }`

A Python example of uploading a picture `cat.png` with the key `cat`
using the  [requests library](http://docs.python-requests.org/) looks
like this:

    base_url = "http://127.0.0.1:5050/"
    with open("cat.png", 'rb') as file:
        key = 'cat'
        r = requests.post(base_url + key, files={'file': file})
        print(r.text) # Will print a json result

You can retrieve the file uploaded in the above example (assuming it
hasn't been cache evicted yet) by issuing a `GET` for
`http://127.0.0.1:5050/cat`


Outstanding Issues
==================

 * Caching policy is currently LRU. Some optimizations could be made
 by discarding slightly younger but larger files.
 * Files will first be stored in a single directory, which is not the
 most scalable solution.
 * Currently single threaded for easier concurrency logic.
