#!coding=utf-8
from typing import List
import time


class UnitStat:
    flags_head = [' ', ']', u']', u'་', u'།']
    flags_head_byte = [160]

    flags_last_0 = [u'་', u'འི་', u'འུ་', u'འོ་', u'ས་', u'ར་']
    flags_last_1 = [u'།', u'འི།', u'འུ།', u'འོ།', u'ས།', u'ར།']
    flags_last_2 = [u'འི', u'འུ', u'འོ', u'ས', u'ར']
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
            word = word[:-1]
            # 词性
            nature = item['nature'].strip()

            _offset = 0

            while True:

                _begin = text.find(word, _offset)

                if _begin > -1:
                    _offset = _begin + 1

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
        _begin_list, _begin_word, _word_in_pool = self.find_word(text)

        _word_count_map = {}  # {'some':{'word':'some','nature':'','count':1,''}}
        _string_buffer = []

        _index = len(_begin_list) - 1
        _last = len(text) - 1
        while _index >= 0:
            # 起始点
            _begin = _begin_list[_index]
            # 内容
            _word = _begin_word[_begin]
            # 结束点
            _end = _begin + len(_word)
            # 词性
            _nature = _word_in_pool[_word][1]

            _string_buffer.insert(0, text[_end:_last])
            _string_buffer.insert(0, ']')
            _string_buffer.insert(0, _word_in_pool[_word][0])
            _string_buffer.insert(0, '[')

            if _word in _word_count_map:
                _count_row = _word_count_map[_word]
                _count_row['count'] = _count_row['count'] + 1
            else:
                _count_row = {'word': _word + u'་', 'nature': _nature, 'count': 1,
                              'id': _word_in_pool[_word][0]}

            _word_count_map[_word] = _count_row

            _last = _begin

            _index = _index - 1

        _string_buffer.insert(0, text[:_last])
        result_text = ''.join(_string_buffer)

        return _word_count_map.values(), result_text

    def run(self, source: str):
        source = source.replace(' ', '')
        source = source.replace(u'༌', u'་')  # 肉眼不可见，显示一样，其实不一样
        _temp = []
        tmp_list = source.splitlines()
        for _line in tmp_list:
            _temp.append(u"->་%s" % _line)

        source = '\n'.join(_temp)

        count_result, text_result = self.text_count(source)
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


