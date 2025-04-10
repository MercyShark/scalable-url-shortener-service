import json

with open('encoding.json', 'r') as f:
    encoding = json.load(f)


def get_binary(number: int) -> str:
    binary = (bin(number)[2:])
    print(binary)
    actual_length = ((6 - (len(binary) % 6)) % 6) + len(binary)
    return binary.zfill(actual_length)

def get_url_code(binary_string: str) -> str:
    url_code = ""
    binary_groups = [binary_string[i:i+6] for i in range(0,len(binary_string),6)]
    for group in binary_groups:
        url_code += encoding[group] 
    return url_code


print(get_url_code(get_binary(3274598283892)))
