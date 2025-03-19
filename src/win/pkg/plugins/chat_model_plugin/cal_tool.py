import re
import os
import sys
import math
import signal
import contextlib
import multiprocessing
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../../../')))


def expression_eval(expression, limit_time=3.0):
    def unsafe_eval():
        result_value.value = ""
        try:
            with time_limit(limit_time):
                result_value.value = eval(expression)
        except TimeoutException:
            print("Timeout")
        except Exception as e:
            name = e.__class__.__name__
            print(str(name)+": "+str(e))

    manager = multiprocessing.Manager()
    result_value = manager.Value(str, "")
    p = multiprocessing.Process(target=unsafe_eval)
    p.start()
    p.join()
    return result_value.value

@contextlib.contextmanager
def time_limit(seconds):
    def signal_handler():
        raise TimeoutException("Timed out!")
    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

class TimeoutException(Exception):
    pass

class Bracket():
  def __init__(self):
      self.bracket = {')':'(', ']':'[', '}':'{', '）':'（'}
      self.left_bracket = "({["
      self.right_bracket = ")}]"
  
  def isValid(self , s: str) -> bool:
      stack = []
      for char in s:
          if char in self.left_bracket:
              stack.append(char)
          elif char in self.right_bracket:
              if len(stack)==0:
                  return False
              else:
                  if self.bracket[char]==stack[-1]:
                      stack.pop()
                  else:
                      return False
      return not stack


