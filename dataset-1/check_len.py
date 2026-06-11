import json

def check_len():
    with open('outputs/processed_data/train_fixed.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    max_in = max(len(d['input']) for d in data)
    max_out = max(len(d['output']) for d in data)
    
    print(f"Max input chars: {max_in}")
    print(f"Max output chars: {max_out}")
    print(f"Max total chars: {max_in + max_out}")

check_len()
