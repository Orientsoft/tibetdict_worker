#!coding=utf-8
from typing import List
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading
import re, string
from flashtext import KeywordProcessor


class UnitStat:
    flags_head = [' ', ']', u']', u'་', u'།']
    flags_head_byte = [160]

    flags_last_0 = [u'་', u'འི་', u'འུ་', u'འོ་', u'ས་', u'ར་']
    flags_last_1 = [u'།', u'འི།', u'འུ།', u'འོ།', u'ས།', u'ར།']
    flags_last_2 = ['འི', 'འུ', 'འོ', 'ས', 'ར']
    flags_last_3 = [u'འི', u'འུ', u'འོ']
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

        word_id_dict = {}  # key:word ,value:word_id
        word_nature_dict = {}  # key:word,value:nature
        keywords_found = []
        # 遍历词库
        keyword_processor = KeywordProcessor()
        keyword_processor.set_non_word_boundaries(set(string.digits))
        for item in self.word_pool:
            # 词典id
            word_id = item['id']
            # 词
            word = item['word'].strip()
            # 藏语原因，去掉末尾的点
            word = word[:-1]
            # 词性
            nature = item['nature'].strip()

            word_id_dict[word] = word_id
            word_nature_dict[word] = nature
            # import！！！此处不能替换
            keyword_processor.add_keyword(word)

            # 搜索词的结果，词必须拥有边界才会被搜索， \w [A-Za-z0-9_] 不会作为词的边界，其他字符均为词的边界
        keywords_found = keyword_processor.extract_keywords(text, span_info=True)
        # 修正结果,词的
        correct_words = []
        for item in keywords_found:
            word = item[0]
            start = item[1]
            end = item[2]
            if word in self.flags_last_3:
                correct_words.append(item)
            else:
                _check_end_0 = text.find(u'་', end) + 1
                _check_end_1 = text.find(u'།', end) + 1

                _last_flag_0 = text[end:_check_end_0]
                _last_flag_1 = text[end:_check_end_1]

                _check_begin = text[start - 1]

                # print(_check_begin, '========', word, '========', _last_flag_0, '========', _last_flag_1)
                # 如果该词的前部分是]等特殊，且后部分为特殊的几个词。则也计入词频
                if (ord(_check_begin) in self.flags_head_byte) and (
                        _last_flag_0 in self.flags_last_0 or _last_flag_1 in self.flags_last_1):
                    correct_words.append(item)
                else:
                    print(f"{_check_begin}{word}{_last_flag_0}")
                    print(f"{_check_begin}{word}{_last_flag_1}")
                    print('exclude item:', item)
        # 替换文本
        # new_keyword_processor = KeywordProcessor()
        # for r in correct_words:
        #     new_keyword_processor.add_keyword(r, f"[{word_id_dict.get(r)}]")

        # result_context = new_keyword_processor.replace_keywords(text)
        # 处理连词特殊情况，flags_last_3 ['འི', 'འུ', 'འོ']
        # kp = KeywordProcessor()
        # for lian_word in self.flags_last_3:
        #     kp.add_keyword(lian_word, f"[{word_id_dict.get(lian_word)}]")
        print(correct_words)

        # result_context = kp.replace_keywords(result_context)
        # 词，开始位置，结束位置 and 词库的dict
        return correct_words, word_id_dict, word_nature_dict

    def text_count(self, text: str):
        # [('བཅོམ་ལྡན་འདས', 3, 15)]  , {'བཅོམ་ལྡན་འདས':'id'}
        # tmp_context = self.new_find_word(text)
        word_found_list, word_id_dict, word_nature_dict = self.new_find_word(text)
        tmp_context = ''
        start = 0
        begin_list = []
        for item in word_found_list:
            begin_list.append(item[1])
            word_id = word_id_dict.get(item[0])
            tmp_context = f"{tmp_context}{text[start:item[1]]}[{word_id}]"
            start = item[2]
        # print(begin_list)
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
        print(source)

        text_result = self.text_count(source)
        text_result = text_result.replace(u"->་", "")
        # print(text_result)
        # count_vals = []
        # for i in count_result:
        #     count_vals.append(i['count'])
        # # 出现的次数，用于颜色动态划分
        # for item in count_result:
        #     item['word'] = self.word_valid(item['word'])
        #     if item['word'] in self.flags_last_3:
        #         item['is_underline'] = True
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

    source = '''
    བཅོམ་ལྡན་འདས་ཀྱི་ཡེ་ཤེས་རྒྱས་པའི་མདོ་སྡེ་རིན་པོ་ཆེ་མཐའ་ཡས་པ་མཐར་ཕྱིན་པ་ཞེས་བྱ་བ་ཐེག་པ་ཆེན་པོའི་མདོ། [151a][151a.1]ཞིག་གོང་ན་ཞི་བ་ཉིད་དང་། གྱ་ནོམ་པ་ཉིད་ཡོད་དོ་སྙམ་ནས་དེས་བསམས་ཏེ་ རྟོག་པ་མེད་པའི་བསམ་གཏན་ཐོབ་ནས་དེ་འདི་སྙམ་དུ་གྱུར་ཏེ། གང་རྟོག་པ་དང་དཔྱོད་པ་དག་མི་འབྱུང་བ་འདི་ནི། མྱ་ངན་ལས་འདས་པ་ཡིན་ཏེ། འདི་ནི་ཞི་བའོ། །འདི་ནི་གྱ་ནོམ་པའོ། །གང་རྟོག་པ་དང་དཔྱོད་[151a.2]པ་དག་མེད་པ་དེ་ཡང་དང་ཡང་དུ་སྐྱེ་བར་མི་འཇུག་ལ་ཉེ་བར་ལེན་པ་ཅུང་ཟད་ཀྱང་མེད་དེ་འདི་ནི་ཕུང་པོ་ལྷག་མ་མེད་པའི་དབྱིངས་སུ་མྱ་ངན་ལས་འདའོ་སྙམ་ནས་དེ་ཏིང་ངེ་འཛིན་དེ་ལས་ལངས་ནས། སྲོག་ཆགས་འབུམ་ཕྲག་དྲུག་བཟོད་པ་འདི་ལ་བཙུད་དོ། །དེ་དག་ཀྱང་འདི་སྙམ་དུ་གྱུར་ཏེ།  རྟོག་པ་དང་[151a.3]དཔྱོད་པ་འདི་དག་སྤངས་ན་དེའི་སྐྱེ་བ་མི་འཇུག་སྟེ་དེ་ཡང་དང་ཡང་དུ་སྐྱེ་བ་མི་འཇུག་པ་འདི་ནི་མྱ་ངན་ལས་འདའ་བ་ཐོབ་བོ་སྙམ་མོ། །དེ་ལྟར་བཟོད་པ་དང་སྣང་བ་ལ་དགའ་བ་དེ་དག་ལ་འོད་གསལ་གྱི་གཞལ་མེད་ཁང་དག་བྱུང་བར་གྱུར་ཏོ། །དེ་ལྟར་གཞལ་མེད་ཁང་དེ་དག་མཐོང་ནས་འདི་སྙམ་[151a.4]དུ་གྱུར་ཏེ།  ༢།Toh.4420Aབརྡ་སྤྲོད་པ་པཱ་ཎི་ནིའི་འགྲེལ་པ་རབ་ཏུ་བྱ་བ་ཤིན་ཏུ་རྒྱས་པ་ཞེས་བྱ་བ།སྣ་ཚོགས།ཏོ༢༧།བ[DD]༄༅༅།།ཨོཾ་སྭསྟི་པྲ་ཛཱ་བྷྱཿ།བླ་མ་དང་མགོན་པོ་འཇམ་པའི་དབྱངས་ལ་སྒོ་གསུམ་གུས་པས་ཕྱག་འཚལ་ལོ།།འི
    '''
    # with open('./test.txt', 'r') as f:
    #     source = f.read()
    print(u.run(source, []))
    # u.new_text_count(source)
    # source = u.pre_deal(source, [])
    # print(u.find_word(source))
    print(time.time() - start)
