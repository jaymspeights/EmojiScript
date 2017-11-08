def parse(text):
    emojis = {"➰":0,"🏁":2,"🔜":3,"🔚":4,"😂":5,"⬆️":6,"😀":7,"➡️":8,"➗":9,"➕":10,"📢":11,"😁":12,"🔟":13,"🐒":14,"❌":15,"👍":16}
    i = 0
    val = ""
    while i < len(text):
        val = text[i]
        if val in emojis:
            yield emojis[val]
            i+=1
            continue
        while True:
            i+=1
            if i >= len(text):
                raise Exception("Error Parsing")
            val+=text[i]
            if val in emojis:
                yield emojis[val]
                i+=1
                break


test = "👍⬆️🏁➡️➰😂"
parser = parse(test)
for tok in parser:
    print (tok)
