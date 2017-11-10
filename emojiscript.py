import sys
import parser
import re

PRINT, EQUAL, GREATER, LESSER, INEQUAL, PLUS, MINUS, DIVIDE, MULTIPLY, MOD, INCREMENT, DECREMENT, ASSIGN, INTEGER, OP, VARIABLE, FUNCTION, SYSCALL, CONTROL, COMPARISON, MAIN, ANON, END, WHILE, IF, EOF = "PRINT", "EQUAL","GREATER","LESSER","INEQUAL", "PLUS", "MINUS", "DIVIDE", "MULTIPLY", "MOD", "INCREMENT", "DECREMENT", "ASSIGN", "INTEGER", "OP", "VARIABLE", "FUNCTION", "SYSCALL", "CONTROL", "COMPARISON", -100, "ANON", "END", "WHILE", "IF", "EOF"

ops = [PLUS, MINUS, DIVIDE, MULTIPLY, MOD, INCREMENT, DECREMENT, ASSIGN]
comps = [EQUAL,GREATER,LESSER,INEQUAL]
digits = range(0,11)
v_identifiers = range(100,200)
f_identifiers = range(-200,-99)
syscalls = [PRINT]
controls = [WHILE, IF]

emoji_map = {"@":ANON,"!":END, ":":WHILE,"?":IF,
"+":PLUS,"-":MINUS,"/":DIVIDE,"*":MULTIPLY,"%":MOD,"^":INCREMENT,"_":DECREMENT,"~":ASSIGN,"=":EQUAL,">":GREATER,"<":LESSER,".":INEQUAL,
"q":0,"w":1,"e":2,"r":3,"t":4,"y":5,"u":6,"i":7,"o":8,"p":9,"[":10,
"a":100,"s":101,"d":102,"f":103,"g":104,"h":105,"j":106,"k":107,"l":108,
"$":-100,"1":-101,"2":-102,"3":-103,"4":-104,"5":-105,"6":-106,"7":-107,"8":-108,"9":-109,"0":-110,
"#":PRINT
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

    def arg(self, argv):
        self.args.append(argv)

    def symbolize(self, char):
        return list(emoji_map.keys())[list(emoji_map.values()).index(char)]

    def scan(self, raw):
        i = 0
        j = 0
        val = ""
        text = []
        while i < len(raw):
            if raw[i].isspace():
                i+=1
                continue
            val = raw[i]
            if val in emoji_map:
                text.append(emoji_map[val])
                j+=1
                i+=1
                continue
            while True:
                i+=1
                if i >= len(raw) or raw[i].isspace():
                    raise Exception("Error Parsing")
                val+=raw[i]
                if val in emoji_map:
                    text.append(emoji_map[val])
                    j+=1
                    i+=1
                    break
        return text

    def load(self, raw_text):
        text = self.scan(raw_text)
        i = 0
        offset = len(self.text)
        while i < len(text):
            if text[i] not in f_identifiers:
                self.error("Expected function declaration but found - " + self.symbolize(text[i]))
            bal = 1
            j=i+1
            while bal > 0:
                if text[j] == ANON:
                    bal += 1
                if text[j] == END:
                    bal -= 1
                j += 1
                if i >= len(text):
                    self.error("Expected function end " + END)
            if text[i] == MAIN:
                if MAIN in self.functions:
                    self.error("Second main function declaration")
                self.main = offset + i
            self.functions[text[i]] = offset + i
            i = j
        self.text += text


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
        if self.current_char not in v_identifiers:
            self.error("Invalid symbol in identifier - " + self.current_char)
        result = self.current_char
        self.advance()
        return result

    def function(self):
        if self.current_char not in f_identifiers:
            self.error("Invalid symbol in identifier - " + self.current_char)
        result = self.current_char
        self.advance()
        return result

    def control(self):
        if self.current_char not in controls:
            self.error("Invalid symbol in identifier - " + self.current_char)
        result = self.current_char
        self.advance()
        return result

    def comp(self):
        if self.current_char not in comps:
            self.error("Invalid symbol in identifier - " + self.current_char)
        result = self.current_char
        self.advance()
        return result

    def syscall(self):
        if self.current_char not in syscalls:
            self.error("Invalid syscall - " + self.current_char)
        result = self.current_char
        self.advance()
        return result

    def op(self):
        result = self.current_char
        self.advance()
        return result

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char in digits:
                return Token(INTEGER, self.pos, self.integer())

            if self.current_char in  ops:
                return Token(OP, self.pos, self.op())

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
        self.prev = self.current_token.pos
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
            self.error("Function not found - " + self.symbolize(function))

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
        if tok.type == OP:
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

        if not condition:
            self.eat(FUNCTION)
        if condition:
            func = self.current_token
            if control.value == WHILE:
                self.setPos(jr)
                self.execute(func.value)
            else:
                self.execute(func.value)

    def bool_expr(self):
        comp = self.current_token
        self.eat(COMPARISON)
        val = self.expr()
        result = True
        solo = True
        while self.current_token.type is not FUNCTION:
            solo = False
            expr = self.expr()
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
        self.eat(OP)

        variable = self.current_token
        if op.value == ASSIGN:
            if variable.value not in self.contexts[-1]:
                self.contexts[-1][variable.value] = Int()
            self.eat(VARIABLE)
            value = self.expr()
            self.contexts[-1][variable.value].setVal(value)
        elif op.value in ops:
            if variable.value not in self.contexts[-1]:
                self.eat(VARIABLE)
                self.contexts[-1][variable.value] = Int()
            value = self.oper(op.value)
            self.contexts[-1][variable.value].setVal(value)

        else:
            self.error("Invalid statement operator - " + self.symbolize(op.value))

    def expr(self):
        tok = self.current_token
        if tok.type == INTEGER:
            self.eat(INTEGER)
            return tok.value
        elif tok.type == OP:# and tok.value is not ASSIGN:
            self.eat(OP)
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