if __name__ == '__main__':
    # import pymongo
    #
    # myclient = pymongo.MongoClient("mongodb://192.168.0.61:37017")
    # mydb = myclient["tibetan"]
    # start = time.time()
    # word_pool = mydb['word_stat_dict'].aggregate([{'$match': {'type': 'stat', 'is_exclude': False}},
    #                                               {'$project': {'_id': 0, 'id': 1, 'word': 1, 'nature': 1,
    #                                                             'length': {'$strLenCP': "$word"}}},
    #                                               {'$sort': {'length': -1}}
    #                                               ])
    # u = UnitStat(word_pool=word_pool)
    # with open('./data/0a1cf472a154d6ab9044a352329db162.txt', 'r') as f:
    #     source = f.read()
    # print(time.time() - start)
    # print(u.run(source))
    # print(time.time() - start)
    import re
    content = '''༩༦།Toh.2785གསང་[12006]་མྱུར་[21390]་[7069][43027]་[14056]་[5886]།
                [9841]།ནུ
                ༡༥༢།ན༄༅།[30399]།[27677]་[15194]་[32857]་ཕྱུག་[46546]་[6217]་[5562]་[47783]་[39946]་[27289]་[46703]་[29517]་འཚལ་[47783]།[30399]།[12006]་[27289]ས་ཤིན་[17565]་[15905]ས་[7719][43027]།[30399]།[6094]ས་[49855]་[45273]་[17565]་[20753]་[30686][43027]་[38601]།[30399]།[51850]་[46546]་[9883]་
                ༡༥༢།བརྟག་འབབ་[27439]།[30399]།[51154]་[12006]་[5562]་[47783]་བསྐོར་[30971]་[31567]།[30399]།དྲཱེཿཨོཾ་ཨཱཿཧྲཱིཿཧཱུཾ།པླཀྵ་[43020]་[31770]་ཆུབ་[48427]་[47783]་[43020]།[30399]།[21769]་[41567]་རྟག་[17565]་[46546]་[6217]ས་བསྐྱོད།[30399]།[3228]་དོག་[22493]་བཟང་[38601]་པའང་[46106]་[30399]།བསྲུང་[30686]་[31567]ས་[25321]ས་[5562]་[47783]་བཅལ་[30399]།[12308]་[37273]་[44791]་[30971]་སླ་[30686]་[43740]།[30399]།བཟོ་[12806]ས་[18580]་པདྨོས་[39270]།[30399]།[10723]་[30399]་[30014]་[46703]་ནི་[24412]་རྗེ་[43740]།[30399]།རལ་[6933]་[35104]་བཟད་[42652]ས་[31567][43102]།[30399]།[29332]་[32341]་[6094]ས་[49855]་[30399]ས་བོན་[46703]ས།[30399]།[8468]་[46546]་[6217]་[5562]་[47783]་[12287]།[30399]།རྩིབས་[26800]་[46703]་ནི་[48682]ས་[45273]་[19628]།[30399]།[44391]་གྱུར་[12006]་གྲུབ་[52401]་[36044]་བསམ།[30399]།[11531]ས་[21110]་[32025]་[46516]་གཞུག་[27289]་[43740]ས།[30399]།[42564]་[32025]་བསྐྱེད་[46703]་[14585]ས་མཆོད།[30399]།[45014]་[16182]་[5562]་[47783]་[39946]་བསྒོམས་[25321]ས།[30399]།[43220]་བཀྱེ་[12006]་བཟླས་[5562]་[47783]་བསྐོར།[30399]།[19951]་[51376]་[20276]་[35005]་[10723]་[37600]་[10764]།[30399]།[51154]་[12006]་མྱུར་[21390]་གྲུབ་[24068]ས།[30399]།གསོལ་བཏབ་[46546]་[46703]་[1134]་བསྒོ་[18820]།[30399]།[45014]་[16182]་[12308]་བདེ་[28423]་[27439]་[31567]།[30399]།[5953]་[21390]་[5562]་[47783]་[45273]་[5731]།[30399]།[19812]ས་རྗེ་[30399]་[13988]་རིག་[27289][43027]་[20648]ས།[30399]།སྒྲུབ་[27546][43027]་[11159]་འཇིག་བྱེད་[27289]།[30399]།དེར་ནི་སྡིག་ལྡན་[35104]་བརྟེན་[26001]།[30399]།[21769]་[18538]་[5562]་[47783]་[14041]་[45014]་[16182]་འཕགས་[27289]་[28431]་[44884]ས་[42584]ས་[547]་[20648]ས་[45770]་[11916]་[12733]་[30399]་[37600]་[11916]་[42437]་[27439]་མཛད་[27289]་ནི་[21183]་[38626]་[12287]་[26800]་[547]ས་[19628]་[44018]་[27439]་བལྟ་[30971]་[31567][43102]།[30399]།[35821]་[17599]་[46703]་[50424]ས་[27289][43027]་[30399]་[14585]་[14878]་[17269]་[27289]་[46703]་[5953]་[41735]་[27289][43027]་[40935]ས་[47675]་[47783]་[21110]་[17339]་[35104]་[31567][43102]།[30399]།[3228]་[25321]་[34686]་[20237]་[30686]་[30146]་[45273]་[21110]་[30399]།[7907][43027]་[37600]་[30686]་[13909]་[19628]་ཅད་[46703]་[30772]་ཡོད་[27289]་[21110]་[30399]།བརྩོན་[27289]་ལྷུར་[31567][43102]།[30399]།[906][43027]་[30052]་[12482]་[6217]ས་[17393]་[19628]་ཅད་[44391]་[49855]་རྫོགས་[27439]་འགྱུར་[17581]།[30399]།[23768]་[46703]་[20090]་[30399]་[35104]་[31567][43102]།[30399]།[27677]་ལྡན་[32533]་[34686][43027]་[34976]་[10943]་ཟབ་[36044][43027]་[22595]།[30399]།[5953]་[20408]་[1965]་[11159]་མེད་[27439]་ནི།[30399]།[51154]་[12006]་[10604]་[47535]་མེད་[48618]་[12287]་[6684]།[30399]།འཁྲུལ་[5562]་[15194]་མགོན་[16182]་[46703]ས་[41121]་[35680]།[30399]།[51154]་[12006]་མྱུར་[21390]་[7069][43027]་[14056]་[5886]་རྫོགས་[50278]།[30399]།
                '''
    # print(re.search(r'^[A-Za-z0-9]+$','231231ab123213ab123'))
    # print(re.fullmatch(r'^[A-Za-z0-9]+$','231231ab123213ab123'))
    print(re.findall(r'\](\S)\[',content))

