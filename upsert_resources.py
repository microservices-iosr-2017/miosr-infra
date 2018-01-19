
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


def get_dict_to_substituted_files(original_config_dir, out_dir, overrides, injected_file):
    vars_dict = get_vars_dict(original_config_dir)
    vars_dict.update(overrides)

    filename_pairs = [("config", injected_file), ("dep", "deployment.yml"), ("svc", "service.yml")]
    substituted_pairs = map(lambda (k, fname): (k, substitute(vars_dict, original_config_dir, fname, out_dir)),
                            filename_pairs)

    return dict(substituted_pairs)

def get_current_config_version(base_name):
    '''
    :return: current config version (or -1 if no config was found) 
    '''
    current_cm_names = os.popen("kubectl get cm | tail -n+2 | cut -d' ' -f 1").read().split("\n")
    names_matching_base = filter(lambda x: x.startswith(base_name), current_cm_names)

    if not names_matching_base:
        v = -1
    else:
        def name_to_suffix(x):
            v_suffix = x.replace(base_name, "")
            if not v_suffix:
                return 0
            else:
                return int(v_suffix.replace("-v", ""))

        version_suffixes = map(name_to_suffix, names_matching_base)
        v = max(version_suffixes)

    return v

def apply_conf(config_name, filename):
    print("Applying config from file: " + filename)
    os.system("kubectl create configmap --dry-run -o yaml {} --from-file={} | kubectl apply -f -"
              .format(config_name, filename))

def apply_res(filename):
    print("Applying resource from file: " + filename)
    os.system("kubectl apply -f {}".format(filename))

def process_args():
    parser = argparse.ArgumentParser(description='Manage MIOSR resources')
    parser.add_argument('-s', '--service', dest="service_name", help='name of service to modify', required=True)
    parser.add_argument('-t', '--cleanup-temp', dest="cleanup_temp", action='store_true',
                        help='should perform temp directory cleanup')
    parser.add_argument('-c', '--replace-config', dest="replace_config", action='store_true',
                        help='replace configuration with new version (and restart cluster)')
    parser.add_argument('-i', '--injected-configuration-file', dest="injected_config", help='name of configuration file to be injected to container', required=False, default='config.properties')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = process_args()

    conf_base_name = "{}-service".format(args.service_name)
    conf_v = get_current_config_version(conf_base_name)
    new_conf_v = max([conf_v+1 if args.replace_config else conf_v, 0])
    config_name = "{}-v{}".format(conf_base_name, new_conf_v)

    config_dir = os.path.join(get_script_dir(), args.service_name)
    out_dir = tempfile.mkdtemp(prefix="{}-".format(args.service_name))

    substitued = get_dict_to_substituted_files(config_dir, out_dir, {"configname": config_name}, args.injected_config)

    # create config
    apply_conf(config_name, substitued["config"])
    # deployment and service
    for fpath in [substitued["dep"], substitued["svc"]]:
        apply_res(fpath)

    if args.cleanup_temp:
        shutil.rmtree(out_dir)
    else:
        print substitued
