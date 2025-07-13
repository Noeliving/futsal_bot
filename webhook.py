from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/futsal', methods=['POST'])
def futsal_webhook():
    data = request.get_json()
    # Aquí procesas lo que te llegue
    print(data)
    # Llama aquí a tu lógica, o importa y ejecuta tu script principal
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
