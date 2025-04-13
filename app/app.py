import secrets
from flask import (
    Flask,
    g,
    render_template,
    redirect,
    abort,
    session,
    url_for,
    request,
    flash
)
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


@app.route('/')
def home():
    return redirect('/tracker')

@app.route('/tracker', methods=['GET','POST'])
def tracker():
    print(request.args)
    # TODO: Validate filter params. If not within available options, use default values.
    goal = request.args.get('goal', 'lose')
    filter = request.args.get('filter', 'weeks')
    with open('data/sample_entries.json') as data_file:
        data = json.load(data_file);
    return render_template('tracker.html', goal=goal, filter=filter, data=data);

if __name__ == '__main__':
    app.run(debug=True, port=5040)