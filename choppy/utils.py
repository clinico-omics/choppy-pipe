import json
import os
import re
import csv
import getpass
import shutil
import zipfile
import config as c
from jinja2 import Environment, FileSystemLoader
from cromwell import Cromwell


def check_identifier(identifier):
    matchObj = re.match(r'^[a-zA-Z][a-zA-Z0-9_]+$', identifier, re.M | re.I)
    if matchObj:
        return True
    else:
        return False


def install_app(app_dir, app_file):
    app_name = os.path.splitext(os.path.basename(app_file))[0]
    dest_namelist = [os.path.join(app_name, 'inputs'),
                     os.path.join(app_name, 'workflow.wdl'),
                     os.path.join(app_name, 'tasks.zip')]

    app_file_handler = zipfile.ZipFile(app_file)

    def check_app(app_file_handler):
        namelist = app_file_handler.namelist()
        if len([path for path in dest_namelist if path in namelist]) == 3:
            return True
        else:
            return False

    if check_app(app_file_handler):
        app_file_handler.extractall(app_dir, dest_namelist)
        print("Install %s successfully." % app_name)
    else:
        raise Exception("Not a valid app.")


def uninstall_app(app_dir):
    answer = ''
    while answer.upper() not in ("YES", "NO", "Y", "N"):
        answer = raw_input("Enter Yes/No: ")
        answer = answer.upper()
        if answer == "YES" or answer == "Y":
            shutil.rmtree(app_dir)
            print("Uninstall %s successfully." % os.path.basename(app_dir))
        elif answer == "NO" or answer == "N":
            print("Cancel uninstall %s." % os.path.basename(app_dir))
        else:
            print("Please enter Yes/No.")


def parse_samples(file):
    reader = csv.DictReader(open(file, 'rb'))
    dict_list = []

    for line in reader:
        dict_list.append(line)

    return dict_list


def render_app(app_path, template_file, data):
    env = Environment(loader=FileSystemLoader(app_path))
    template = env.get_template(template_file)
    return template.render(**data)


def write(path, filename, data):
    with open(os.path.join(path, filename), 'w') as f:
        f.write(data)


def submit_workflow(wdl, inputs, dependencies, label, username=c.getuser(),
                    server='localhost', extra_options=None, labels_dict=None):
    labels_dict = kv_list_to_dict(
        label) if kv_list_to_dict(label) != None else {}
    labels_dict['username'] = username
    host, port, auth = c.get_conn_info(server)
    cromwell = Cromwell(host=host, port=port, auth=auth)
    result = cromwell.jstart_workflow(wdl_file=wdl, json_file=inputs, dependencies=dependencies,
                                      extra_options=kv_list_to_dict(
                                          extra_options),
                                      custom_labels=labels_dict)
    result['port'] = cromwell.port

    return result


def kv_list_to_dict(kv_list):
    """
    Converts a list of kv pairs delimited with colon into a dictionary.
    :param kv_list: kv list: ex ['a:b', 'c:d', 'e:f']
    :return: a dict, ex: {'a': 'b', 'c': 'd', 'e': 'f'}
    """
    new_dict = dict()
    if kv_list:
        for item in kv_list:
            (key, val) = item.split(':')
            new_dict[key] = val
        return new_dict
    else:
        return None


def parse_json(instance):
    if isinstance(instance, dict):
        for key, value in instance.iteritems():
            if isinstance(value, basestring):
                try:
                    instance[key] = json.loads(value)
                except ValueError:
                    pass
            elif isinstance(value, dict):
                instance[key] = parse_json(instance[key])
    elif isinstance(instance, list):
        for idx, value in enumerate(instance):
            instance[idx] = parse_json(value)

    return instance


