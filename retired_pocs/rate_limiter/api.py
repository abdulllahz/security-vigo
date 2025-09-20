from flask import Flask

app = Flask(__name__)

@app.route('/login')
def login():
    return 'Login!'

@app.route('/signup')
def signup():
    return 'Signup!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')