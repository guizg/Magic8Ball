from flask import Flask, request, jsonify, Response
import json
from random import randint

app = Flask(__name__)
@app.route('/')
def hello_world():
	return 'Hello, World!'


@app.route('/magicball', methods = ['GET'])
def magic():
    
    if request.method == 'GET':
        pergunta = json.loads(request.data)['pergunta']
        # print(pergunta)

        primeira = pergunta.split()[0]

        if primeira == "quantos" or primeira == "Quantos":
            r = str(randint(0,100))
            return jsonify({"answer": r})

        donno = ["qual", "Qual", "quais", "Quais", "como", "Como", "por", "Por"]

        if primeira in donno:
            return jsonify({"answer": "NAO SEI, SORRY ;("})

        if len(pergunta)%2 == 0:
            return jsonify({"answer": "SIM"})
        else:
            return jsonify({"answer": "NAO"})


@app.route('/healthcheck', methods = ['GET'])
def healthcheck():
	return Response(status=200)
	
app.run(host='0.0.0.0', port=5000, debug=False)