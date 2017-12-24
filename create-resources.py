
import os
import sys
import codecs
import string
import tempfile
import json
import shutil
import argparse

def get_script_dir():
    return os.path.dirname(os.path.realpath(__file__))


def get_vars_dict(dir):
    f = codecs.open(os.path.join(dir, "vars.json"))
    vars_dict = json.loads(f.read())
    f.close()
    return vars_dict


def substitute(mapping, in_dir, filename, out_dir):
    '''

    :param mapping: 
    :param filename: 
    :return: name of new file created by substituting $ references 
    '''
    in_path = os.path.join(in_dir, filename)
    out_path = os.path.join(out_dir, filename)

    template_file = codecs.open(in_path, 'r', 'utf-8')
    template = template_file.read()
    template_file.close()

    content_with_substitutes = string.Template(template).substitute(mapping)

    output_file = codecs.open(out_path, 'w', 'utf-8')
    output_file.write(content_with_substitutes)
    output_file.close()

    return out_path


def get_dict_to_substituted_files(original_config_dir, out_dir):
    vars_dict = get_vars_dict(original_config_dir)

    filename_pairs = [("config", "config.properties"), ("dep", "deployment.yml"), ("svc", "service.yml")]
    substituted_pairs = map(lambda (k, fname): (k, substitute(vars_dict, original_config_dir, fname, out_dir)),
                            filename_pairs)

    return dict(substituted_pairs)


def apply_conf(service_name, filename):
    print("Applying config from file: " + filename)
    os.system("kubectl create configmap --dry-run -o yaml {}-config --from-file={} | kubectl apply -f -"
              .format(service_name, filename))

def apply_res(filename):
    print("Applying resource from file: " + filename)
    os.system("kubectl apply -f {}".format(filename))

def process_args():
    parser = argparse.ArgumentParser(description='Manage MIOSR resources')
    parser.add_argument('-s', '--service', dest="service_name", help='name of service to modify', required=True)
    parser.add_argument('-c', '--cleanup', dest="cleanup_temp", action='store_true',
                        help='should perform temp directory cleanup')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = process_args()

    config_dir = os.path.join(get_script_dir(), args.service_name)
    out_dir = tempfile.mkdtemp(prefix="{}-".format(args.service_name))

    substitued = get_dict_to_substituted_files(config_dir, out_dir)

    # create config
    apply_conf(args.service_name, substitued["config"])
    # deployment and service
    for fpath in [substitued["dep"], substitued["svc"]]:
        apply_res(fpath)

    if args.cleanup_temp:
        shutil.rmtree(out_dir)
    else:
        print substitued
