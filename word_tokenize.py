#!coding=utf-8
from typing import List
import time
import re


class Tokenize:
    flags_head = [' ', ']', u']', u'་', u'།',u'.']
    flags_head_byte = [160]

    flags_last_0 = [u'་', u'འི་', u'འུ་', u'འོ་', u'ས་', u'ར་']
    flags_last_1 = [u'།', u'འི།', u'འུ།', u'འོ།', u'ས།', u'ར།']
    # flags_last_2 = [u'འི', u'འུ', u'འོ', u'ས', u'ར']
    flags_last_3 = [u'འི', u'འུ', u'འོ']

    def __init__(self, word_pool: List):
        self.word_pool = word_pool
        for b in self.flags_head:
            self.flags_head_byte.append(ord(b))

    # 去掉末尾的་
    @staticmethod
    def word_valid(word):
        _tmp = word.split(u'་')
        _word = u'་'.join(_tmp[:-1])

        return _word

    def find_word(self, text: str):
        _begin_word = {}  # {'3':'some'}  3为单词的起始点

        # 遍历词库
        for item in self.word_pool:
            # 词
            word = item.strip()
            # 藏语原因，去掉末尾的点
            word = word[:-1]

            _offset = 0

            while True:

                _begin = text.find(word, _offset)

                if _begin > -1:
                    _offset = _begin + 1

                    # 单个词,连词
                    if word in self.flags_last_3:
                        if _begin not in _begin_word:
                            _begin_word[_begin] = word
                    else:
                        _end = _begin + len(word)  # 词结尾的位置
                        # 起点：该词结尾的位置，往后找到点或竖的位置
                        _check_end_0 = text.find(u'་', _end) + 1
                        _check_end_1 = text.find(u'།', _end) + 1

                        _last_flag_0 = text[_end:_check_end_0]
                        _last_flag_1 = text[_end:_check_end_1]

                        _check_begin = text[_begin - 1] if _begin > 0 else ' '
                        # 如果该词的前部分是]等特殊，且后部分为特殊的几个词。则也计入词频
                        if (ord(_check_begin) in self.flags_head_byte) and (
                                _last_flag_0 in self.flags_last_0 or _last_flag_1 in self.flags_last_1):
                            if _begin in _begin_word:
                                if len(word) > len(_begin_word[_begin]):
                                    _begin_word[_begin] = word
                            else:
                                _begin_word[_begin] = word
                else:
                    break

        _begin_list = list(_begin_word.keys())  # set to list
        _begin_list.sort()

        _index = 1

        while _index < len(_begin_list):
            _index_begin = _begin_list[_index]
            _index_word = _begin_word[_index_begin]
            _index_end = _index_begin + len(_index_word)
            # 前一个词
            _i = _index - 1
            _i_begin = _begin_list[_i]
            _i_word = _begin_word[_i_begin]
            _i_end = _i_begin + len(_i_word)
            # 异常处理，若上一词的结尾位置比 词的开始位置大，则异常
            if _i_end > _index_begin:
                del _begin_word[_index_begin]
                del _begin_list[_index]
            else:
                _index = _index + 1
        # 所有的起始点，起始点对应的单词
        return _begin_list, _begin_word

    def text_count(self, text: str):
        _begin_list, _begin_word = self.find_word(text)

        _string_buffer = []

        _index = len(_begin_list) - 1
        _last = len(text) - 1
        # 从末尾开始
        while _index >= 0:
            # 起始点
            _begin = _begin_list[_index]
            # 内容
            _word = _begin_word[_begin]
            # _word = f'{_word}་'
            # 结束点
            _end = _begin + len(_word)
            # 词性
            _string_buffer.insert(0,f" {_word} {text[_end:_last]}")

            _last = _begin

            _index = _index - 1

        _string_buffer.insert(0, text[:_last])
        result_text = ''.join(_string_buffer)

        return result_text

    # 预处理文件
    def pre_deal(self, source: str, del_content: List):
        for d in del_content:
            source = source.replace(d, '')
        # 若空格前不是点或者竖，则该空格应该被替换为点
        source = re.sub('([^།་ \\n])([ ])', r"\1་\2", source)
        source = source.replace(' ', '')
        source = source.replace(u'༌', u'་')  # 肉眼不可见，显示一样，其实不一样
        # _temp = []
        # tmp_list = source.splitlines()
        # for _line in tmp_list:
        #     _temp.append(u"->་%s" % _line)
        #
        # source = '\n'.join(_temp)
        return source

    def run(self, source: str, del_content: List):
        source = self.pre_deal(source, del_content)
        text_result = self.text_count(source)
        # 1.结果将(空格་) 替换为་空格
        text_result = text_result.replace(u" ་", "་ ")
        # 2.结果将多空格替换为单空格
        text_result = re.sub(' +', ' ', text_result)
        # 3.若空格前不是点则加入@
        text_result = re.sub('([^།་])([ ])', r"\1@\2", text_result)
        # 4.处理掉"@空格"
        text_result = text_result.replace(u"@ ", "")
        return text_result


if __name__ == '__main__':
    import pymongo

    n = 4
    myclient = pymongo.MongoClient("mongodb://192.168.0.61:37017")
    db = myclient["tibetan"]
    start = time.time()
    word_pool = [x['word'] for x in db['word_stat_dict'].find({'type': 'used'})]
    # 加入已经确认的新词
    for x in db['self_dict'].find({'is_check': True}):
        word_pool.append(x['word'])
    u = Tokenize(word_pool=word_pool)
    source = '''
    རྫུ་འཕྲུལ་ལྡན་ པའི་ མཐུ་ ལ་ ལྟོས། དེ་ནས་ བཅོམ་ལྡན་p621ln1འདས་ ཀྱིས་ གཙུག་ལག་ཁང་ གི་ ཕྱི་རོལ་ དུ་ ཞབས་ གཉིས་བཀྲུས་ ཏེ།
    '''
    # with open('./test.txt','r') as f:
    #     source = f.read()
    print(time.time() - start)
    print(u.run(source, []))
    print(time.time() - start)
