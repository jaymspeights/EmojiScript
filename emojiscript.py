import sys
import parser
import re

EQUAL, GREATER, LESSER, INEQUAL, INTEGER, SOP, EOP, VARIABLE, FUNCTION, SYSCALL, CONTROL, COMPARISON, MAIN, ANON, END, EOF = "EQUAL","GREATER","LESSER","INEQUAL", "INTEGER", "STATEMENT OP", "EXPRESSION OP", "VARIABLE", "FUNCTION", "SYSCALL", "CONTROL", "COMPARISON", "MAIN", "ANON", "END", "EOF"
WHILE, IF, ELSE = "WHILE", "IF", "ELSE"
PRINT = "PRINT"
PLUS, MINUS, DIVIDE, MULTIPLY, MOD, INCREMENT, DECREMENT = "PLUS", "MINUS", "DIVIDE", "MULTIPLY", "MOD", "INCREMENT", "DECREMENT"
SPLUS, SMINUS, SDIVIDE, SMULTIPLY, SMOD, SINCREMENT, SDECREMENT, ASSIGN = ":PLUS", ":MINUS", ":DIVIDE", ":MULTIPLY", ":MOD", ":INCREMENT", ":DECREMENT", "ASSIGN"

e_ops = [PLUS, MINUS, DIVIDE, MULTIPLY, MOD, INCREMENT, DECREMENT]
s_ops = [SPLUS, SMINUS, SDIVIDE, SMULTIPLY, SMOD, SINCREMENT, SDECREMENT, ASSIGN]
comps = [EQUAL,GREATER,LESSER,INEQUAL]
digits = range(0,11)
v_identifiers = range(100,200)
f_identifiers = list(range(-199,-99)) + [MAIN]
syscalls = [PRINT]
controls = [WHILE, IF, ELSE]

COMMENT = "`"
emoji_map = {"{":ANON,"}":END, "while":WHILE,"if":IF, "else":ELSE,
"+":PLUS,"-":MINUS,"/":DIVIDE,"*":MULTIPLY,"%":MOD,"^":INCREMENT,"_":DECREMENT,
":+":SPLUS,":-":SMINUS,":/":SDIVIDE,":*":SMULTIPLY,":%":SMOD,":^":SINCREMENT,":_":SDECREMENT,"assign":ASSIGN,
"=":EQUAL,">":GREATER,"<":LESSER,".":INEQUAL,
"0":0,"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"ten":10,
"v1":100,"v2":101,"v3":102,"v4":103,"v5":104,"v6":105,"v7":106,"v8":107,"v9":108,
"$":MAIN,"f1":-101,"f2":-102,"f3":-103,"f4":-104,"f5":-105,"f6":-106,"f7":-107,"f8":-108,"f9":-109,"f0":-100,
"print":PRINT
}



class Int(object):
    def __init__(self):
        self.value = 0
    def getVal(self):
        return self.value
    def setVal(self, value):
        self.value=value

class Token(object):
    def __init__(self, type, pos, value):
        self.type = type
        self.value = value
        self.pos = pos

    def __str__(self):
        return 'Token({type}, {value}, {pos})'.format(
            type=self.type,
            value=repr(self.value),
            pos=repr(self.pos)
        )

    def __repr__(self):
        return self.__str__()

