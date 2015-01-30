from configparser import ConfigParser
from sys import argv, exit

from flask import abort, Flask, render_template, request, send_file

from file_cache import FileCache


app = Flask(__name__)


@app.route('/<key>', methods=['GET', 'POST'])
def set_or_get(key=None):
    """
    Route for uploading a file.  Expects a key parameter.
    """
    # TODO: What if a user uploads a file with a blank filename?
    if not key:
        abort(400)
    if request.method == 'POST':
        print(request.files['file'])
        return cache.store_file(key, request.files['file'])

    file = cache.get_file(key)
    if not file:
        abort(404)
    return send_file(file[0], as_attachment=True, attachment_filename=file[1])


@app.route('/')
def status_screen():
    files, total_size, max_size = cache.status()
    return render_template(
        'packrat.html',
        files=files,
        total_size=total_size,
        max_size=max_size)


if __name__ == '__main__':
    if len(argv) != 2:
        exit("Usage: python packrat.py <config.ini>")
    config = ConfigParser()
    config.read(argv[1])
    try:
        host = config['packrat'].get('host')
        port = config['packrat'].get('port')
        debug = config['packrat'].getboolean('debug', True)
        cache_max_size = config['packrat'].getint('cache_size')
        cache_path = config['packrat'].get('storage_location')
        app.config['MAX_CONTENT_LENGTH'] = cache_max_size
    except KeyError:
        print("Invalid or non-existent config file: " + argv[1])
        raise
    cache = FileCache(cache_max_size, cache_path)
    app.run(host=host, port=int(port), debug=debug, use_reloader=False)
