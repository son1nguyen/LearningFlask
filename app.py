#!/usr/bin/env python

import json

import requests
from flask import Flask, render_template, jsonify, request, send_file

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


@app.route('/download/<branch>/<job_name>/<build_number>', methods=['GET'])
def pipeline(branch, job_name, build_number):
    # /home/ubuntu/builds/master/Build_CDM/4515/archive.zip
    return send_file(filename_or_fp='/home/ubuntu/builds/{}/{}/{}/archive.zip'.format(branch, job_name, build_number),
                     as_attachment=True, attachment_filename='archive.zip')


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
    print(str(len(response.json()['hits']['hits'])) + ' records found')

    result = []
    for hit in response.json()['hits']['hits']:
        result.append(hit['_source'])

    return jsonify(result)


@app.route('/qualify_cdm')
def about():
    return render_template('qualify_cdm.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
