#!coding=utf-8
from typing import List
import time
import uuid
import re


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

    def color_divide(self, vals: List[int]):
        vals.sort(reverse=True)
        _tmp_length = int(len(vals) / self.color_num)
        colouration_result = {}
        for x in range(len(vals)):
            # 是否整除不影响结果
            if x < _tmp_length:
                colouration_result[vals[x]] = 0
            elif x < 2 * _tmp_length:
                colouration_result[vals[x]] = 1
            elif x < 3 * _tmp_length:
                colouration_result[vals[x]] = 2
            elif x < 4 * _tmp_length:
                colouration_result[vals[x]] = 3
            elif x < 5 * _tmp_length:
                colouration_result[vals[x]] = 4
            else:
                colouration_result[vals[x]] = 5
        return colouration_result

    def find_word(self, text: str):
        _word_in_pool = {}  # {'some':['id','名词']}
        _begin_word = {}  # {'3':'some'}  3为单词的起始点

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

            _offset = 0

            while True:

                _begin = text.find(word, _offset)

                if _begin > -1:
                    _offset = _begin + len(word)

                    # 单个词
                    if word in self.flags_last_3:
                        if _begin not in _begin_word:
                            _begin_word[_begin] = word
                            _word_in_pool[word] = [word_index, nature]
                    else:
                        _end = _begin + len(word)  # 词结尾的位置
                        _check_end_0 = text.find(u'་', _end) + 1
                        _check_end_1 = text.find(u'།', _end) + 1

                        _last_flag_0 = text[_end:_check_end_0]
                        _last_flag_1 = text[_end:_check_end_1]

                        _check_begin = text[_begin - 1]
                        # 如果该词的前部分是]等特殊，且后部分为特殊的几个词。则也计入词频
                        if (ord(_check_begin) in self.flags_head_byte) and (
                                _last_flag_0 in self.flags_last_0 or _last_flag_1 in self.flags_last_1):
                            if _begin in _begin_word:
                                if len(word) > len(_begin_word[_begin]):
                                    _begin_word[_begin] = word
                                    _word_in_pool[word] = [word_index, nature]
                            else:
                                _begin_word[_begin] = word
                                _word_in_pool[word] = [word_index, nature]
                else:
                    break
        _begin_list = list(_begin_word.keys())  # set to list
        _begin_list.sort()

        _index = 1
        _cross_count = 0

        while _index < len(_begin_list):
            _index_begin = _begin_list[_index]
            _index_word = _begin_word[_index_begin]
            _index_end = _index_begin + len(_index_word)

            _i = _index - 1
            _i_begin = _begin_list[_i]
            _i_word = _begin_word[_i_begin]
            _i_end = _i_begin + len(_i_word)

            if _i_end > _index_begin:
                del _begin_word[_index_begin]
                del _begin_list[_index]

                _cross_count = _cross_count + 1

            else:
                _index = _index + 1
        # 所有的起始点，起始点对应的单词，词的词性及id
        return _begin_list, _begin_word, _word_in_pool

    def text_count(self, text: str):
        start = time.time()
        _begin_list, _begin_word, _word_in_pool = self.find_word(text)
        print('找词所花时间:', time.time() - start)
        word_count_map = {}  # {'some':{'word':'some','nature':'','count':1,''}}
        result_text = ''
        start = 0
        for pos in _begin_list:
            word = _begin_word[pos]
            word_id = _word_in_pool[word][0]
            nature = _word_in_pool[word][1]
            # 组装最终context
            result_text = f"{result_text}{text[start:pos]}[{word_id}]"
            start = pos + len(word)
            # 计算词频
            if word in word_count_map:
                _count_row = word_count_map[word]
                _count_row['count'] = _count_row['count'] + 1
            else:
                _count_row = {'word': word + u'་', 'nature': nature, 'count': 1,
                              'id': word_id}

            word_count_map[word] = _count_row
        return word_count_map.values(), result_text

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
        start = time.time()
        count_result, text_result = self.text_count(source)
        print('组装+找词:', time.time() - start)
        count_vals = []
        for i in count_result:
            count_vals.append(i['count'])
        # 出现的次数，用于颜色动态划分
        color = self.color_divide(list(set(count_vals)))
        for item in count_result:
            item['color'] = color.get(item['count'])
            item['word'] = self.word_valid(item['word'])
            if item['word'] in self.flags_last_3:
                item['is_underline'] = True
        text_result = text_result.replace(u"->་", "")
        return list(count_result), text_result

    def run_new_word(self, source: str, del_content: List):
        source = self.pre_deal(source, del_content)

        _begin_list, _begin_word, _word_in_pool = self.find_word(source)
        # print(_begin_list)
        # print(_begin_word)

        _string_buffer = []
        _start = 0
        result = []
        result_word = {}
        for pos in _begin_list:
            _word = _begin_word[pos]
            new_word = source[_start:pos]
            # TODO 所有不统计的特殊情况都可以在这里判断，_end_content同理
            if new_word == '->་':
                continue
            elif '->་' in new_word:
                new_word = new_word.replace(u'->་', '')
            if new_word in self.not_new_word:
                _string_buffer.append(new_word)
            # new_word是新词，且未统计过
            elif new_word not in result_word.keys():
                _id = uuid.uuid1().hex
                # 0:3 新词
                _string_buffer.append(f'[{_id}]')
                result.append({
                    'id': _id,
                    'word': new_word,
                    'context': ''
                })
                result_word[new_word] = _id
            else:
                _string_buffer.append(f'[{result_word[new_word]}]')
            _start = pos + len(_word)
            # 原有词
            _string_buffer.append(_word)
        # 末尾
        _end_content = source[_start:]
        if _end_content == '->་':
            pass
        elif '->་' in _end_content:
            _end_content = _end_content.replace('->་', '')
        elif _end_content in self.not_new_word:
            _string_buffer.append(_end_content)
        # new_word是新词，且未统计过
        elif _end_content not in result_word.keys():
            _id = uuid.uuid1().hex
            # 0:3 新词
            _string_buffer.append(f'[{_id}]')
            result.append({
                'id': _id,
                'word': _end_content,
                'context': ''
            })
            result_word[_end_content] = _id
        else:
            _string_buffer.append(f'[{result_word[_end_content]}]')

        result_text = ''.join(_string_buffer)
        result_text = result_text.replace(u"->་", "")

        return list(result), result_text


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
    print(u.run(source, []))
    # with open('./test.txt','r') as f:
    #     source = f.read()
    # u.run(source, [])
    print(time.time() - start)
