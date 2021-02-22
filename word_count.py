from collections import Counter
from utils.minio_tools import MinioUploadPrivate
import uuid
import traceback
import time


class WordCountError(Exception):
    def __init__(self):
        self.msg = 'content为空'


class WordCount:
    def __init__(self, conn, color_total: int = 6):
        self.content = None
        self.conn = conn
        self.word_stat_in_content = None
        self.color_total = color_total
        self.start_time = time.time()
        # self.time = time.time()

    def get_content(self, _id):
        # start_time = time.time()
        result = self.conn['work_history'].find_one({'id': _id})
        self.content = MinioUploadPrivate().get_object(full_path=result['parsed']).decode(encoding='utf-8')
        # logger.info('get_content used: %s' % str(start_time - self.time))

    def split_and_count_file_content(self, split: str = ' '):
        '''
        文档内容已经以空格进行过分词，所以根据空格分隔content为list，并轮询进行计数
        :return: 组装成一个字符为key，该字符计数为value的字典
        '''
        # start_time = time.time()
        # logger.info(self.content)
        content_list = self.content.split(split)
        # Counter的结果类型继承dict的属性
        self.word_stat_in_content = Counter(content_list)
        # 若content为空字符串，报"后台异常"
        if not self.word_stat_in_content:
            raise WordCountError
        # logger.info('split_and_count_file_content used: %s' % str(start_time - self.time))
        return self.word_stat_in_content

    def colouration(self, word_stat_in_content):
        '''
        动态染色，无具体色号，共6种，以int类型标注
        :return: 频率为key，颜色编号为value的字典
        '''
        if not word_stat_in_content:
            # logger.info(
            #     'function "colouration" in class "WordCount" do not find self.word_stat_\
            #     in_content and run function "split_and_count_file_content"')
            self.split_and_count_file_content()
        colouration_result = {}
        # start_time = time.time()
        # 得到每种频率
        frequency = list(set(word_stat_in_content.values()))
        frequency.sort(reverse=True)
        step = len(frequency) / self.color_total
        for x in range(len(frequency)):
            # 是否整除不影响结果
            if x < step:
                colouration_result[frequency[x]] = 0
            elif x < 2 * step:
                colouration_result[frequency[x]] = 1
            elif x < 3 * step:
                colouration_result[frequency[x]] = 2
            elif x < 4 * step:
                colouration_result[frequency[x]] = 3
            elif x < 5 * step:
                colouration_result[frequency[x]] = 4
            else:
                colouration_result[frequency[x]] = 5
        # logger.info('colouration used: %s' % str(start_time - self.time))
        return colouration_result

    def word_count(self, _id):
        '''
        根据文档已经统计出的词进行查询，得到List[BaseModel]，遍历该列表
        :return: [{'word': str, 'nature': str, 'count': int, 'color': str, 'word_index': str}]
        '''
        try:
            if not self.content:
                # logger.info('run "get_content"')
                self.get_content(_id=_id)
            if not self.word_stat_in_content:
                # logger.info(
                #     'function "word_count" in class "WordCount" do not find self.word_stat_in_content \
                #     and run function "split_and_count_file_content"')
                self.split_and_count_file_content()
            # start_time = time.time()
            query = {
                'word': {'$in': list(self.word_stat_in_content.keys())},
                'type': 'stat',
                'is_exclude': False
            }
            # 此时查出来的的list都是有效数据
            result = self.conn['word_stat_dict'].find(query)
            data_word_stat_dict = [x for x in result]
            result = []
            word_stat_dict = {}
            replace_dict = {}
            for x in data_word_stat_dict:
                word_stat_dict[x['word']] = self.word_stat_in_content[x['word']]
                result.append({
                    'id': x['id'],
                    'word': x['word'],
                    'nature': x['nature'],
                    'count': self.word_stat_in_content[x['word']],
                })
                replace_dict[x['word']] = x['id']
            # logger.info('word_count used: %s' % str(start_time - self.time))
            colouration_result = self.colouration(word_stat_in_content=word_stat_dict)
            for x in result:
                x['color'] = colouration_result[x['count']]
            result.sort(key=lambda x: x['count'], reverse=True)
            # 生成替换后的模板
            for key, value in replace_dict.items():
                self.content = self.content.replace(key, '[' + value + ']')
            # logger.info(self.content)
            return result, self.content
        except Exception as e:
            traceback.print_exc()
            print(e)
            return None

    def new_word(self, _id):
        '''
        传入word_history的id，获取到文章内容self.content，分词得到word_stat_in_content，查询数据库后遍历文章(list)做差集，即为新词
        取上下文算法：用序列遍历原文章list，取到新词时for循环组装上下文
        :return: [{'word': str, 'context': str}]
        '''
        try:
            if not self.content:
                self.get_content(_id=_id)
            if not self.word_stat_in_content:
                self.split_and_count_file_content()
            query = {
                'word': {'$in': list(self.word_stat_in_content.keys())},
                'type': 'new',
                'is_exclude': False
            }
            result = self.conn['word_stat_dict'].find(query)
            query = {
                'word': {'$in': list(self.word_stat_in_content.keys())}
            }
            result_self = self.conn['self_dict'].find(query)
            # 组装元素为word的列表
            data_word_stat_dict = [x['word'] for x in result]
            # 自有词典与平台词典取并集
            for x in result_self:
                data_word_stat_dict.append(x['word'])
            data_content_list = self.content.split(' ')
            new_word = []
            # new_word_list是用来排重的，因为new_word会是嵌套结构，判断是否重复比较复杂
            new_word_list = []
            word_index = 0
            # 每轮询一个元素，根据该元素长度，递增索引，取上下文时根据该索引截取原文，根据||分隔，从后往前取两个。后文取法同理
            for x in range(len(data_content_list)):
                word_index += len(data_content_list[x])
                # 该词为生词，并且若该词已经统计过，则不再重复统计
                if data_content_list[x] not in data_word_stat_dict and data_content_list[x] not in new_word_list:
                    _id = uuid.uuid1().hex
                    # 将新词替换为id
                    upward = self.content[:word_index].split('།།')[-2:]
                    upward[1] = upward[1][:-len(data_content_list[x])] + '[' + _id + ']'
                    downward = self.content[word_index:].split('།།')[:2]
                    new_word.append({
                        'id': _id,
                        'word': data_content_list[x],
                        'context': ' '.join(upward + downward)
                    })
                    new_word_list.append(data_content_list[x])
            # 将新词从长到短排序，文章已经做过分词，所以不用考虑交叉匹配的错误
            new_word.sort(key=lambda x: len(x['word']), reverse=True)
            # 遍历new_word列表，依次replace
            for x in new_word:
                if '\n' in x['word']:
                    x['word'].replace('\n', '')
                if '\r' in x['word']:
                    x['word'].replace('\r', '')
                if '\t' in x['word']:
                    x['word'].replace('\t', '')
                if x['word'] == '':
                    new_word.remove(x)
                    continue
                self.content = self.content.replace(x['word'], '[' + x['id'] + ']')
                # logger.info(self.content)
            return new_word, self.content
        except Exception as e:
            traceback.print_exc()
            print(e)
            return None
