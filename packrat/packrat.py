from io import BytesIO
from os import getenv

from flask import abort, Flask, render_template, request, send_file

from memorycache import MemoryCache

app = Flask(__name__)
cache = MemoryCache()

@app.route('/<key>', methods=['GET', 'POST'])
def upload(key=None):
  """
  Route for uploading a file.  Expects a key parameter.
  """
  # TODO: What if a user uploads a file with a blank filename?
  if not key:
    abort(400)
  if request.method == 'POST':
    print(request.files['file'])
    feh = cache.store_file(key, request.files['file'])
    return feh

  file = cache.get_file(key)
  if not file:
    abort(404)
  return send_file(BytesIO(file[1]), as_attachment=True, attachment_filename=file[0])

@app.route('/')
def status_screen():
  files, total_size, max_size = cache.status()
  return render_template(
    'packrat.html',
    files=files,
    total_size=total_size,
    max_size=max_size)


if __name__ == '__main__':
  host = getenv('WEB_HOST', "0.0.0.0")
  port = getenv('WEB_PORT', "5000")
  app.run(host=host, port=int(port), debug=True)
