﻿
# CBOW MODEL IN PYTORCH
# https://blog.csdn.net/weixin_35757704/article/details/124559926
import numpy as np
from torchtext.vocab import vocab
from collections import Counter, OrderedDict
from torch.utils.data import Dataset, DataLoader
from torchtext.transforms import VocabTransform  # 注意：torchtext版本0.12+
import torch
from torch import nn
from torch.nn import functional as F


def load_model():
    path = "./MODEL1.pth"
    model = torch.load(path)
    model.eval()
    return model





def get_text(file_data=read_file()):
    sentence_list = []
    for text in file_data.split('\n'):
      #print(text)
      sentence_list.append(text_prepare(text,stopwords=False))
    #print(sentence_list)
    #sentence_list = [ # 假设这是全部的训练语料
    #        "nlp drives computer programs that translate text from one language to another",
    #        "nlp combines computational linguistics rule based modeling of human language with statistical",
    #        "nlp model respond to text or voice data and respond with text",
    #]
    return sentence_list


class CbowDataSet(Dataset):
  def __init__(self, text_list, side_window=3):
        """
        构造Word2vec的CBOW采样Dataset
        :param text_list: 语料
        :param side_window: 单侧正例（构造背景词）采样数，总正例是：2 * side_window
        """
        super(CbowDataSet, self).__init__()
        self.side_window = side_window
        text_vocab, vocab_transform = self.reform_vocab(text_list)
        self.text_list = text_list  # 原始文本
        self.text_vocab = text_vocab  # torchtext的vocab
        self.vocab_transform = vocab_transform  # torchtext的vocab_transform
        self.cbow_data = self.generate_cbow()

  def __len__(self):
      return len(self.cbow_data)

  def __getitem__(self, idx):
      data_row = self.cbow_data[idx]
      return data_row[0], data_row[1]

  def reform_vocab(self, text_list):
        """根据语料构造torchtext的vocab"""
        total_word_list = []
        for _ in text_list: # 将嵌套的列表([[xx,xx],[xx,xx]...])拉平 ([xx,xx,xx...])
            total_word_list += _.split(" ")
        counter = Counter(total_word_list) # 统计计数
        sorted_by_freq_tuples = sorted(counter.items(), key=lambda x: x[1], reverse=True) # 构造成可接受的格式：[(单词,num), ...]
        ordered_dict = OrderedDict(sorted_by_freq_tuples)
        # 开始构造 vocab
        special_token = ["<UNK>", "<SEP>"] # 特殊字符
        text_vocab = vocab(ordered_dict, specials=special_token) # 单词转token，specials里是特殊字符，可以为空
        text_vocab.set_default_index(0)
        vocab_transform = VocabTransform(text_vocab)
        return text_vocab, vocab_transform

  def generate_cbow(self):
    """生成CBOW的训练数据"""
    cbow_data = []
    for sentence in self.text_list:
        sentence_id_list = np.array(self.vocab_transform(sentence.split(' ')))
        for center_index in range(
                    self.side_window, len(sentence_id_list) - self.side_window): # 防止前面或后面取不到足够的值，这是取index的上下界
                pos_index = list(range(center_index - self.side_window, center_index + self.side_window + 1))
                del pos_index[self.side_window]
                cbow_data.append([sentence_id_list[center_index], sentence_id_list[pos_index]])
    return cbow_data

  def get_vocab_transform(self):
    return self.vocab_transform

  def get_vocab_size(self):
    return len(self.text_vocab)

class Word2VecModel(nn.Module):
  def __init__(self, vocab_size, batch_size, word_embedding_size=100, hidden=64):
        """
        Word2vec模型CBOW实现
        :param vocab_size: 单词个数
        :param word_embedding_size: 每个词的词向量维度
        :param hidden: 隐层维度
        """
        super(Word2VecModel, self).__init__()
        self.vocab_size = vocab_size
        self.word_embedding_size = word_embedding_size
        self.hidden = hidden
        self.batch_size = batch_size
        self.word_embedding = nn.Embedding(self.vocab_size, self.word_embedding_size) # token对应的embedding
        # 建模
        self.linear_in = nn.Linear(self.word_embedding_size, self.hidden)
        self.linear_out = nn.Linear(self.hidden, self.vocab_size)
  def forward(self, input_labels):
        around_embedding = self.word_embedding(input_labels)
        avg_around_embedding = torch.mean(around_embedding, dim=1) # 1. 输入的词向量对应位置求平均
        in_emb = F.relu(self.linear_in(avg_around_embedding)) # 2. 过第一个linear，使用relu激活函数
        out_emb = F.log_softmax(self.linear_out(in_emb)) # 3. 过第二个linear，得到维度是：[batch_size, 单词总数]
        return out_emb

  def get_embedding(self, token_list: list):
    return self.word_embedding(torch.Tensor(token_list).long())


def test(model):
    # 最后测试一下
    # 得到: nlp can translate text from one language to another 的词向量
    sentence_list = get_text()
    cbow_data_set = CbowDataSet(sentence_list)
    sentence = "nlp can translate text from one language to another"
    vocab_transform = cbow_data_set.get_vocab_transform()
    sentence_ids = vocab_transform(sentence.split(' '))
    sentence_embedding = model.get_embedding(sentence_ids)
    print("这个是句向量的维度：", sentence_embedding.shape)

    

path = "./MODEL1.pth"
model = torch.load(path)
model.eval()