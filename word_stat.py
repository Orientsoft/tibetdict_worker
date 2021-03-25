#!coding=utf-8
from typing import List
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading
import re
from flashtext import KeywordProcessor


class UnitStat:
    flags_head = [' ', ']', u']', u'་', u'།']
    flags_head_byte = [160]

    flags_last_0 = [u'་', u'འི་', u'འུ་', u'འོ་', u'ས་', u'ར་']
    flags_last_1 = [u'།', u'འི།', u'འུ།', u'འོ།', u'ས།', u'ར།']
    flags_last_2 = [u'འི', u'འུ', u'འོ', u'ས', u'ར']
    flags_last_3 = [u'འི', u'འུ', u'འོ']
    not_new_word = ['་', '->་', '།', ' ', '']
    color_num = 6

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

    def new_find_word(self, text: str):

        keyword_processor = KeywordProcessor()
        word_pool_dict = {}
        # 遍历词库
        for item in self.word_pool:
            # 词典id
            word_index = item['id']
            # 词
            word = item['word'].strip()
            # 藏语原因，去掉末尾的点
            word = word[:-1]
            # 词性
            nature = item['nature'].strip()
            # header_re = "[ |\]|་|།]"
            # footer_re = "[འི|འུ|འོ|ས|ར]?[་|།]"

            # p = re.compile(f"{header_re}{word}{footer_re}")
            # for m in p.finditer(text):
            #     print(m.start()+1,m.start()+1+len(word), m.group())
            word_pool_dict[word] = [word_index, nature]
            keyword_processor.add_keyword(word)
        keywords_found = keyword_processor.extract_keywords(text, span_info=True)
        # 修正结果
        correct_found = []
        for item in keywords_found:
            word = item[0]
            start = item[1]
            end = item[2]
            if word in self.flags_last_3:
                correct_found.append(item)
            else:
                _check_end_0 = text.find(u'་', end) + 1
                _check_end_1 = text.find(u'།', end) + 1

                _last_flag_0 = text[end:_check_end_0]
                _last_flag_1 = text[end:_check_end_1]

                _check_begin = text[start - 1]
                # 如果该词的前部分是]等特殊，且后部分为特殊的几个词。则也计入词频
                if (ord(_check_begin) in self.flags_head_byte) and (
                        _last_flag_0 in self.flags_last_0 or _last_flag_1 in self.flags_last_1):
                    correct_found.append(item)
                else:
                    print('exclude item:', item)
        # 词，开始位置，结束位置 and 词库的dict
        return correct_found, word_pool_dict

    def text_count(self, text: str):
        # [('བཅོམ་ལྡན་འདས', 3, 15)]  , {'བཅོམ་ལྡན་འདས':['fadfa1231231','词性_名词']}
        word_found_list, word_pool_dict = self.new_find_word(text)
        tmp_context = ''
        start = 0
        for item in word_found_list:
            word_id = word_pool_dict.get(item[0])[0]
            tmp_context = f"{tmp_context}{text[start:item[1]]}[{word_id}]"
            start = item[2]
        print(tmp_context)
        return tmp_context


    # 预处理文件
    def pre_deal(self, source: str, del_content: List):
        for d in del_content:
            source = source.replace(d, '')
        # 若空格前不是点或者竖，则该空格应该被替换为点
        source = re.sub('([^།་ \\n])([ ])', r"\1་\2", source)
        source = source.replace(' ', '')
        source = source.replace(u'༌', u'་')  # 肉眼不可见，显示一样，其实不一样
        _temp = []
        tmp_list = source.splitlines()
        for _line in tmp_list:
            _temp.append(u"->་%s" % _line)

        source = '\n'.join(_temp)
        return source

    def run(self, source: str, del_content: List):
        source = self.pre_deal(source, del_content)

        text_result = self.text_count(source)
        # count_vals = []
        # for i in count_result:
        #     count_vals.append(i['count'])
        # # 出现的次数，用于颜色动态划分
        # for item in count_result:
        #     item['word'] = self.word_valid(item['word'])
        #     if item['word'] in self.flags_last_3:
        #         item['is_underline'] = True
        # text_result = text_result.replace(u"->་", "")
        # return list(count_result), text_result



if __name__ == '__main__':
    import pymongo

    n = 4
    myclient = pymongo.MongoClient("mongodb://192.168.0.61:37017")
    mydb = myclient["tibetan"]
    start = time.time()
    word_pool = mydb['word_stat_dict'].aggregate([{'$match': {'type': 'stat', 'is_exclude': False}},
                                                  {'$project': {'_id': 0, 'id': 1, 'word': 1, 'nature': 1,
                                                                'length': {'$strLenCP': "$word"}}},
                                                  {'$sort': {'length': -1}}
                                                  ])
    # word_pool = mydb['word_stat_dict'].find({'type': 'stat', 'is_exclude': False})
    result = []

    # 不参与排序
    _link = ['འི་', 'འི།', 'འུ་', 'འུ།', 'འོ་', 'འོ།']
    _tmp_result = []

    for item in word_pool:
        _key = item['word'].strip()
        _value = item['nature'].strip()
        _id = item['id']

        # 如果末尾不为་   , 末尾则加上་
        if not _key.endswith('་'):
            _key = f'{_key}་'

        if _key in _link:
            _tmp_result.append({
                'id': _id,
                'word': _key,
                'nature': _value
            })
        else:
            result.append({
                'id': _id,
                'word': _key,
                'nature': _value
            })
    save_result = result + _tmp_result
    word_pool = save_result
    print(time.time() - start)
    u = UnitStat(word_pool=word_pool)

    # source = '''བཅོམ་ལྡན་འདས་ ཀྱི་ ཡེ་ཤེས་ རྒྱས་པ འི་ མདོ་སྡེ་ རིན་པོ་ཆེ་ མཐའ་ཡས་པ་ མཐ ར་ ཕྱིན་པ་ ཞེས་ བྱ་བ་ ཐེག་པ་ ཆེན་པོ འི་ མདོ །123 བཅོམ་ལྡན་འདས་ ཀྱི་ ཡེ་ཤེས་ རྒྱས་པ འི་ མདོ་སྡེ་ རིན་པོ་ཆེ་ མཐའ་ཡས་པ་ མཐ ར་ ཕྱིན་པ་ ཞེས་ བྱ་བ་ ཐེག་པ་ ཆེན་པོ འི་ མདོ །456 བཅོམ་ལྡན་འདས་ ཀྱི་ ཡེ་ཤེས་ རྒྱས་པ འི་ མདོ་སྡེ་ རིན་པོ་ཆེ་ མཐའ་ཡས་པ་ མཐ ར་ ཕྱིན་པ་ ཞེས་ བྱ་བ་ ཐེག་པ་ ཆེན་པོ འི་ མདོ །
    # '''
    with open('./test.txt','r') as f:
        source = f.read()
    print(u.run(source,[]))
    # u.new_text_count(source)
    # source = u.pre_deal(source, [])
    # print(u.find_word(source))
    print(time.time() - start)
