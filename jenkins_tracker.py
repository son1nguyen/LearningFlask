#!/usr/bin/env python

"""Jenkins utilities."""
import json
import logging
import os
import time
import traceback
from datetime import datetime
from os.path import expanduser

import requests
import wget
from bs4 import BeautifulSoup
from jenkinsapi.jenkins import Jenkins
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)

ES_DB = 'http://10.0.65.183:9200/'


class DownstreamBuild:

    def __init__(self, job_name, build_number, build_status, build_url, started_time):
        self.job_name = job_name
        self.build_number = build_number
        self.build_status = build_status
        self.build_url = build_url
        self.started_time = started_time

    def encodeJSON(self):
        return self.__dict__


class BuildPipeline:

    def __init__(self, branch, job_name=None, description=None,
                 build_number=None, build_status=None, build_url=None,
                 download_url=None, started_time=None):
        self.branch = branch
        self.job_name = job_name
        self.description = description
        self.build_number = build_number
        self.build_status = build_status
        self.build_url = build_url
        self.download_url = download_url
        self.started_time = started_time
        self.downstream_builds = []

    def encodeJSON(self):
        return dict(branch=self.branch, job_name=self.job_name, description=self.description,
                    build_number=self.build_number, build_status=self.build_status,
                    build_url=self.build_url, download_url=self.download_url,
                    started_time=self.started_time, downstream_builds=self.downstream_builds)


class BuildPipelineEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'encodeJSON'):
            return obj.encodeJSON()
        else:
            return json.JSONEncoder.default(self, obj)