class Interpreter(object):
    def __init__(self):
        self.text = []
        self.pos = 0
        self.functions = {}
        self.contexts = []
        self.args = []
        self.current_char = None
        self.current_token = None
        self.anons = 0

    def arg(self, argv):
        self.args.append(argv)

    def symbolize(self, char):
        return list(emoji_map.keys())[list(emoji_map.values()).index(char)]

    def scan(self, raw):
        i = -1
        val = ""
        text = []
        while i < len(raw)-1:
            i+=1
            if raw[i] is COMMENT:
                i += 1
                while raw[i] is not COMMENT:
                    i += 1
                    if i >= len(raw):
                        self.error("Error Parsing")
                i += 1
            if raw[i].isspace():
                continue
            val = raw[i]
            if val in emoji_map:
                text.append(emoji_map[val])
                continue
            while True:
                i+=1
                if i >= len(raw) or raw[i].isspace():
                    raise Exception("Error Parsing")
                val+=raw[i]
                if val in emoji_map:
                    text.append(emoji_map[val])
                    break
        return text

    def load(self, raw_text):
        text = self.scan(raw_text)
        i = 0
        offset = len(self.text)
        while i < len(text):
            if text[i] not in f_identifiers:
                self.error("Expected function declaration but found - " + self.symbolize(text[i]))
            j=i+1
            while text[j] is not END:
                if text[j] is ANON:
                    self.sliceAnon(j, text)
                j += 1
                if j >= len(text):
                    self.error("Expected function end " + END)
            if text[i] == MAIN:
                if MAIN in self.functions:
                    self.error("Second main function declaration")
                self.main = offset + i
            self.functions[text[i]] = offset + i
            i = j+1
        self.text += text


    def sliceAnon(self, i, text):
        identifier = "a" + str(self.anons)
        text[i] = identifier
        self.anons += 1
        j=i+1
        while text[j] is not END:
            if text[j] is ANON:
                self.sliceAnon(j, text)
            j+=1
            if j >= len(text):
                self.error("Expected function end " + END)
        text += text[i:j+1]
        del text[i+1:j+1]
        f_identifiers.append(identifier)


    def error(self, message):
        raise Exception("Error parsing input at pos " + str(self.pos) + " : " + message)

    def setPos(self, position):
        self.pos = position
        self.current_char = self.text[self.pos]
        self.current_token = self.get_next_token()

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def integer(self):
        result = ""
        while self.current_char is not None and self.current_char in digits:
            result += str(self.current_char)
            self.advance()
        return int(result)

    def variable(self):
        result = self.current_char
        self.advance()
        return result

    def function(self):
        result = self.current_char
        self.advance()
        return result

    def control(self):
        result = self.current_char
        self.advance()
        return result

    def comp(self):
        result = self.current_char
        self.advance()
        return result

    def syscall(self):
        result = self.current_char
        self.advance()
        return result

    def sop(self):
        result = self.current_char
        self.advance()
        return result

    def eop(self):
        result = self.current_char
        self.advance()
        return result

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char in digits:
                return Token(INTEGER, self.pos, self.integer())

            if self.current_char in  s_ops:
                return Token(SOP, self.pos, self.sop())

            if self.current_char in  e_ops:
                return Token(EOP, self.pos, self.eop())

            if self.current_char in v_identifiers:
                return Token(VARIABLE, self.pos, self.variable())

            if self.current_char in f_identifiers:
                return Token(FUNCTION, self.pos, self.function())

            if self.current_char in syscalls:
                return Token(SYSCALL, self.pos, self.syscall())

            if self.current_char in controls:
                return Token(CONTROL, self.pos, self.control())

            if self.current_char in comps:
                return Token(COMPARISON, self.pos, self.comp())

            if self.current_char == END:
                return Token(END, self.pos, None)

            self.error("Unexpected Symbol at - " + self.current_char)
        return Token(EOF, None)

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error("Expected " + token_type + " but found " + self.current_token.type)


    def scope(self):
        context = {}
        if len(self.contexts) > 0:
            for k, v in self.contexts[-1].items():
                val = Int()
                val.setVal(v.getVal())
                context[k] = val
            while True:
                tok = self.current_token
                if not tok.type == VARIABLE:
                    break
                self.eat(VARIABLE)
                if tok.value not in self.contexts[-1]:
                    self.error("Variable not in scope - " + self.symbolize(tok.value))
                context[tok.value] = self.contexts[-1][tok.value]
        else:
            i = 0
            while True:
                tok = self.current_token
                if not tok.type == VARIABLE:
                    break
                self.eat(VARIABLE)
                if i >= len(self.args):
                    self.error("Not enough args")
                val = Int()
                val.setVal(int(self.args[i]))
                context[tok.value] = val
                i += 1

        self.contexts.append(context)

    def execute(self, function):
        if function not in self.functions:
            error("Missing function declaration - " + self.symbolize(function))
        jr = self.pos
        self.setPos(self.functions[function])
        self.eat(FUNCTION)

        self.scope()

        while True:
            tok = self.current_token
            if tok.type == END:
                self.eat(END)
                self.contexts.pop()
                self.setPos(jr)
                return
            else:
                self.statement()


    def statement(self):
        tok = self.current_token
        if tok.type == SOP:
            return self.assign()
        if tok.type == SYSCALL:
            return self.call()
        if tok.type == FUNCTION:
                return self.execute(tok.value)
        if tok.type == CONTROL:
            return self.flow()
        else:
            self.error("Expected Statement but found " + tok.type)

    def flow(self):
        control = self.current_token
        jr = self.pos - 2
        self.eat(CONTROL)


        condition = self.bool_expr()
        func = self.current_token
        if condition:
            if control.value == WHILE:
                self.setPos(jr)
                self.execute(func.value)
            else:
                self.execute(func.value)
                if self.current_token.value is ELSE:
                    self.eat(CONTROL)
                    self.eat(FUNCTION)

        else:
            self.eat(FUNCTION)
            if self.current_token.value == ELSE:
                self.eat(CONTROL)
                self.execute(self.current_token.value)

    def bool_expr(self):
        comp = self.current_token
        self.eat(COMPARISON)
        val = self.expr()
        if val is None:
            self.error("expected expression but found - " + self.symbolize(self.current_token.type))
        result = True
        solo = True
        while self.current_token.type is not FUNCTION:
            solo = False
            expr = self.expr()
            if expr is None:
                self.error("expected function but found - " + self.symbolize(self.current_token.type))
            if comp.value == EQUAL:
                result = result and val == expr
            if comp.value == GREATER:
                result = result and val > expr
            if comp.value == LESSER:
                result = result and val < expr
            if comp.value == INEQUAL:
                result = result and val != expr
        if solo:
            return val>0
        return result

    def call(self):
        tok = self.current_token
        self.eat(SYSCALL)

        if tok.value == PRINT:
            value = self.expr()
            print(value)
            return value
        else:
            error("Unknown SYSCALL - " + self.symbolize(tok.value))

    def assign(self):
        op = self.current_token
        self.eat(SOP)

        variable = self.current_token
        if variable.type is not VARIABLE:
            error("Expected Vairable but found - " + self.symbolize(variable.value))
        if op.value == ASSIGN:
            self.eat(VARIABLE)
            value = self.expr()
            if variable.value not in self.contexts[-1]:
                self.contexts[-1][variable.value] = Int()
            self.contexts[-1][variable.value].setVal(value)
        elif op.value in s_ops:
            if op.value == SMULTIPLY:
                type = MULTIPLY
            elif op.value == SDIVIDE:
                type = DIVIDE
            elif op.value == SPLUS:
                type = PLUS
            elif op.value == SMINUS:
                type = MINUS
            elif op.value == SMOD:
                type = MOD
            elif op.value == SINCREMENT:
                self.eat(VARIABLE)
                if variable.value not in self.contexts[-1]:
                    self.error("Must assign value first - " + self.symbolize(variable.value))
                self.contexts[-1][variable.value].setVal(self.contexts[-1][variable.value].getVal()+1)
                return
            elif op.value == SDECREMENT:
                self.eat(VARIABLE)
                if variable.value not in self.contexts[-1]:
                    self.error("Must assign value first - " + self.symbolize(variable.value))
                self.contexts[-1][variable.value].setVal(self.contexts[-1][variable.value].getVal()-1)
                return
            else:
                self.error("Invalid statement - " + self.symbolize(op.value))

            if variable.value not in self.contexts[-1]:
                self.eat(VARIABLE)
                value = self.oper(type)
                self.contexts[-1][variable.value] = Int()
            else:
                value = self.oper(type)
            self.contexts[-1][variable.value].setVal(value)

        else:
            self.error("Invalid statement operator - " + self.symbolize(op.value))

    def expr(self):
        tok = self.current_token
        if tok.type == INTEGER:
            self.eat(INTEGER)
            return tok.value
        elif tok.type == EOP:
            self.eat(EOP)
            return self.oper(tok.value)
        elif tok.type == VARIABLE:
            self.eat(VARIABLE)
            if tok.value not in self.contexts[-1]:
                self.error("Must assign value first - " + self.symbolize(tok.value))
            var = self.contexts[-1][tok.value]
            return var.getVal()
        else:
            return None


    def oper(self, type):
        result = None
        while True:
            value = self.expr()
            if value is None:
                return result
            else:
                if type == MULTIPLY:
                    if result is None:
                        result = 1;
                    result = result * value
                elif type == DIVIDE:
                    if result is None:
                        result = 1;
                    result = result / value
                elif type == PLUS:
                    if result is None:
                        result = 0;
                    result = result + value
                elif type == MINUS:
                    if result is None:
                        result = 0;
                    result = result - value
                elif type == MOD:
                    if result is None:
                        result = 0;
                    result = result % value
                elif type == INCREMENT:
                    return value+1
                elif type == DECREMENT:
                    return value-1
                else:
                    self.error("Invalid operation in expression- " + self.symbolize(type))
    def run(self):
        if MAIN not in self.functions:
            self.error("No main found")
        self.execute(MAIN)

def main():
    if len(sys.argv) > 1:
        i = 1
        fn = re.compile(r'.*\.es$')
        interpreter = Interpreter()
        while i < len(sys.argv):
            text = ""
            if fn.match(sys.argv[i]):
                with open(sys.argv[i]) as f:
                    text += f.read()
                f.close()
                interpreter.load(text)
            else:
                interpreter.arg(sys.argv[i])
            i+=1
        interpreter.run()
    else:
        while True:
            try:
                text = input("☺>")
            except EOFError:
                break
            if not text:
                continue
            interpreter = Interpreter()
            interpreter.load(text)
            interpreter.run()

if __name__ == '__main__':
    main()
