$(document).ready(function () {
    Array.prototype.contains = function (needle) {
        for (i in this) {
            if (this[i] == needle) return true;
        }
        return false;
    };

    function constructTableHeader(headers) {
        var searchValue = '[var]';
        var tableHeaderTemplate = '<th>' + searchValue + '</th>';

        $('#build_cdm_table thead tr').empty();
        var headerContent = '';
        $.each(headers, function (headerIndex, headerValue) {
            headerContent += tableHeaderTemplate.replace(searchValue, headerValue);
        });
        console.log(headerContent);
        $('#build_cdm_table thead tr').append(headerContent);
    }

    function constructTableContent(pipelines) {
        var searchValue = '[var]';
        var linkValue = '[link]';
        var tableDataSuccessTemplate = '<td class="table-success"><a href="[link]">' + searchValue + '</a></td>';
        var tableDataFailureTemplate = '<td class="table-danger"><a href="[link]">' + searchValue + '</a></td>';
        var tableDataSkippedTemplate = '<td class="table-warning">' + searchValue + '</td>';
        var tableDataAbortedTemplate = '<td class="table-secondary"><a href="[link]">' + searchValue + '</a></td>';
        var tableDataRunningTemplate = '<td class="loading"><i class="fa fa-spinner fa-spin"></i><a href="[link]">   [var]</a></td>';

        $('#build_cdm_table tbody').empty();
        var bodyContent = '';
        $.each(pipelines, function (pipelineIndex, pipeline) {
            bodyContent += '<tr>';
            $.each(pipeline, function (buildIndex, build) {
                var build_status = build['build_status'];
                if (build_status == null) {
                    bodyContent += tableDataSkippedTemplate.replace(searchValue, "NOT BUILT");
                } else if (build_status == 'RUNNING') {
                    tmp = tableDataRunningTemplate.replace(linkValue, build['build_url']);
                    bodyContent += tmp.replace(searchValue, build['build_number']);
                } else if (build_status == 'SUCCESS') {
                    tmp = tableDataSuccessTemplate.replace(linkValue, build['build_url']);
                    bodyContent += tmp.replace(searchValue, build['build_number']);
                } else if (build_status == 'FAILURE') {
                    tmp = tableDataFailureTemplate.replace(linkValue, build['build_url']);
                    bodyContent += tmp.replace(searchValue, build['build_number']);
                } else if (build_status == 'ABORTED') {
                    tmp = tableDataAbortedTemplate.replace(linkValue, build['build_url']);
                    bodyContent += tmp.replace(searchValue, build['build_number']);
                }
            });
            bodyContent += '</tr>';
        });
        $('#build_cdm_table tbody').append(bodyContent);
    }

    function getBranchData(branch, from, size) {
        es_connection = '10.0.65.183:9200/';
        console.log('Fetching data from ' + branch);

        branch = branch.replace('.', '');

        // http://127.0.0.1:5000/build_cdm/master?from=0&size=200

        $.getJSON('build_cdm/' + branch, {from: from, size: size}, function (pipeline_builds) {
            var job_names = Array();
            $.each(pipeline_builds, function (pipelineIndex, pipeline) {
                console.log(pipeline);
                $.each(pipeline, function (buildIndex, build) {
                    var job_name = build['job_name'];
                    if (!job_names.contains(job_name)) job_names.push(job_name);
                });
            });
            console.log(pipeline_builds);
            // constructTableHeader(job_names);
            // constructTableContent(pipelines)
        });
    }

    getBranchData('master', 0, 5);

    $('#branch-selector').change(function () {
            var selectedVal = $("#branch-selector").val();
            getBranchData(selectedVal, 0, 5)
        }
    );
});