class JenkinsTracker:

    def __init__(self, jenkins_url, branch, log_file_name):
        """Constructor."""
        self._jenkins_url = jenkins_url
        self.branch = branch
        self._jenkins_server = Jenkins(jenkins_url)
        self._log = logging.getLogger(__name__)
        logging.basicConfig(filename=log_file_name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(processName)s]%(threadName)s: "
            "%(levelname)-01s: %(module)s::%(funcName)s:"
            "%(lineno)-02s: %(message)s",
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        handler.setFormatter(formatter)
        self._log.addHandler(handler)
        self._log.setLevel(logging.DEBUG)

    def write_result_to_file(self, file_path, content):
        file = open(file_path, 'w')
        file.write(content)
        file.close()

    # def get_last_three_pipelines(self, job_name):
    #     job = self._jenkins_server[job_name]
    #     last_build = job.get_last_completed_build()
    #     last_build_downstream_url = last_build.baseurl + '/downstreambuildview/'
    #     downstream_page = requests.get(last_build_downstream_url)
    #     soup = BeautifulSoup(downstream_page.content, 'html.parser')
    #     print('Successfully download ' + last_build_downstream_url + ' page content')
    #
    #     downstream_job_names = []
    #     downstream_job_list = []
    #     self._get_leaf_job_names(soup.select('table .pane')[0], downstream_job_names)
    #     for downstream_job_name in downstream_job_names:
    #         downstream_job = PipelineBuild(downstream_job_name)
    #         build_ids = list(self._jenkins_server[downstream_job_name].get_build_ids())
    #         for build_id in build_ids[:3]:
    #             build = self._jenkins_server[downstream_job_name].get_build(build_id)
    #             downstream_job.build_ids.append(build.buildno)
    #             downstream_job.build_status.append(build.get_status())
    #             downstream_job.build_urls.append(build.baseurl)
    #         print(json.dumps(downstream_job.__dict__))
    #         downstream_job_list.append(downstream_job)
    #
    #     print(json.dumps([downstream_job.__dict__ for downstream_job in downstream_job_list]))
    #
    # def _get_leaf_job_names(self, div_element, downstream_job_names):
    #     child_divs = list(div_element.find_all('div', recursive=False))
    #     if not child_divs:
    #         build_info = div_element.text.strip().split(' ')
    #         job_name = build_info[0]
    #         downstream_job_names.append(job_name)
    #     else:
    #         for div in child_divs:
    #             self._get_leaf_job_names(div, downstream_job_names)

    def save_pipeline_result(self, pipeline):
        print('Saving to elastic search\n' + json.dumps(pipeline.encodeJSON(), cls=BuildPipelineEncoder))
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            url=ES_DB + pipeline.branch + '/' + pipeline.job_name + '/' + str(pipeline.build_number),
            data=json.dumps(pipeline.encodeJSON(), cls=BuildPipelineEncoder),
            headers=headers)
        print(response.json())

    def get_latest_builds(self, job_name):
        """Get the status of a pipeline including it's root and leaf builds.

        :param job_name: the job that we want to get build info
        :return: list of the last 10 builds
        """
        job = self._jenkins_server[job_name]
        build_numbers = list(job.get_build_ids())

        build_pipeline_list = []
        for build_number in build_numbers[0:20]:
            try:
                print('----- ' + self.branch + ' ' + job_name +
                      ' ' + str(build_number) + ' -----')
                downstream_page_url = job.baseurl + '/' + str(build_number) + '/downstreambuildview/'
                downstream_page = requests.get(downstream_page_url)
                soup = BeautifulSoup(downstream_page.content, 'html.parser')
                print('Successfully download page content')

                root_job = job.get_build(build_number)
                build_pipeline = BuildPipeline(branch=self.branch, job_name='Build_CDM',
                                               description=root_job.get_description(),
                                               build_number=build_number, build_status=root_job.get_status(),
                                               build_url=root_job.baseurl,
                                               started_time=root_job.get_timestamp().strftime("%b %d %H:%M:%S %Z %Y"))

                self._get_latest_builds_util(soup.select('table .pane')[0], build_pipeline.downstream_builds)
                score = 0
                if build_pipeline.build_status == 'SUCCESS':
                    for downstream_build in build_pipeline.downstream_builds:
                        if ('Crystal_Acceptance' in downstream_build.job_name or
                            'Edge_Fileset_Smoke_Aws' in downstream_build.job_name) and \
                                downstream_build.build_status == 'SUCCESS':
                            score += 1

                if score >= 1:
                    home_dir = expanduser("~")

                    print 'Build {} is a good build with score +{}'.format(build_pipeline.build_number, score)
                    stored_dir = '{}/builds/{}/{}/{}'.format(home_dir, build_pipeline.branch,
                                                             build_pipeline.job_name, build_pipeline.build_number)
                    artifact_url = '{}/artifact/*zip*/archive.zip'.format(build_pipeline.build_url)
                    artifact_file = Path(stored_dir + '/archive.zip')
                    if artifact_file.exists() is False:
                        print 'Store artifact {} in {}'.format(artifact_url, artifact_file.as_posix())
                        # subprocess.check_output(['wget', '-P', stored_dir, artifact_url])
                        os.makedirs(stored_dir)
                        print wget.download(url=artifact_url, out=stored_dir)
                    else:
                        print 'Artifact already exists in {}'.format(stored_dir)

                    build_pipeline.download_url = '/download/{}/{}/{}'.format(build_pipeline.branch,
                                                                              build_pipeline.job_name,
                                                                              build_pipeline.build_number)
                self.save_pipeline_result(build_pipeline)
            except Exception as e:
                traceback.print_exc()

    def _get_latest_builds_util(self, div_element, build_pipeline):
        """
        :param div_element:
        :type Tag
        :param build_pipeline_list:
        :type list
        :return:
        """

        child_divs = list(div_element.find_all('div', recursive=False))
        if not child_divs:
            build_info = div_element.text.strip().split(' ')
            job_name = build_info[0]

            if 'NOT_BUILT' in div_element.text.strip():
                build_pipeline.append(DownstreamBuild(job_name, None, None, None, None))
                return

            build_number = build_info[3]
            build_url = self._jenkins_server[job_name].baseurl + '/' + build_info[3]

            build = None
            if 'counting' in div_element.text.strip():
                started_time = div_element.text.strip().split('(')[1].split(')')[0]
                build = DownstreamBuild(job_name, build_number, 'RUNNING', build_url, started_time)
            else:
                started_time = div_element.text.strip().split('(')[1][4:28]
                build_status = build_info[11][0:len(build_info[11]) - 1]
                build = DownstreamBuild(job_name, build_number, build_status, build_url, started_time)

            build_pipeline.append(build)
        else:
            for div in child_divs:
                self._get_latest_builds_util(div, build_pipeline)


if __name__ == '__main__':

    try:
        while True:
            print('START POLLING DATA AT ' + str(datetime.now()))
            try:
                jenkins_tracker_master = JenkinsTracker('http://cdm-builds.corp.rubrik.com/', 'master',
                                                        'build_cdm.log')
                jenkins_tracker_master.get_latest_builds('Build_CDM')
            except Exception as e:
                traceback.print_exc()

            try:
                jenkins_tracker_42 = JenkinsTracker('http://cdm-builds.corp.rubrik.com/', '42', 'build_cdm.log')
                jenkins_tracker_42.get_latest_builds('Build_CDM_4.2')
            except Exception as e:
                traceback.print_exc()

            try:
                jenkins_tracker_41 = JenkinsTracker('http://cdm-builds.corp.rubrik.com/', '41', 'build_cdm.log')
                jenkins_tracker_41.get_latest_builds('Build_CDM_4.1')
            except Exception as e:
                traceback.print_exc()

            # Sleep for 60 mins
            print("Start sleeping for 20 mins")
            time.sleep(20 * 60)

    except Exception as e:
        traceback.print_exc()
