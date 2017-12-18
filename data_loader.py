import torch
import torch.utils.data
from torch.autograd import Variable
from vocab import *
from config import *
import numpy as np
import random

np.random.seed(0)


class DataLoader:
    EOS = 0  # to mean end of sentence
    UNK = 1  # to mean unknown token

    maxlen = MAXLEN

    def __init__(self, text_file=None, sentences=None, word_dict=None):

        if text_file:
            print("Loading text file at {}".format(text_file))
            with open(text_file, "rt") as f:
                sentences = f.readlines()
            print("Making dictionary for these words")
            word_dict = build_and_save_dictionary(sentences, source=text_file)

        assert sentences and word_dict, "Please provide the file to extract from or give sentences and word_dict"

        self.sentences = sentences
        self.word_dict = word_dict
        print("Making reverse dictionary")
        self.revmap = list(self.word_dict.items())

        self.lengths = [len(sent) for sent in self.sentences]

    def convert_sentence_to_indices(self, sentence):

        indices = [
                      # assign an integer to each word, if the word is too rare assign unknown token
                      self.word_dict.get(w) if self.word_dict.get(w, VOCAB_SIZE + 1) < VOCAB_SIZE else self.UNK

                      for w in sentence.split()  # split into words on spaces
                  ][: self.maxlen - 1]  # take only maxlen-1 words per sentence at the most.

        # last words are EOS
        indices += [self.EOS] * (self.maxlen - len(indices))

        indices = np.array(indices)
        indices = Variable(torch.from_numpy(indices))
        if USE_CUDA:
            indices = indices.cuda(CUDA_DEVICE)

        return indices

    def convert_indices_to_sentences(self, indices):

        def convert_index_to_word(idx):

            idx = idx.data[0]
            if idx == 0:
                return "EOS"
            elif idx == 1:
                return "UNK"

            word, idx_ = self.revmap[idx - 2]

            assert idx_ == idx
            return word

        words = [convert_index_to_word(idx) for idx in indices]

        return " ".join(words)

    def fetch_batch(self, batch_size, group_size):

        groups = []
        lengths = []

        for g in range(group_size):

            first_index = random.randint(0, len(self.sentences) - batch_size)
            indices = []
            lens = []

            for i in range(first_index, first_index + batch_size):
                sent = self.sentences[i]
                ind = self.convert_sentence_to_indices(sent)
                indices.append(ind)
                lens.append(len(sent))

            groups.append(indices)
            lengths.append(lens)

        groups = torch.stack([torch.stack(b) for b in groups])
        lengths = np.array(lengths)

        return groups, lengths