if __name__ == "__main__":
    instance = {
        "calls": {},
        "end": "2018-12-27T11:42:09.787+08:00",
        "failures": [
            {
                "causedBy": [
                    {
                        "causedBy": [],
                        "message": "Failed to import workflow ./tasks/mapping.wdl.:\nFile not found /tasks/mapping.wdl\n.%2Ftasks%2Fmapping.wdl: Name or service not known"
                    }
                ],
                "message": "Workflow input processing failed"
            }
        ],
        "id": "7e1ad759-b538-474d-abd1-deaffdd7c2ce",
        "inputs": {},
        "outputs": {},
        "start": "2018-12-27T11:42:09.766+08:00",
        "status": "Failed",
        "submission": "2018-12-27T11:41:50.580+08:00",
        "submittedFiles": {
            "inputs": "{\"Sentieon.fasta\":\"GRCh38.d1.vd1.fa\",\"Sentieon.ref_dir\":\"oss://pgx-reference-data/GRCh38.d1.vd1/\",\"Sentieon.dbsnp\":\"dbsnp_146.hg38.vcf\",\"Sentieon.fastq_1\":\"oss://pgx-storage-backend/Quartet_fastq/20170403_DNA_ILM_ARD/Quartet_DNA_ILM_ARD_LCL5_1_20170403_R1.fastq.gz\",\"Sentieon.SENTIEON_INSTALL_DIR\":\"/opt/sentieon-genomics\",\"Sentieon.dbmills_dir\":\"oss://pgx-reference-data/GRCh38.d1.vd1/\",\"Sentieon.db_mills\":\"Mills_and_1000G_gold_standard.indels.hg38.vcf\",\"Sentieon.nt\":\"30\",\"Sentieon.cluster_config\":\"OnDemand ecs.sn1ne.4xlarge img-ubuntu-vpc\",\"Sentieon.docker\":\"localhost:5000/sentieon-genomics:v2018.08.01 oss://pgx-docker-images/dockers\",\"Sentieon.dbsnp_dir\":\"oss://pgx-reference-data/GRCh38.d1.vd1/\",\"Sentieon.sample\":\"Quartet_DNA_ILM_ARD_LCL5_1_20170403\",\"Sentieon.fastq_2\":\"oss://pgx-storage-backend/Quartet_fastq/20170403_DNA_ILM_ARD/Quartet_DNA_ILM_ARD_LCL5_1_20170403_R2.fastq.gz\",\"user\":\"renluyao\"}",
            "labels": "{\"username\": \"renluyao\"}",
            "options": "{\n\n}",
            "root": "None",
                    "workflow": "import \"./tasks/mapping.wdl\" as mapping\r\nimport \"./tasks/Metrics.wdl\" as Metrics\r\nimport \"./tasks/Dedup.wdl\" as Dedup\r\nimport \"./tasks/deduped_Metrics.wdl\" as deduped_Metrics\r\nimport \"./tasks/Realigner.wdl\" as Realigner\r\nimport \"./tasks/BQSR.wdl\" as BQSR\r\nimport \"./tasks/Haplotyper.wdl\" as Haplotyper\r\n\r\n\r\nworkflow Sentieon {\r\n\r\n\tFile fastq_1\r\n\tFile fastq_2\r\n\r\n\tString SENTIEON_INSTALL_DIR\r\n\tString sample\r\n\tString nt\r\n\tString docker\r\n\t\r\n\tString fasta\r\n\tFile ref_dir\r\n\tFile dbmills_dir\r\n\tString db_mills\r\n\tFile dbsnp_dir\r\n\tString dbsnp\r\n\tString cluster_config\r\n\r\n\r\n\tcall mapping.mapping as mapping {\r\n\t\tinput: \r\n\t\tSENTIEON_INSTALL_DIR=SENTIEON_INSTALL_DIR,\r\n\t\tgroup=sample,\r\n\t\tsample=sample,\r\n\t\tpl=\"ILLUMINAL\",\r\n\t\tnt=nt,\r\n\t\tfasta=fasta,\r\n\t\tref_dir=ref_dir,\r\n\t\tfastq_1=fastq_1,\r\n\t\tfastq_2=fastq_2,\r\n\t\tdocker=docker,\r\n\t\tcluster_config=cluster_config\r\n\t}\r\n\r\n\tcall Metrics.Metrics as Metrics {\r\n\t\tinput:\r\n\t\tSENTIEON_INSTALL_DIR=SENTIEON_INSTALL_DIR,\r\n\t\tfasta=fasta,\r\n\t\tref_dir=ref_dir,\r\n\t\tnt=nt,\r\n\t\tsorted_bam=mapping.sorted_bam,\r\n\t\tsorted_bam_index=mapping.sorted_bam_index,\t\t\r\n\t\tsample=sample,\r\n\t\tdocker=docker,\r\n\t\tcluster_config=cluster_config\r\n\t}\r\n\r\n\tcall Dedup.Dedup as Dedup {\r\n\t\tinput:\r\n\t\tSENTIEON_INSTALL_DIR=SENTIEON_INSTALL_DIR,\r\n\t\tnt=nt,\r\n\t\tsorted_bam=mapping.sorted_bam,\r\n\t\tsorted_bam_index=mapping.sorted_bam_index,\r\n\t\tsample=sample,\r\n\t\tdocker=docker,\r\n\t\tcluster_config=cluster_config\r\n\t}\r\n\tcall deduped_Metrics.deduped_Metrics as deduped_Metrics {\r\n\t\tinput:\r\n\t\tSENTIEON_INSTALL_DIR=SENTIEON_INSTALL_DIR,\r\n\t\tfasta=fasta,\r\n\t\tref_dir=ref_dir,\r\n\t\tnt=nt,\r\n\t\tDedup_bam=Dedup.Dedup_bam,\r\n\t\tDedup_bam_index=Dedup.Dedup_bam_index,\r\n\t\tsample=sample,\r\n\t\tdocker=docker,\r\n\t\tcluster_config=cluster_config\r\n\t}\r\n\tcall Realigner.Realigner as Realigner {\r\n\t\tinput:\r\n\t\tSENTIEON_INSTALL_DIR=SENTIEON_INSTALL_DIR,\r\n\t\tfasta=fasta,\r\n\t\tref_dir=ref_dir,\r\n\t\tnt=nt,\r\n\t\tDedup_bam=Dedup.Dedup_bam,\r\n\t\tDedup_bam_index=Dedup.Dedup_bam_index,\r\n\t\tdb_mills=db_mills,\r\n\t\tdbmills_dir=dbmills_dir,\r\n\t\tsample=sample,\r\n\t\tdocker=docker,\r\n\t\tcluster_config=cluster_config\r\n\t}\r\n\r\n\tcall BQSR.BQSR as BQSR {\r\n\t\tinput:\r\n\t\tSENTIEON_INSTALL_DIR=SENTIEON_INSTALL_DIR,\r\n\t\tfasta=fasta,\r\n\t\tref_dir=ref_dir,\r\n\t\tnt=nt,\r\n\t\trealigned_bam=Realigner.realigner_bam,\r\n\t\trealigned_bam_index=Realigner.realigner_bam_index,\r\n\t\tdb_mills=db_mills,\r\n\t\tdbmills_dir=dbmills_dir,\r\n\t\tdbsnp=dbsnp,\r\n\t\tdbsnp_dir=dbsnp_dir,\r\n\t\tsample=sample,\r\n\t\tdocker=docker,\r\n\t\tcluster_config=cluster_config\r\n\t}\r\n\tcall Haplotyper.Haplotyper as Haplotyper {\r\n\t\tinput:\r\n\t\tSENTIEON_INSTALL_DIR=SENTIEON_INSTALL_DIR,\r\n\t\tfasta=fasta,\r\n\t\tref_dir=ref_dir,\r\n\t\tnt=nt,\r\n\t\trecaled_bam=BQSR.recaled_bam,\r\n\t\trecaled_bam_index=BQSR.recaled_bam_index,\r\n\t\tdbsnp=dbsnp,\r\n\t\tdbsnp_dir=dbsnp_dir,\r\n\t\tsample=sample,\r\n\t\tdocker=docker,\r\n\t\tcluster_config=cluster_config\r\n\t}\r\n}\r\n",
                    "workflowType": "WDL"
        }
    }
    print(json.dumps(parse_json(instance), indent=2, sort_keys=True))