#!/usr/bin/env python

"""Jenkins utilities."""

import json
import sys
import time
import traceback
import logging
import requests

from bs4 import BeautifulSoup
from jenkinsapi.jenkins import Jenkins

ES_DB = 'http://10.0.65.183:9200/'


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
    #     self._log.debug('Successfully download ' + last_build_downstream_url + ' page content')
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
    #         self._log.debug(json.dumps(downstream_job.__dict__))
    #         downstream_job_list.append(downstream_job)
    #
    #     self._log.debug(json.dumps([downstream_job.__dict__ for downstream_job in downstream_job_list]))
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
        self._log.debug('Saving to elastic search\n' + json.dumps(pipeline.encodeJSON(), cls=BuildPipelineEncoder))
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url=ES_DB + pipeline.branch + '/' + pipeline.job_name + '/' + str(pipeline.build_number),
                                 data=json.dumps(pipeline.encodeJSON(), cls=BuildPipelineEncoder),
                                 headers=headers)
        self._log.debug(response.json())

    def get_latest_builds(self, job_name):
        """Get the status of a pipeline including it's root and leaf builds.

        :param job_name: the job that we want to get build info
        :return: list of the last 10 builds
        """
        job = self._jenkins_server[job_name]
        build_numbers = list(job.get_build_ids())

        build_pipeline_list = []
        for build_number in build_numbers[0:50]:
            try:
                self._log.debug('----- ' + self.branch + ' ' + job_name +
                                ' ' + str(build_number) + ' -----')
                downstream_page_url = job.baseurl + '/' + str(build_number) + '/downstreambuildview/'
                downstream_page = requests.get(downstream_page_url)
                soup = BeautifulSoup(downstream_page.content, 'html.parser')
                self._log.debug('Successfully download page content')

                build_pipeline = BuildPipeline(branch=self.branch, job_name=job_name, description=job.get_build(build_number).get_description(),
                                               build_number=build_number, build_status=job.get_build(build_number).get_status(),
                                               build_url=job.get_build(build_number).baseurl)

                self._get_latest_builds_util(soup.select('table .pane')[0], build_pipeline.downstream_builds)

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
                build_pipeline.append(DownstreamBuild(job_name, None, None, None))
                return

            build_number = build_info[3]
            build_url = self._jenkins_server[job_name].baseurl + '/' + build_info[3]

            build = None
            if 'counting' in div_element.text.strip():
                build = DownstreamBuild(job_name, build_number, 'RUNNING', build_url)
            else:
                build_status = build_info[11][0:len(build_info[11]) - 1]
                build = DownstreamBuild(job_name, build_number, build_status, build_url)

            build_pipeline.append(build)
        else:
            for div in child_divs:
                self._get_latest_builds_util(div, build_pipeline)


if __name__ == '__main__':
    try:
        jenkins_tracker_42 = JenkinsTracker('http://4-1-builds.corp.rubrik.com/', '41', 'build_cdm.log')
        jenkins_tracker_42.get_latest_builds('Build_CDM')
    except Exception as e:
        traceback.print_exc()
