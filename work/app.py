from flask import Flask, request

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    print("受信データ:", data)
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)