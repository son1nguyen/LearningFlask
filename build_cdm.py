import time
import traceback

from jenkins_tracker import JenkinsTracker

if __name__ == '__main__':
    try:
        while True:
            # try:
            #     jenkins_tracker_master = JenkinsTracker('http://master-builds.corp.rubrik.com/', '/home/ubuntu/build_cdm.log')
            #     pipeline_content = jenkins_tracker_master.get_latest_builds('Build_CDM').replace('null', 'None')
            #     print(pipeline_content)
            #     jenkins_tracker_master.write_result_to_file('master.txt', pipeline_content)
            # except Exception as e:
            #     traceback.print_exc()

            try:
                jenkins_tracker_42 = JenkinsTracker('http://4-2-builds.corp.rubrik.com/', 42, 'build_cdm.log')
                pipeline_content = jenkins_tracker_42.get_latest_builds('Build_CDM').replace('null', 'None')
                print(pipeline_content)
                jenkins_tracker_42.write_result_to_file('42.txt', pipeline_content)
            except Exception as e:
                traceback.print_exc()

            # try:
            #     jenkins_tracker_41 = JenkinsTracker('http://4-1-builds.corp.rubrik.com/', '/home/ubuntu/build_cdm.log')
            #     pipeline_content = jenkins_tracker_41.get_latest_builds('Build_CDM').replace('null', 'None')
            #     print(pipeline_content)
            #     jenkins_tracker_41.write_result_to_file('41.json', pipeline_content)
            # except Exception as e:
            #     traceback.print_exc()

            # Sleep for 60 mins
            print("Start sleeping for 60 mins")
            time.sleep(60 * 60)

    except Exception as e:
        traceback.print_exc()
