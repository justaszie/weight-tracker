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
import utils
from datetime import date

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
        data = json.load(data_file)
        for row in data['entries']:
            row['week_start'] = date.fromisoformat(row['week_start'])
    return render_template('tracker.html', goal=goal, filter=filter, data=data)

app.jinja_env.filters['signed_amt_str'] = utils.to_signed_amt_str

if __name__ == '__main__':
    app.run(debug=True, port=5040)
