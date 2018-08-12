$(document).ready(function () {
    var from = 0;
    var size = 40;

    Array.prototype.contains = function (needle) {
        for (i in this) {
            if (this[i] == needle) return true;
        }
        return false;
    };

    function constructTableHeader(pipeline_builds) {
        // Add job names to table
        var job_names = Array();
        $.each(pipeline_builds, function (pipelineIndex, pipeline) {
            if (!job_names.contains(pipeline['job_name'])) job_names.push(pipeline['job_name']);
            $.each(pipeline['downstream_builds'], function (downstreamIndex, downstream_build) {
                if (!job_names.contains(downstream_build['job_name']))
                    job_names.push(downstream_build['job_name']);
            })
        });
        console.log(job_names);
        $.each(job_names, function (index, job_name) {
            var table_row = '<tr><th scope="row">' + job_name + '</th></tr>';
            $('#build_cdm_table').append(table_row);
        });
    }

    function constructTableContent(pipeline_builds) {
        var rows = $('#build_cdm_table tr');
        $.each(pipeline_builds, function (pipelineIndex, pipeline) {
            var pipeline_data = '<td><a href="' + pipeline['build_url'] + '">' + pipeline['build_number'] + '</a>';
            if (pipeline['build_status'] != null && pipeline['build_status'] == 'SUCCESS') {
                pipeline_data = '<td class="table-success"><a href="' + pipeline['build_url'] + '">' + pipeline['build_number'] + '</a>';
            } else if (pipeline['build_status'] != null && pipeline['build_status'] == 'FAILURE') {
                pipeline_data = '<td class="table-danger"><a href="' + pipeline['build_url'] + '">' + pipeline['build_number'] + '</a>';
            } else if (pipeline['build_status'] != null && pipeline['build_status'] == 'ABORTED') {
                pipeline_data = '<td class="table-secondary"><a href="' + pipeline['build_url'] + '">' + pipeline['build_number'] + '</a>';
            }

            if (pipeline['description'] != null) {
                var lines = pipeline['description'].split(' ');
                $.each(lines, function (lineIndex) {
                    if (lines[lineIndex].indexOf('href') != -1) {
                        pipeline_data += '<i><a ' + lines[lineIndex] + '</i></i>'
                    } else {
                        pipeline_data += '<i><pre>' + lines[lineIndex] + '</pre></i>'
                    }
                });
            }
            if (pipeline['started_time'] != null) {
                pipeline_data += '<i><pre><small>' + new Date(pipeline['started_time']).toLocaleString() + '</small></pre></i>'
            }
            pipeline_data += '</td>';
            $("#build_cdm_table tr:nth(0)").append(pipeline_data);


            $.each(pipeline['downstream_builds'], function (downstreamIndex, downstream_build) {
                var searchValue = '[var]';
                var linkValue = '[link]';
                var started_time = '';
                if (downstream_build['started_time'] != null && downstream_build['started_time'].indexOf('counting') == -1) {
                    started_time = '<i><pre><small>' + new Date(downstream_build['started_time']).toLocaleString() + '</small></pre></i>';
                } else {
                    started_time = '<i><pre><small>' + downstream_build['started_time'] + '</small></pre></i>';
                }

                // Add build info to table
                var tableDataSuccessTemplate = '<td class="table-success"><a href="[link]">' + searchValue + '</a>' + started_time + '</td>';
                var tableDataFailureTemplate = '<td class="table-danger"><a href="[link]">' + searchValue + '</a>' + started_time + '</td>';
                var tableDataSkippedTemplate = '<td class="table-warning">' + searchValue + '</td>';
                var tableDataAbortedTemplate = '<td class="table-secondary"><a href="[link]">' + searchValue + '</a>' + started_time + '</td>';
                var tableDataRunningTemplate = '<td class="loading"><i class="fa fa-spinner fa-spin"></i><a href="[link]">   [var]</a>' + started_time + '</td>';

                // var downstream_data = '<td>' + downstream_build['build_number'] + '</td>';
                // $("#build_cdm_table tr:nth(" + (downstreamIndex + 1) + " )").append(downstream_data);

                var build_status = downstream_build['build_status'];
                if (build_status == null) {
                    tableDataSkippedTemplate = tableDataSkippedTemplate.replace(searchValue, "NOT BUILT");
                    $("#build_cdm_table tr:nth(" + (downstreamIndex + 1) + " )").append(tableDataSkippedTemplate);
                } else if (build_status == 'RUNNING') {
                    tmp = tableDataRunningTemplate.replace(linkValue, downstream_build['build_url']);
                    tmp = tmp.replace(searchValue, downstream_build['build_number']);
                    $("#build_cdm_table tr:nth(" + (downstreamIndex + 1) + " )").append(tmp);
                } else if (build_status == 'SUCCESS') {
                    tmp = tableDataSuccessTemplate.replace(linkValue, downstream_build['build_url']);
                    tmp = tmp.replace(searchValue, downstream_build['build_number']);
                    $("#build_cdm_table tr:nth(" + (downstreamIndex + 1) + " )").append(tmp);
                } else if (build_status == 'FAILURE') {
                    tmp = tableDataFailureTemplate.replace(linkValue, downstream_build['build_url']);
                    tmp = tmp.replace(searchValue, downstream_build['build_number']);
                    $("#build_cdm_table tr:nth(" + (downstreamIndex + 1) + " )").append(tmp);
                } else if (build_status == 'ABORTED') {
                    tmp = tableDataAbortedTemplate.replace(linkValue, downstream_build['build_url']);
                    tmp = tmp.replace(searchValue, downstream_build['build_number']);
                    $("#build_cdm_table tr:nth(" + (downstreamIndex + 1) + " )").append(tmp);
                }
            })
        });
    }

    function getBuildCDMData(branch, createNewTable) {
        if (createNewTable == true) from = 0;
        branch = branch.replace('.', '').toLowerCase();
        console.log('Fetching data from ' + branch + " branch starting from " + from);

        $.getJSON('build_cdm/' + branch, {from: from, size: size}, function (pipeline_builds) {
            if (createNewTable == true) constructTableHeader(pipeline_builds);
            constructTableContent(pipeline_builds);
            from += size;
        });
    }

    getBuildCDMData('master', true);

    $('#build_cdm_table').on('scroll', function () {
        if ($(this).scrollLeft() + $(this).innerWidth() == $(this)[0].scrollWidth) {
            console.log('500px away from eight end. Loading more data');
            var branch = $("#branch-selector").val();
            getBuildCDMData(branch, false);
        }
    });

    $('#branch-selector').change(function () {
            var branch = $("#branch-selector").val();
            $('#build_cdm_table').empty();
            getBuildCDMData(branch, true);
        }
    );
});
