INTEGER, OP, VARIABLE, FUNCTION, SYSCALL, CONTROL, COMPARISON, EOF = "INTEGER", "OP", "VARIABLE", "FUNCTION", "SYSCALL", "CONTROL", "COMPARISON", "EOF"
MAIN = "$"
ANON = "@"
END = "!"
ops = ["+", "-", "/", "*", "%", "^", "_", "~"]
comps = ["=",">","<","."]
digits = ["q","w","e","r","t","y","u","i","o","p","["]
v_identifiers = ["a", "s", "d", "f", "g", "h", "j", "k", "l"]
f_identifiers = ["1","2","3","4","5","6","7","8","9","0", "$"]
syscalls = ["#"]
controls = [":", "?"]


class Int(object):
    def __init__(self):
        self.value = 0
    def getVal(self):
        return self.value
    def setVal(self, value):
        self.value=value

class Token(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()

class Interpreter(object):
    def __init__(self, text):
        self.text = ""
        self.pos = 0
        self.functions = {}
        self.contexts = []
        self.loadText(text)
        self.current_char = self.text[self.pos]
        self.current_token = None

    def loadText(self, text):
        i = 0
        offset = len(self.text)
        while i < len(text):
            if text[i] not in f_identifiers:
                self.error("Expected function declaration but found - " + text[i])
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

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        result = ""
        while self.current_char is not None and self.current_char in digits:
            result += str(digits.index(self.current_char))
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
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char in digits:
                return Token(INTEGER, self.integer())

            if self.current_char in  ops:
                return Token(OP, self.op())

            if self.current_char in v_identifiers:
                return Token(VARIABLE, self.variable())

            if self.current_char in f_identifiers:
                return Token(FUNCTION, self.function())

            if self.current_char in syscalls:
                return Token(SYSCALL, self.syscall())

            if self.current_char in controls:
                return Token(CONTROL, self.control())

            if self.current_char in comps:
                return Token(COMPARISON, self.comp())

            if self.current_char == END:
                return Token(END, None)

            self.error("Unexpected Symbol at - " + self.current_char)
        return Token(EOF, None)

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error("Expected " + token_type + " but found " + self.current_token.type)


    def execute(self, function):
        if function not in self.functions:
            self.error("Function not found - " + function)

        jr = self.pos
        self.setPos(self.functions[function])

        self.eat(FUNCTION)

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
                self.error("Variable not in scope - " + tok.value)
            context[tok.value] = self.contexts[-1][tok.value]

        self.contexts.append(context)
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
        jr = self.pos-2
        self.eat(CONTROL)

        condition = self.bool_expr()

        if not condition:
            self.eat(FUNCTION)
        if condition:
            func = self.current_token
            if control.value == ":":
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
            if comp.value == "=":
                result = result and val == expr
            if comp.value == ">":
                result = result and val > expr
            if comp.value == "<":
                result = result and val < expr
            if comp.value == ".":
                result = result and val != expr
        if solo:
            return val>0
        return result

    def call(self):
        tok = self.current_token
        self.eat(SYSCALL)

        if tok.value == "#":
            value = self.expr()
            print(value)

    def assign(self):
        op = self.current_token
        self.eat(OP)

        variable = self.current_token
        if op.value == "~":
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
            self.error("Invalid statement operator - " + op.value)

    def expr(self):
        tok = self.current_token
        if tok.type == INTEGER:
            self.eat(INTEGER)
            return tok.value
        elif tok.type == OP and tok.value is not "~":
            self.eat(OP)
            return self.oper(tok.value)
        elif tok.type == VARIABLE:
            self.eat(VARIABLE)
            if tok.value not in self.contexts[-1]:
                self.error("Must assign value first - " + tok.value)
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
                if type == "*":
                    if result is None:
                        result = 1;
                    result = result * value
                elif type == "/":
                    if result is None:
                        result = 1;
                    result = result / value
                elif type == "+":
                    if result is None:
                        result = 0;
                    result = result + value
                elif type == "-":
                    if result is None:
                        result = 0;
                    result = result - value
                elif type == "%":
                    if result is None:
                        result = 0;
                    result = result % value
                elif type == "^":
                    return value+1
                elif type == "_":
                    return value-1
                else:
                    self.error("Invalid operation in expression- " + type)
    def run(self):
        if MAIN not in self.functions:
            self.error("No main found")
        self.execute(MAIN)

def main():
    while True:
        try:
            text = input("☺>")
        except EOFError:
            break
        if not text:
            continue
        interpreter = Interpreter(text)
        interpreter.run()

if __name__ == '__main__':
    main()
