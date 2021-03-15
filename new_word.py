import uuid


def new_word(db, source: str):
    word_dict_list = [x['word'] for x in db['word_stat_dict'].find({'type': 'stat'})]
    # \t、\n全部替换为空格，并将两个空格替换为1个，该替换方式无法完全避免多空格情况，所以在循环中要进行判断
    source = source.replace('\t', ' ').replace('\n', ' ').replace('  ', '')
    word_in_content = source.split(' ')
    word_in_content = word_in_content[2:]
    word_list = []
    for x in word_in_content:
        if x == '':
            continue
        elif x[-1] == '།':
            word_list.append(x[:-1] + '་')
        else:
            word_list.append(x)
    # 取差集
    new_word_list = list(set(word_list).difference(set(word_dict_list)))
    result = []
    for x in new_word_list:
        result.append({'word': x, 'id': uuid.uuid1().hex, 'is_check': False, 'context': ''})
    return result
