# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Downloads CNN Dailymail dataset.

Downloads CNN Dailymail dataset.
"""

from absl import app
from absl import flags
from absl import logging
from absl.flags import argparse_flags

import threading
from datasets import load_dataset
from utils import gcs_path
import evaluate
import nltk
import os
from transformers import AutoModelForSeq2SeqLM
from transformers import AutoTokenizer
from transformers import utils as transformer_utils

FLAGS = flags.FLAGS

flags.DEFINE_string('dataset', None, 'Name of dataset to download.')
flags.DEFINE_string('subset', None, 'subset of dataset.')
flags.DEFINE_string('dataset_path', None, 'Path to download dataset to.')
flags.DEFINE_string('model_checkpoint', 't5-small', 'Model checkpoint name')
flags.DEFINE_string('workspace_path', None, 'Path to download workspace data to.')

def download_workspace():
  nltk.download('punkt')
  evaluate.load('rouge')
  AutoTokenizer.from_pretrained(FLAGS.model_checkpoint)
  AutoModelForSeq2SeqLM.from_pretrained(FLAGS.model_checkpoint)
  dst, fs = gcs_path(FLAGS.workspace_path)

  logging.info('Saving nltk_data....')
  fs.put('./nltk_data', os.path.join(dst, 'nltk_data'), recursive=True)

  logging.info('Saving huggingface data....')
  fs.put('.cache/huggingface', dst, recursive=True)

def download_dataset():
  src, src_fs = gcs_path(FLAGS.dataset)
  dst, _ = gcs_path(path=FLAGS.dataset_path, gcs_prefix='gs://')
  if src_fs:
    logging.info('Copying Dataset....')
    src_fs.cp(src, dst, recursive=True)
  else:
    logging.info('Downloading Dataset....')
    datasets = load_dataset(FLAGS.dataset, FLAGS.subset)
    logging.info('Saving Dataset to %s....', FLAGS.dataset_path)
    datasets.save_to_disk(dst)

def main(argv):
  del argv

  t1 = threading.Thread(target=download_workspace)
  t2 = threading.Thread(target=download_dataset)

  t1.start()
  t2.start()

  t1.join()
  t2.join()
  

if __name__ == '__main__':
  transformer_utils.logging.disable_progress_bar()
  logging.set_verbosity(logging.INFO)
  parser = argparse_flags.ArgumentParser(allow_abbrev=False)
  app.run(main, flags_parser=parser.parse_known_args)
