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

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

@app.route('/tracker', methods=['GET'])
def show_summary():
    return render_template('tracker', goal='lose', filter='weeks');

if __name__ == '__main__':
    app.run(debug=True, port=5040)