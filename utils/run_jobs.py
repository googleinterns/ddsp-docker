import os
from absl import app
from absl import logging

def run_configurations(list_of_config_files):

    for config_file in list_of_config_files:
        file_path = os.path.join('./cluster_configurations', config_file)
        if os.path.exists(file_path):
            # run training
            pass
        else:
            logging.info("File %s was not found. Job configuration file skipped.", file_path)


def main(unused_argv):
    run_configurations(['config.yaml', 'config2.yaml'])

if __name__ == "__main__":
    app.run(main)