class SpecialChar():
    def __init__(self):
        self.inner_cal = [".", " ", "+", "-", "*", "/", "sin", "cos", "tan", "ln", "√", "lg", "log", "!", "^", "%", "°", "e", "π", 
                          "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "(", ")"]
    
    def isVaild(self, s:str) -> bool:
        for cal_ope in self.inner_cal:
            s = s.replace(cal_ope, "")
        if s:
            return False
        return True
            

class LimitNum():
    def __init__(self):
        self.max_num = 1000
    
    def isVaild(self, s:str) -> bool:
        pattern = r"([\d\.]+)!"
        matches = re.findall(pattern, s)
        for match in matches:
            if "." in match:
                return False
            if int(match) > self.max_num:
                return False
        return True


class ArrayStack():
    def __init__(self, maxSize):
        self.maxsize = maxSize
        self.stack = []
        self.top = -1
        self.simple_ope = "+-*/^$@#&_`;!"
 
    def isFull(self):
        return self.top == self.maxsize - 1
 
    def isEmpty(self):
        return self.top == -1
 
    def push(self,value):
        if self.isFull():
            return
        self.top = self.top + 1
        self.stack.append(value)
 
    def pop(self):
        if self.isEmpty():
            return
        value = self.stack.pop()
        self.top = self.top - 1
        return value
 
    def priority(self, oper):
        if oper in "$@#&_`;!":
            return 3
        elif oper in "^":
            return 2
        elif oper in "*/":
            return 1
        elif oper in "+-":
            return 0
        else:
            return -1
 
    def isOper(self, val):
        if val in self.simple_ope:
            return True
        else:
            return False
 
    def is_bracket(self, val):
        return val == "(" or val == ")"
 
    def peek(self):
        return self.stack[self.top]
 

class InfixtoSuffix():
    def __init__(self, expression):
        self.expression = expression
        self.s1 = ArrayStack(2000)
        self.s2 = [] 
        self.flag = 0
        self.index = 0
        self.data = 1
        self.keepnum = 0
 
    def change(self):
        while self.index <= len(self.expression) - 1:
            if self.s1.isOper(self.expression[self.index]) == False and self.s1.is_bracket(self.expression[self.index]) == False:
                self.keepnum = self.expression[self.index]
                while True:
                    if self.index + self.data <= len(self.expression) - 1:
                        if (self.s1.isOper(self.expression[self.index + self.data])) == False and self.s1.is_bracket(self.expression[self.index + self.data]) == False:
                            self.flag = 1
                            self.keepnum = self.keepnum + self.expression[self.index+self.data]
                            self.data = self.data + 1
                        else:
                            break
                    else:
                        break
                self.s2.append(self.keepnum)
                self.keepnum = ""
            elif self.expression[self.index] == "(":
                self.s1.push(self.expression[self.index])
 
            elif (self.expression[self.index]) == ")":
                while (self.s1.peek())!="(":
                    self.s2.append(self.s1.pop())
                self.s1.pop() 
            else:
                while (self.s1.isEmpty() == False and self.s1.priority(self.s1.peek())>=self.s1.priority(self.expression[self.index])):
                    self.s2.append(self.s1.pop())
                self.s1.push(self.expression[self.index])
            if self.flag:
                self.index = self.index + self.data
                self.flag = 0
                self.data = 1
            else:
                self.index = self.index + 1
        while self.s1.isEmpty() == False:
            self.s2.append(self.s1.pop())
        return self.s2


class Calculator():
    def __init__(self):
        self.bin_ope = "+-*/^;"
        self.una_ope = "$@#&_`!"
        self.involve_neg = (self.bin_ope + self.una_ope).replace("!", "")
        self.cons2num = {
                    "e": "2.718281",
                    "π": "3.141592",
                    "%": "/100",
                    "°": "/180*3.141592",
                      }
        self.ope2math = {
                    "^": "**",
                    "$": "math.sin",
                    "@": "math.cos",
                    "#": "math.tan",
                    "&": "math.log",
                    "_": "math.sqrt",
                    "`": "math.log10",
                      }
        self.ope2punc = {
                    "sin": "$",
                    "cos": "@",
                    "tan": "#",
                    "ln": "&",
                    "√": "_",
                    "lg": "`",
                    "log": ";",
                          }
        self.punc2ope = {v: k for k, v in self.ope2punc.items()}

    def get_final_anwser(self, expression):
        for ope in self.ope2math:
            expression = expression.replace(ope, self.ope2math[ope])

        if "!" in expression:
            expression = re.sub(r'(\d+)!', f'math.factorial(\\1)', expression)

        while ")!" in expression:
            fact_index = expression.find(")!")
            find_index = self.find_matching_left_bracket(expression, fact_index)
            expression = expression[:find_index] + "math.factorial" + expression[find_index:fact_index+1] + expression[fact_index+2:]

        if ";" in expression:
            pattern = re.compile(r";\((\d+)\)\((\d+)\)")
            expression = re.sub(pattern, r"math.log(\1,\2)", expression)
        
        res = eval(expression)
        return res

    def do_bin_cal(self, num1, num2, oper):
        num1 = int(num1) if "." not in num1 else float(num1)
        num2 = int(num2) if "." not in num2 else float(num2)
        if oper == "+":
            res =  num1 + num2
        elif oper == "-":
            res =  num1 - num2 
        elif oper == "*":
            res = num1 * num2
        elif oper == "/":
            res = num1 / num2
        elif oper == "^":
            res = num1 ** num2
        elif oper == ";":
            res = math.log(num1, num2)

        if int(res) == res:
            res = int(res)
        return str(res)

    def do_una_cal(self, num1, oper):
        num1 = int(num1) if "." not in num1 else float(num1)
        if oper == "$":
            res = math.sin(num1)
        elif oper == "@":
            res = math.cos(num1)
        elif oper == "#":
            res = math.tan(num1)
        elif oper == "&":
            res = math.log(num1)
        elif oper == "_":
            res = math.sqrt(num1)
        elif oper == "`":
            res = math.log10(num1)
        elif oper == "!":
            res = math.factorial(num1)

        if int(res) == res:
            res = int(res)
        return str(res)

    def bin_cal_replace(self, expression, num1, num2, token, res):
        if ("(" + num1+token+num2 + ")") in expression:
            expression = expression.replace("(" + num1+token+num2 + ")", res)
        elif (num1+token+num2) in expression:
            expression = expression.replace(num1+token+num2, res)

        if token == ";":
            if (token+"("+num1+")"+"("+num2+")") in expression:
                expression = expression.replace(token+"("+num1+")"+"("+num2+")", res)
            elif (token+num1+"("+num2+")") in expression:
                expression = expression.replace(token+num1+"("+num2+")", res)
            elif (token+"("+num1+")"+num2) in expression:
                expression = expression.replace(token+"("+num1+")"+num2, res)
            elif (token+num1+num2) in expression:
                expression = expression.replace(token+num1+num2, res)
        return expression

    def una_cal_replace(self, expression, num1, token, res):
        if ("(" + token + num1 + ")") in expression:
            expression = expression.replace("(" + token + num1 + ")", res)
        elif (token+num1) in expression:
            expression = expression.replace(token+num1, res)
        elif (token + "(" + num1 + ")") in expression:
            expression = expression.replace(token + "(" + num1 + ")", res)
        if token == "!":
            if (num1+token) in expression:
                expression = expression.replace(num1+token, res)
            elif ("("+num1+")"+token) in expression:
                expression = expression.replace("("+num1+")"+token, res)
        return expression

    def solveSuffix(self, suffix_list, expression):
        if len(suffix_list) < 2:
            return None
        operandStack = list()
        deal_flag = False

        for i in range(len(suffix_list)):
            token = suffix_list[i]
            if token in self.bin_ope and (not deal_flag):
                num2 = operandStack.pop()
                num1 = operandStack.pop()
                res = self.do_bin_cal(num1, num2, token)
                operandStack.append(res)
                expression = self.bin_cal_replace(expression, num1, num2, token, res)
                deal_flag = True
            elif token in self.una_ope and (not deal_flag):
                num1 = operandStack.pop()
                res = self.do_una_cal(num1, token)
                operandStack.append(res)
                expression = self.una_cal_replace(expression, num1, token, res)
                deal_flag = True
            else:
                operandStack.append(token)

        return operandStack, expression

    def round_up(self, expression):
      pattern = r"\d+\.\d+"
      matches = re.findall(pattern, expression)
      for match in matches:
        rounded = round(float(match), 3)
        expression = expression.replace(match, str(rounded))
      return expression

    def mul_padding(self, expression):
        pattern = r"([\d\.]+)([\$@#&_`;eπ\(])"
        expression = re.sub(pattern, r"\1*\2", expression)
        return expression

    def find_matching_left_bracket(self, expression, right_bracket_index):
      stack = []
      for i in range(right_bracket_index-1, -1, -1):
        if expression[i] == ')':
          stack.append(i)
        elif expression[i] == '(':
          if stack:
            stack.pop()
          else:
            return i

    def contain_ope_neg(self, expression):
        for ope in self.involve_neg:
            if (ope+"-") in expression:
                return True
        return False

    def only_num(self, expression):
        pattern = r"[\d\.]+"
        matches = re.findall(pattern, expression)
        if len(matches) == 1:
            return True
        return False

    def trans_exp(self, expression):
        for ope in self.ope2punc:
            expression = expression.replace(ope, self.ope2punc[ope])
        return expression

    def trans_exp_back(self, expression_list):
        for i in range(len(expression_list)):
            for punc in self.punc2ope:
                expression_list[i] = expression_list[i].replace(punc, self.punc2ope[punc])
            expression_list[i] = self.round_up(expression_list[i])

    def constant_replace(self, yuan_flag, expression):
        for const in self.cons2num.keys():
            if const in expression:
                yuan_flag = True
        for cons in self.cons2num:
            expression = expression.replace(cons, self.cons2num[cons])
        return yuan_flag, expression

    def add_bracket(self, expression):
        expression = re.sub(r"([\$@#&_`\;])([\d°\.]+)", r"\1(\2)", expression)
        return expression

    def check_valid(self, expression):
        if not Bracket().isValid(expression):
            return False
        if not SpecialChar().isVaild(expression):
            return False
        if not LimitNum().isVaild(expression):
            return False
        return True

    def deal_neg(self, yuan_flag, expression):
        if self.contain_ope_neg(expression):
            yuan_flag = True
            inverse_re = r"([\+\-\*/\^\$@#&_`;])-([\d\.]+)"
            expression = re.sub(inverse_re, r"\1(0-\2)", expression)

        if expression.startswith("-"):
            yuan_flag = True
            inverse_re = r"^\-([\d\.]+)"
            expression = re.sub(inverse_re, r"-1*\1", expression)
            expression =  re.sub(inverse_re, r"(0-\1)", expression)

        if "(-" in expression:
            yuan_flag = True
            expression = expression.replace("(-", "(0-")      

        return yuan_flag, expression

    def deal_expression(self, expression):
        expression = self.trans_exp(expression)
        expression = self.add_bracket(expression)
        expression = self.mul_padding(expression)
        expression_yuan, yuan_flag = expression, False
        yuan_flag, expression = self.constant_replace(yuan_flag, expression)
        yuan_flag, expression = self.deal_neg(yuan_flag, expression)
        return expression_yuan, yuan_flag, expression

    def cal(self, expression):
        try:
            if not self.check_valid(expression):
                return False, None

            expression_yuan, yuan_flag, expression = self.deal_expression(expression)
            finan_anwser = self.get_final_anwser(expression)
            suffix_exp = InfixtoSuffix(expression)
            suffix = suffix_exp.change()
            expression_list = [expression_yuan, expression,] if yuan_flag else [expression,]
            while len(suffix) > 1:
                suffix, expression = self.solveSuffix(suffix, expression)
                expression_list.append(expression)

            try:
                if float(finan_anwser) == float(suffix[0]):
                    pass
                else:
                    return False, finan_anwser
            except Exception as e:
                print(e)
                return True, finan_anwser
            
            self.trans_exp_back(expression_list)
            if self.only_num(expression_list[-1]):
                final_process = "=".join(expression_list)
                return True, final_process
            else:
                return False, finan_anwser
        except Exception as e:
            print(e)
            return False, None


def solve_inner_func(func_text):
    if not func_text:
        return '对不起，我无法回答这个问题。'
    try:
        split_lst = func_text.split(';')
        func_name = split_lst[0].replace(' ', '')

        if len(split_lst) == 2 and func_name == 'cal':
            str_expr = split_lst[1].replace(' ', '')
            _, ans = Calculator().cal(str_expr)
            if not ans:
                ans = '对不起，我无法回答这个问题。'
            else:
                ans = str(ans)
        else:
            ans = '抱歉，我无法理解问题的含义，请重新表达。'
    except:
        ans = '抱歉，我无法理解您的问题，请尝试提问一个不那么复杂或更明确的问题。'
    return ans


def tool_cal(gen_text):
    gen_text = re.sub(r'\s*<api>\s*', '<api>', gen_text)
    gen_text = re.sub(r'\s*<api_end>\s*', '<api_end>', gen_text)
    gen_text = re.sub(r'\s*<API>\s*', '<API>', gen_text)
    func_text = gen_text.replace("}<api_end>", "").replace("<api>{", "").replace("<api_end>", "").replace("<api>", "")
    func_text = re.sub(r'^[>{]*', '', func_text)
    iter_ans = solve_inner_func(func_text)
    iter_ans = iter_ans.replace('\n', '<n>')
    return iter_ans


def api_tool_hf(generator):
    first_3_flag = True
    api_flag = False
    while True:
        try:
            if first_3_flag == True:
                abnormal_res = ''
                next_1_token, _, _ = next(generator)
                if not next_1_token.endswith(('<', 'api')):
                    yield next_1_token
                    continue
                abnormal_res = next_1_token
                
                next_2_token, _, _ = next(generator)
                abnormal_res = next_2_token
                if not next_2_token.endswith(('<api', '<api>', '<api>{')):
                    yield next_2_token
                    continue
                
                next_3_token, _, _ = next(generator)
                abnormal_res = next_3_token
                next_token = next_3_token
                if next_token.endswith((" <api>{", "<api>{", " <api", "<api", "<api>")):
                    api_flag = True
                    len_api = len(next_token)
                else:
                    yield next_token
                    continue
                first_3_flag = False
                
            else:
                abnormal_res = ''
                next_token, _, _ = next(generator)
                
        except StopIteration:
            if abnormal_res:
                yield abnormal_res
            break

        if not api_flag:
            yield next_token
            continue
        else:
            str_token_cache = next_token
            print('cal tool output: ', str_token_cache)
            if not next_token.endswith("<eod>"):
                continue

    if api_flag:
        full_token = str_token_cache.replace("<eod>", "")
        cal_token = full_token[len_api:]
        tool_res_tokens = tool_cal(cal_token)
        
        res_tokens = full_token[:len_api] + tool_res_tokens
        res_tokens = res_tokens.replace("<api>{", "").replace("<api>", "")
        yield res_tokens



def api_tool_gguf(generator):
    first_3_flag = True
    api_flag = False
    token_cache = []
    while True:
        try:
            if first_3_flag == True:
                abnormal_cache = []
                next_1_token = next(generator)
                token_cache.append(next_1_token["choices"][0]["text"])
                abnormal_cache.append(next_1_token["choices"][0]["text"])
                next_token = ''.join(token_cache)
                dct_token = next_1_token
                if not next_token.endswith(('<', 'api')):
                    yield next_1_token
                    continue
                
                next_2_token = next(generator)
                token_cache.append(next_2_token["choices"][0]["text"])
                abnormal_cache.append(next_2_token["choices"][0]["text"])
                next_token = ''.join(token_cache)
                dct_token["choices"][0]["text"] = ''.join(token_cache[-2:])
                if not next_token.endswith(('<api', '<api>', '<api>{')):
                    yield dct_token
                    continue
                
                next_3_token = next(generator)
                token_cache.append(next_3_token["choices"][0]["text"])
                abnormal_cache.append(next_3_token["choices"][0]["text"])
                next_token = ''.join(token_cache)
                dct_token["choices"][0]["text"] = ''.join(token_cache[-3:])
                if next_token.endswith((" <api>{", "<api>{", " <api", "<api", "<api>")):
                    api_flag = True
                    len_api = len(next_token)
                else:
                    yield dct_token
                    continue
                first_3_flag = False
                
            else:
                abnormal_cache = []
                dct_token = next(generator)
                token_cache.append(dct_token["choices"][0]["text"])
                print('cal tool output: ', token_cache)

        except StopIteration:
            if abnormal_cache:
                abnormal_res = "".join(abnormal_cache)
                dct_token["choices"][0]["text"] = abnormal_res
                yield dct_token
            break
        
        if not api_flag:
            yield dct_token
            continue
        else:
            if next_token != '<eod>':
                continue
            
    if api_flag:
        str_token_cache = ''.join(token_cache)
        full_token = str_token_cache.replace("<eod>", "")
        cal_token = full_token[len_api:]
        tool_res_tokens = tool_cal(cal_token)
        res_tokens = full_token[:len_api] + tool_res_tokens
        res_tokens = res_tokens.replace("<api>{", "").replace("<api>", "")
        dct_token["choices"][0]["text"] = res_tokens
        yield dct_token


def api_tool_bigdl(generator):
    api_flag = False
    token_cache = []
    
    while True:
        try:
            next_token = next(generator)
            if next_token == "":
                continue
        except StopIteration:
            break
        
        if ("<api>{" in next_token or "<api" in next_token) and not api_flag:
        # if next_token in [" <api>{", "<api>{", " <api", "<api"] and not api_flag:
            api_flag = True
            token_cache.append(next_token)
            continue
        elif not ("<api>{" in next_token or "<api" in next_token) and not api_flag:
            api_flag = False
            yield next_token
            continue
        else:
            token_cache.append(next_token)
            if next_token != "<eod>":
                continue

    if api_flag:
        str_token_cache = ''.join(token_cache)
        full_token = str_token_cache.replace("<eod>", "")
        tool_res_tokens = tool_cal(full_token)
        res_tokens = tool_res_tokens + "<eod>"
        yield res_tokens


def generator(tool_flag):
    if tool_flag == "1":
        test_content = [
            "beg",
            "<api>", 
            "{", 
            "cal", 
            ";", 
            "10+2*3", 
            "}", 
            "<api_end>", 
            "<eod>"]
    elif tool_flag == "2":
        test_content = [
            "我", 
            "是", 
            "一个", 
            "粉刷匠", 
            "，", 
            "粉刷", 
            "本领", 
            "强", 
            "<eod>"]
    elif tool_flag == "3":
        test_content = [
            "",
            "<", 
            "api", 
            ">{",
            "",
            "cal", 
            ";", 
            "10+2*3", 
            "}", 
            "<api_", 
            "end>", 
            "<eod>"]
    elif tool_flag == "4":
        test_content = [
            "哈", 
            "哈", 
            "哈", 
            "哈", 
            "哈"]
    elif tool_flag == "5":
        test_content = [
            "我", 
            "我是", 
            "我是一个", 
            "我是一个粉刷匠", 
            "我是一个粉刷匠，",
            "我是一个粉刷匠，粉刷",
            "我是一个粉刷匠，粉刷本领",
            "我是一个粉刷匠，粉刷本领强",
            "我是一个粉刷匠，粉刷本领强。",]
    elif tool_flag == "6":
        test_content = [
            "beg",
            "beg<", 
            "beg<api", 
            "beg<api>", 
            "beg<api>{", 
            "beg<api>{cal", 
            "beg<api>{cal;", 
            "beg<api>{cal;10+2*3", 
            "beg<api>{cal;10+2*3}", 
            "beg<api>{cal;10+2*3}<api_end>", 
            "beg<api>{cal;10+2*3}<api_end><eod>"]

    for token in test_content:
        # yield {"choices": [{"text": token}]}
        yield token


# if __name__ == "__main__":

#     test = generator("6")
#     test_api = api_tool_hf(test)
#     while True:
#         try:
#             print(next(test_api))
#         except StopIteration:
#             break
 
      