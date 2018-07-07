import json

import requests
from elasticsearch_dsl import connections


class DownstreamBuild:

    def __init__(self, job_name, build_number, build_status, build_url):
        self.job_name = job_name
        self.build_number = build_number
        self.build_status = build_status
        self.build_url = build_url

    def encodeJSON(self):
        return self.__dict__


class BuildPipeline:

    def __init__(self, branch, job_name=None, description=None,
                 build_number=None, build_status=None, build_url=None):
        self.branch = branch
        self.job_name = job_name
        self.description = description
        self.build_number = build_number
        self.build_status = build_status
        self.build_url = build_url
        self.downstream_builds = []

    def encodeJSON(self):
        return dict(branch=self.branch, job_name=self.job_name, description=self.description,
                    build_number=self.build_number, build_status=self.build_status, build_url=self.build_url,
                    downstream_builds=self.downstream_builds)


class BuildPipelineEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'encodeJSON'):
            return obj.encodeJSON()
        else:
            return json.JSONEncoder.default(self, obj)


if __name__ == '__main__':
    ES_DB = 'http://10.0.65.183:9200/'
    connections.create_connection(hosts=[ES_DB])
    print(connections.get_connection().cluster.health())

    pipeline = BuildPipeline(branch='42', job_name='Build_CDM', description='say something',
                             build_number=3, build_status='SUCCESS', build_url='http://4-1-builds.corp.rubrik.com/job/Build_CDM/1')
    pipeline.downstream_builds.append(DownstreamBuild('Build_CDM_AMI', None, None, None))
    pipeline.downstream_builds.append(DownstreamBuild('Build_CDM_Edge_Esx', None, None, None))

    print(json.dumps(pipeline.encodeJSON(), cls=BuildPipelineEncoder))

    headers = {'Content-Type': 'application/json'}
    response = requests.post(url='http://10.0.65.183:9200/pipelines/build_cdm/' +
                                 pipeline.branch + '_' + pipeline.job_name + '_' + pipeline.build_number,
                             data=json.dumps(pipeline.encodeJSON(), cls=BuildPipelineEncoder),
                             headers=headers)

    print(response.json())

    # doc = {
    #     "sort": {
    #         "build_number": {
    #             "order": "desc"
    #         }
    #     },
    #     "from": 0,
    #     "size": 2
    # }
    # headers = {'Content-Type': 'application/json'}
    # response = requests.post(url='http://192.168.162.56:9200/pipelines/build_cdm/', data=json.dumps(doc), headers=headers)
    # print(response.status_code)
    # print(response.json()['hits']['hits'][0]['_source']['build_number'])
