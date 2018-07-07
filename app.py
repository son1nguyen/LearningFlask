import ast
import json

import requests
from flask import Flask, render_template, jsonify, request

import jenkins_tracker

app = Flask(__name__)

headers = {'Content-Type': 'application/json'}
build_cdm_payload = {
    'sort': {
        'build_number': {
            'order': 'desc'
        }
    },
    'from': 'start_from',
    'size': 'number_of_builds'
}


@app.route('/')
@app.route('/build_cdm')
def hello_world():
    return render_template('build_cdm.html')


# @app.route('/build_cdm/<branch>', methods=['GET'])
# def pipeline(branch='master'):
#     print('Getting ' + branch + ' data')
#     file = open(branch + '.txt', 'r')
#     content = ast.literal_eval(file.read())
#     file.close()
#     return jsonify(content)


@app.route('/build_cdm/<branch>', methods=['GET'])
def get_build_cdm(branch='master'):
    start_from = int(request.args['from'])
    number_of_builds = int(request.args['size'])

    build_cdm_payload['from'] = start_from
    build_cdm_payload['size'] = number_of_builds
    print(build_cdm_payload)

    # Construct post request: /42/Build_CDM/_search
    response = requests.post(url=jenkins_tracker.ES_DB + branch + '/Build_CDM/_search',
                             data=json.dumps(build_cdm_payload),
                             headers=headers)
    print(json.dumps(response.json()))

    result = []
    for hit in response.json()['hits']['hits']:
        result.append(hit['_source'])
    print(json.dumps(result))

    return jsonify(result)


@app.route('/qualify_cdm')
def about():
    return render_template('qualify_cdm.html')


if __name__ == '__main__':
    app.run(debug=True)
