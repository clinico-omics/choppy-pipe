# -*- coding: utf-8 -*-
"""
    choppy.core.cromwell
    ~~~~~~~~~~~~~~~~~~~~

    Module to interact with Cromwell Server.

    :copyright: © 2019 by the Choppy team.
    :license: AGPL, see LICENSE.md for more details.
"""

from __future__ import unicode_literals
import logging
import json
import requests
import datetime
import sys
from choppy.config import get_global_config
from choppy import exit_code

from requests.utils import quote
from ratelimit import rate_limited

global_config = get_global_config()
module_logger = logging.getLogger(__name__)
ONE_MINUTE = 60


class Cromwell:
    """ Module to interact with Cromwell Pipeline workflow manager. 

        Example usage:
        cromwell = Cromwell()
        cromwell.start_workflow('VesperWorkflow', {'project_name': 'Vesper_Anid_test'}) # noqa

        Generated json payload:
        {"VesperWorkflow.project_name":"Vesper_Anid_test"}
    """

    def __init__(self, host='localhost', port=8000, auth=None):
        self.host = host
        self.port = port
        self.auth = auth

        self.url = 'http://' + host + ':' + \
            str(self.port) + '/api/workflows/v1'
        self.url2 = 'http://' + host + ':' + \
            str(self.port) + '/api/workflows/v2'
        self.logger = logging.getLogger(__name__)
        self.logger.debug('URL:{}'.format(self.url))

        v_url = "http://{}:{}/engine/v1/version".format(host, str(self.port))

        try:
            self.long_version = json\
                .loads(requests
                       .get(v_url, auth=self.auth)
                       .content)['cromwell']
        except (requests.ConnectionError, ValueError) as e:
            msg = "Unable to connect to {}:{}:\n{}".format(
                self.host, self.port, str(e))
            print_log_exit(msg)

        self.short_version = int(self.long_version.split('-')[0])
        self.cached_metadata = {}

    def get(self, rtype, workflow_id=None, headers=None, v2=False):
        """A generic get request function.

        :param rtype: a type of request such as 'abort' or 'status'.
        :param workflow_id: The ID of a workflow if get request requires one.
        :param headers: Optional headers for request.
        :return: json of request response
        """
        url = self.url if not v2 else self.url2
        if workflow_id:
            workflow_url = url + '/' + workflow_id + '/' + rtype
        else:
            workflow_url = url + '/' + rtype
        self.logger.debug("GET REQUEST:{}".format(workflow_url))
        if headers:
            r = requests.get(workflow_url, headers=headers, auth=self.auth)
        else:
            r = requests.get(workflow_url, auth=self.auth)
        return json.loads(r.content)

    def post(self, rtype, workflow_id=None):
        """A generic post request function.

        :param rtype: a type of request such as 'abort' or 'status'.
        :param workflow_id: The ID of a workflow if get request requires one.
        :return: json of request response
        """
        if workflow_id:
            workflow_url = self.url + '/' + workflow_id + '/' + rtype
        else:
            workflow_url = self.url + '/' + rtype
        self.logger.debug("POST REQUEST:{}".format(workflow_url))
        r = requests.post(workflow_url, auth=self.auth)
        return json.loads(r.text)

    def patch(self, rtype, workflow_id, payload, headers):
        """Make a patch request to the Cromwell server.

        :param rtype: the request type (ex: label)
        :param workflow_id: the workflow id for the workflow to patch
        :param payload: the json data to patch.
        :param headers: payload headers.
        :return: request result
        """
        workflow_url = self.url + '/' + workflow_id + '/' + rtype
        self.logger.debug("POST REQUEST:{}".format(workflow_url))
        tries = 4
        while tries != 0:
            r = requests.patch(url=workflow_url, data=payload,
                               headers=headers, auth=self.auth)
            if r.status_code == 200:
                logging.info('{} request succeeded.'.format(rtype))
                tries = 0
            else:
                logging.warning("{} failed. Error {}: {}".format(
                    rtype, r.status_code, json.loads(r.text)['message']))
                logging.info("Retrying...")
                tries -= tries
        # Should return none only if patch request fails.
        return r

    def restart_workflow(self, workflow_id, disable_caching=False):
        """Restart a workflow given an existing workflow id.

        :param workflow_id: the id of the existing workflow
        :param disable_caching: If true, do not use cached data to restart the workflow. # noqa
        :return: Request response json.
        """
        metadata = self.query_metadata(workflow_id)
        processed_labels = self.process_metadata_label(metadata)

        try:
            workflow_input = metadata['submittedFiles']['inputs']
            wdl = metadata['submittedFiles']['workflow']
            self.logger.info(
                'Workflow restarting with inputs: {}'.format(workflow_input))
            restarted_wf = self.jstart_workflow(wdl, workflow_input,
                                                wdl_string=True, v2=True,
                                                disable_caching=disable_caching,
                                                custom_labels=processed_labels)
            return restarted_wf
        except KeyError:
            return None

    @staticmethod
    def getCalls(status, call_arr, full_logs=False, limit_n=3):
        filteredCalls = list(
            filter(lambda c: c[1][0]['executionStatus'] == status, call_arr.items()))
        filteredCalls = map(lambda c: (c[0], c[1][0]), filteredCalls)

        def parse_logs(call_tuple):
            call = call_tuple[1]
            task = call_tuple[0]

            log = {}
            try:
                log['stdout'] = {
                    'name': call['stdout'], 'label': task + "." + str(call["shardIndex"]) + ".stdout"}
            except KeyError as e:
                log['stddout'] = e
            try:
                log['stderr'] = {
                    'name': call['stderr'], 'label': task + "." + str(call["shardIndex"]) + ".stderr"}
            except KeyError as e:
                log['stderr'] = e
            if full_logs:
                try:
                    with open(call['stdout'], 'r') as stdout_in:
                        log['stdout']['log'] = stdout_in.read()
                except IOError as e:
                    log['stdout']['log'] = e
                try:
                    with open(call['stderr'], 'r') as stderr_in:
                        log["stderr"]['log'] = stderr_in.read()
                except IOError as e:
                    log["stderr"]['log'] = e
            return log

        return map(lambda c: parse_logs(c), filteredCalls[:limit_n])

    def explain_workflow(self, workflow_id, include_inputs=True):
        def assign(sdict, ddict, key):
            try:
                ddict[key] = sdict[key]
            except KeyError as e:
                ddict[key] = e
        result = self.query_metadata(workflow_id)
        explain_res = {}
        additional_res = {}
        stdout_res = {}

        if result is not None:
            assign(result, explain_res, 'status')
            assign(result, explain_res, 'id')
            assign(result, explain_res, 'workflowRoot')
            if explain_res["status"] == "Failed":
                stdout_res["failed_jobs"] = Cromwell.getCalls('Failed', result['calls'],
                                                              full_logs=True)

            elif explain_res["status"] == "Running":
                explain_res["running_jobs"] = Cromwell.getCalls(
                    'Running', result['calls'])

            if include_inputs:
                additional_res["inputs"] = result["inputs"]
        else:
            print("Workflow not found.")

        return (explain_res, additional_res, stdout_res)

    def start_workflow(self, wdl_file, workflow_name, workflow_args, dependencies=None):
        """Start a workflow using a dictionary of arguments.

        :param wdl_file: workflow description file.
        :param workflow_name: the name of the workflow (ex: gatk).
        :param workflow_args: A dictionary of workflow arguments.
        :param dependencies: The subworkflow zip file. Optional.
        :return: Request response json.
        """
        json_workflow_args = {}
        for key in workflow_args.keys():
            json_workflow_args[workflow_name + "." + key] = workflow_args[key]
        json_workflow_args['user'] = global_config.getuser()
        args_string = json.dumps(json_workflow_args)

        print("args_string:")
        print(args_string)

        files = {'wdlSource': (wdl_file, open(wdl_file, 'rb'), 'application/octet-stream'),
                 'workflowInputs': ('report.csv', args_string, 'application/json')}

        if dependencies:
            # add dependency as zip file
            files['wdlDependencies'] = (dependencies, open(
                dependencies, 'rb'), 'application/zip')
        r = requests.post(self.url, files=files, auth=self.auth)
        return json.loads(r.text)

    def jstart_workflow(self, wdl_file, json_file, dependencies=None,
                        wdl_string=False, disable_caching=False,
                        extra_options=None, custom_labels={}, v2=False):
        """Start a workflow using json file for argument inputs.

        :param wdl_file: Workflow description file or WDL string (specify wdl_string if so). # noqa
        :param json_file: JSON file or JSON string containing arguments.
        :param dependencies: The subworkflow zip file. Optional.
        :param wdl_string: If the wdl_file argument is actually a string. Optional. # noqa
        :param disable_caching: Disable Cromwell cacheing.
        :param extra_options: additional options to be passed to Cromwell.
        :return: Request response json.
        """

        if not json_file.startswith("{"):
            with open(json_file) as fh:
                args = json.load(fh)
            fh.close()
            args['user'] = global_config.getuser()
            # j_args = json.dumps(args)
        else:
            args = json.loads(json_file)
            # j_args = json_file

        # j_args needs to be a string at this point
        j_args = json.dumps(args)

        if not wdl_string:
            files = {'wdlSource': (wdl_file, open(wdl_file, 'rb'), 'application/octet-stream'),
                     'workflowInputs': ('report.csv', j_args, 'application/json')}
        else:
            files = {'wdlSource': ('workflow.wdl', wdl_file, 'application/text-plain'),
                     'workflowInputs': ('report.csv', j_args, 'application/json')}
        if custom_labels:
            if self.short_version >= 30:
                label_key = "labels"
            else:
                label_key = "customLabels"
            files[label_key] = ('labels.json', json.dumps(
                custom_labels), 'application/json')
        if dependencies:
            # add dependency as zip file
            files['wdlDependencies'] = (dependencies, open(
                dependencies, 'rb'), 'application/zip')
        workflow_options = {}
        if disable_caching:
            workflow_options.update({"read_from_cache": False})
        if extra_options:
            workflow_options.update(extra_options)
        if disable_caching or extra_options:
            files['workflowOptions'] = ('options.json', json.dumps(
                workflow_options), 'application/json')
            print('Enabling the following additional workflow options:')
            for k, v in workflow_options.items():
                print("{}:{}".format(k, v))

        r = requests.post(self.url, files=files, auth=self.auth) \
            if not v2 else requests.post(self.url2, files=files,
                                         auth=self.auth)
        if r.status_code not in [200, 201]:
            print_log_exit("Request Failed: {}".format(r.content))
        return json.loads(r.text)

    def stop_workflow(self, workflow_id):
        """Ends a running workflow.

        :param workflow_id: The workflow identifier.
        :return: Request response json.
        """
        self.logger.info('Aborting workflow {}'.format(workflow_id))
        return self.post('abort', workflow_id)

    def query_metadata_cached(self, workflow_id, expire=15):
        """Return all cached metadata for a given workflow

        :param workflow_id: The workflow identifier
        :param expire: The number of seconds the cache is deemed to be not fresh # noqa
        :return: Request response json
        """
        if workflow_id in self.cached_metadata:
            date_time = datetime.datetime.now() - datetime.timedelta(seconds=15)
            if self.cached_metadata[workflow_id]["timestamp"] > date_time:
                return self.cached_metadata[workflow_id]

        metadata = self.query_metadata(workflow_id, v2=True)
        metadata["timestamp"] = datetime.datetime.now()
        self.cached_metadata[workflow_id] = metadata
        return metadata

    @rate_limited(300, ONE_MINUTE)
    def query_metadata(self, workflow_id, v2=False):
        """Return all metadata for a given workflow.

        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info(
            'Querying metadata for workflow {}'.format(workflow_id))
        return self.get('metadata', workflow_id,
                        {'Accept': 'application/json',
                         'Accept-Encoding': 'identity'}, v2=v2)

    def process_metadata_label(self, metadata):
        """Transfer the labels from an old workflow id to a new one. Labels applied by the system are removed so as to avoid conflicts.

        :param old_id: The old workflow to take labels from.
        :param new_id: The new workflow id to apply the labels to.
        :return: void.
        """
        processed_labels = metadata['labels']
        try:
            del processed_labels['cromwell-workflow-id']
            del processed_labels['username']
            processed_labels['username'] = global_config.getuser()
        except KeyError as e:
            logging.debug(
                "{}. No cromwell-workflow-id in old labels.".format(str(e.message)))

        return processed_labels

    def label_workflow(self, workflow_id, labels):
        """A method for labeling a workflow with one more labels.

        :param workflow_id: Workflow ID to label.
        :param labels: A dictionary of labels.
        :return: JSON response
        """
        if not workflow_id:
            raise TypeError("Workflow ID can not be {}".format(workflow_id))
        labels_json = json.dumps(labels)
        headers = {'Content-type': 'application/json',
                   'Accept': 'application/json'}
        return self.patch('labels', workflow_id, labels_json, headers)

    def query_labels(self, labels, start_time=None, status_filter=None,
                     running_jobs=False):
        """Query cromwell database with a given set of labels.

        :param labels: A dictionary of label keys and values.
        :return: Query results.
        """
        label_dict = {}
        for k, v in labels.items():
            label_dict["label=" + k] = v
        time_query = "start=" + start_time if start_time is not None else ""
        status_query = ""
        if status_filter:
            for status in status_filter:
                status_query += "status={}&".format(status)

        url = self.build_query_url(
            self.url + '/query?' + "&".join([time_query, status_query]).lstrip("&"), label_dict, "%3A")
        url = url + 'status=Running' if running_jobs else url

        # In some cases we can get a dangling & so this removed that.
        r = requests.get(url.rstrip('&'), auth=self.auth)
        return json.loads(r.content)

    def query_status(self, workflow_id):
        """Return the status for a given workflow.

        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info('Querying status for workflow {}'.format(workflow_id))
        return self.get('status', workflow_id)

    def query_logs(self, workflow_id):
        """Return the task execution logs for a given workflow.

        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info('Querying logs for workflow {}'.format(workflow_id))
        return self.get('logs', workflow_id)

    def query_outputs(self, workflow_id):
        """Return the outputs for a given workflow.

        :param workflow_id: The workflow identifier.
        :return: Request Response json.
        """
        self.logger.info('Querying logs for workflow {}'.format(workflow_id))
        return self.get('outputs', workflow_id)

    def query(self, query_dict):
        """A function for performing a qet query given a dictionary of query terms. # noqa

        :param query_dict: Dictionary of query terms.
        :return: A dictionary of the json content.
        """
        base_url = self.url + '/query?'
        query_url = self.build_query_url(base_url, query_dict)
        self.logger.debug("QUERY REQUEST:{}".format(query_url))
        r = requests.get(query_url, auth=self.auth)
        return json.loads(r.text)

    @staticmethod
    def build_query_url(base_url, url_dict, sep='='):
        """A function for building a query URL given a dictionary of key/value pairs to query. # noqa

        :param base_url: The base query URL (ex:http://btl-cromwell:9000/api/workflows/v1/query?)
        :param url_dict: Dictionary of query terms.
        :param sep: Seperator for query terms.
        :return: Returns the full query URL.
        """
        first = True
        url_string = ''
        for key, value in url_dict.items():
            if not first:
                url_string += '&'
            if isinstance(value, datetime.datetime):
                dt = quote(str(value)) + 'Z'
                value = dt.replace('%20', 'T')
            if isinstance(value, list):
                for item in value:
                    url_string += '{}{}{}'.format(key, sep, item)
            else:
                url_string += '{}{}{}'.format(key, sep, value)
            first = False
        return base_url.rstrip() + url_string

    def query_backend(self):
        return self.get('backends')


def print_log_exit(msg, sys_exit=True, ple_logger=module_logger):
    """Function for standard print/log/exit routine for fatal errors.

    :param msg: error message to print/log.
    :param sys_exit: Cause choppy to exit.
    :param ple_logger: Logger to use when logging message.
    :return:
    """
    ple_logger.critical(msg)
    if sys_exit:
        sys.exit(exit_code.GENERAL_ERROR)
