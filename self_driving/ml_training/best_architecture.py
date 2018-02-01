#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tensorflow as tf
import os
import numpy as np
import shutil
import argparse

from DataHolder import DataHolder
from Config import Config
from Trainer import Trainer
from DFN import DFN
from util import reconstruct_from_record, accuracy_per_category
from util import int2command, get_random_architecture_and_activations


def architecture_search(records,
                        experiments=10,
                        deepest_net_size=4):
    """
    :type train_data_path: str
    :type eval_data_path: str
    """
    sizes = np.random.randint(1, deepest_net_size, experiments)
    hidden_layers, activations = get_random_architecture_and_activations(network_sizes=sizes) # noqa
    numeric_result = []
    results = []
    info = []

    for arch, act in zip(hidden_layers, activations):
        config = Config(architecture=arch,
                        activations=act)

        data = DataHolder(config,
                          records=records)
        name = str(arch)
        print(name + ":\n")
        graph = tf.Graph()
        network = DFN(graph, config)
        trainer = Trainer(graph, config, network, data)
        trainer.fit(verbose=True)
        valid_acc = trainer.get_valid_accuracy()
        numeric_result.append(valid_acc)
        name += ': valid_acc = {0:.6f} | '.format(valid_acc)
        valid_images, valid_labels, _ = reconstruct_from_record(data.get_valid_tfrecord()) # noqa
        valid_images = valid_images.astype(np.float32) / 255
        valid_pred = trainer.predict(valid_images)
        acc_cat = accuracy_per_category(valid_pred, valid_labels, categories=4)
        for i, cat_result in enumerate(acc_cat):
            name += int2command[i] + ": = {0:.6f}, ".format(cat_result)
        results.append(name)
        if os.path.exists("checkpoints"):
            shutil.rmtree("checkpoints")
        attrs = vars(config)
        config_info = ["%s: %s" % item for item in attrs.items()]
        info.append(config_info)

    best_result = max(list(zip(numeric_result, hidden_layers, info)))
    result_string = """In an experiment with {0} architectures
    the best one is {1} with valid accuracy of {2}.
    \nThe training uses the following params:
    \n{3}\n""".format(experiments,
                      best_result[1],
                      best_result[0],
                      best_result[2])
    file = open("architecture.txt", "w")
    file.write("Results with different values for learing_rate\n")
    for result in results:
        result += "\n"
        file.write(result)
    file.write("\n")
    file.write(result_string)
    file.close()


def main():
    """
    Main script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-m",
                        "--mode",
                        type=str,
                        default="pure",
                        help="mode for data: pure, flip, aug, bin, gray, green (default=pure)") # noqa
    args = parser.parse_args()
    records = ["_train.tfrecords", "_valid.tfrecords", "_test.tfrecords"]
    new_records = []
    for record in records:
        record = args.mode + record
        new_records.append(record)
    architecture_search(new_records)


if __name__ == "__main__":
    main()