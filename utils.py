import string
import random
import json

char_set_list = list(string.ascii_letters + string.digits)
custom_encoding = {}
for i in range(62):
    idx = random.randint(0,len(char_set_list) - 1)
    custom_encoding[bin(i)[2:].zfill(6)] = char_set_list[idx]
    char_set_list.pop(idx)


if __name__ == "__main__":
    with open("encoding.json","w") as f:
        json.dump(custom_encoding,f)

