import re, os
from rouge_score import rouge_scorer, tokenize
# from transformers import BertTokenizer


class DataUtils:
    @staticmethod
    def split_segments(statement: str):
        all_statements = []
        statement = re.sub(' +', ' ', statement.replace('\n', ' '))
        split_pattern = r'(?<!\w\.\w.)(?<![A-Z]\.)(?<![A-Z][a-z]\.)(?<! [a-z]\.)(?<![A-Z][a-z][a-z]\.)(?<=\.|\?|\!)\"*\s*\s*(?:\W*)([A-Z])'
        tmp_statements = []
        
        for s in re.split(r"(\[\d+\])", statement):
        # for s in re.split(r"[。]", statement):
            if not s:
                continue
            cites = re.findall(r"\[(\d+)\]", s)
            if not cites: # Segment
                tmp_statements.append([s, []])
            elif not tmp_statements: # Citation Mark, but no Segments
                continue
            else: # Citation Mark
                for item in cites:
                    tmp_statements[-1][1].append(int(item) - 1)
        
        for s, cite in tmp_statements:
            prefix = ""
            for ix, seg in enumerate(re.split(split_pattern, s)):
                if len(prefix) > 20:
                    all_statements.append([prefix, []])
                    prefix = ""
                prefix += seg
                if prefix and prefix[-1] in ['.!?:']:
                    prefix += " "
            if prefix:
                if all_statements and len(prefix) < 20:
                    all_statements[-1][0] += prefix
                else:
                    all_statements.append([prefix, []])
            if all_statements:
                all_statements[-1][1] += cite
        
        return [seg[0] for seg in all_statements], [seg[1] for seg in all_statements]

    @staticmethod
    def split_segments_cn(statement: str):
        all_statements = []

        p_char = r'(！|。)'
        fields = re.split(p_char, statement)  # 多分隔符分割语句
        values_0 = fields[::2]  # 只包含诗句,list[start:end:step]
        if '' in values_0:
            values_0.remove('')
        delimiters_0 = fields[1::2]  # 只包含标点

        for va,de in zip(values_0, delimiters_0):
            all_statements.append(va+de)
        if all_statements == []:
            all_statements = [statement]
        if len(fields)%2!=0 and len(fields[-1]):
            all_statements.append(fields[-1])

        return all_statements, [[] for seg in all_statements]

    @staticmethod
    def matching_score(all_statements, references):
        def remove_stopwords(stmt: str):
            stmt = tokenize.tokenize(stmt, None)
            ret = []
            for item in stmt:
                if item in stopwords:
                    continue
                ret.append(item)
            return " ".join(ret)
            # return "".join(ret)  #中文
        
        # all_statements = [remove_stopwords(item) for item in all_statements]
        # references = [remove_stopwords(item) for item in references]
        
        # return None

        # web_files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        # embeddings_model_path = os.path.join(web_files_dir, 'bert_pretrained')

        # tokenizer = BertTokenizer.from_pretrained(embeddings_model_path)

        scorer = rouge_scorer.RougeScorer(['rouge1'], use_stemmer=True)
        all_scores = []
        for statement in all_statements:
            # if len(tokenize.tokenize(statement, None)) < 5:
            #     all_scores.append([0] * len(references))
            #     continue
            ref_score = []
            for idx, ref in enumerate(references):
                rouge = scorer.score(ref, statement)['rouge1'].precision
                # print(rouge)
                ref_score.append(rouge)
            all_scores.append(ref_score)
        return all_scores
    
    @staticmethod
    def get_ideal_citations(all_scores, raw_citations, citation_threshold, all_statements, extra_bonus=0.3):
        
        assert len(all_scores) == len(raw_citations)
        
        ideal_citations = []
        for seg_idx, scores in enumerate(all_scores):
            idc = []
            best_idx = 0
            best_scr = 0
            for idx, score in enumerate(scores):
                if idx in raw_citations[seg_idx]:
                    score += extra_bonus / len(raw_citations[seg_idx])
                if score >= citation_threshold:
                    idc.append(idx)
                if score > best_scr:
                    best_idx = idx
            if len(idc) == 0 and len(raw_citations[seg_idx]) > 0:
                idc.append(best_idx)

            # 以'\n'开头说明是新的一段。上一段的引用不需要改变
            if not all_statements[seg_idx].startswith('\n') and len(ideal_citations) > 0 and set(ideal_citations[-1]) <= set(idc):  #set(b) <= set(a)) # a是否包含b，<= 则表示是否是子集
                ideal_citations[-1] = []
            elif not all_statements[seg_idx].startswith('\n') and len(ideal_citations) > 0 and set(idc) <= set(ideal_citations[-1]):
                ideal_citations[-1] = list(set(ideal_citations[-1]) - set(idc))

            ideal_citations.append(idc)
        return ideal_citations
    
    @staticmethod
    def recompose(all_statements, raw_citations, references, sep=" ", citation_threshold=0.75) -> str:
        scores = DataUtils.matching_score(all_statements, references)
        ret = ""
        ideal_citations = DataUtils.get_ideal_citations(scores, raw_citations, citation_threshold, all_statements)

        for seg, cit in zip(all_statements, ideal_citations):
            # judge if seg[0] is alphanumeric
            if ret and ret[-1] == "]" and seg and seg[0].isalnum():
                ret += sep
            ret += seg
            for c in cit:
                ret += "[%d]"%(c+1)
            if ret and ret[-1] in ".!?:":
                ret += sep
        return ret.strip()

class Stopwords:
    @staticmethod
    def load():
        #英文
        # src = [
        #     "./stopwords/english",
        #     "./stopwords/explaination",
        # ]
        #中文
        src = [
            os.path.join(os.path.dirname(__file__), "stopwords/chinese")
        ]
        ret = []
        for item in src:
            with open(item, "r", encoding='utf-8') as f:
                ret += [word.strip() for word in f.readlines()]
        return ret


stopwords = set(Stopwords.load())


def citation_correction(original_answer, references):
    cites = re.findall(r"\[(\d+)\]", original_answer)
    if len(cites)>0:
        segments, raw_cite = DataUtils.split_segments(original_answer)
    else:
        segments, raw_cite = DataUtils.split_segments_cn(original_answer)
    
    return DataUtils.recompose(segments, raw_cite, references)


if __name__ == "__main__":
    original_answer = "泰山位于中国山东省中部，隶属于泰安市[4]，是世界文化和自然双遗产、国家5A级旅游景区。"
    references = ["泰山是世界文化和自然双遗产、国家5A级旅游景区。", "泰山位于中国山东省中部，隶属于泰安市。"]
    answer = citation_correction(original_answer, references)
    print(answer)
    pass
