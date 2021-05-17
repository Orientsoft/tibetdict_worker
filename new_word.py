import uuid
from typing import List


class NewWord:
    def __init__(self, word_pool: List):
        self.word_pool = word_pool

    @staticmethod
    def word_format(word):
        if not word:
            return ''
        word = word.replace('་་','་')
        if word[-1] not in ['།', '་']:
            return f'{word[:-1]}་'
        else:
            if word.endswith('་'):
                return word
            else:  # 以'།'结尾
                if word[:-1].endswith('་'):
                    return word[:-1]
                else:
                    return f'{word[:-1]}་'

    def pre_deal(self, source, del_char: List = None):
        source = source.replace('\t', ' ').replace('\n', ' ').replace('\r', '').replace('  ', ' ')
        # 人为加入的字符需去掉
        for d in del_char:
            source.replace(d, '')
        word_in_content = source.split(' ')
        word_in_content = word_in_content[2:]
        word_list = [self.word_format(x) for x in word_in_content]
        return word_list

    def run(self, source, del_char: List = None):
        result = []
        # 取差集
        result_word = self.pre_deal(source, del_char)
        new_word_list = list(set(result_word).difference(set(self.word_pool)))
        for x in new_word_list:
            if not x:
                continue
            result.append({'word': x, 'id': uuid.uuid1().hex, 'is_check': False, 'context': ''})
        return result
