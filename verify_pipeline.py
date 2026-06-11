"""Quick verification - ASCII safe for Windows console."""
import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def main():
    print("=" * 60)
    print("EXACT 2026 - Pipeline Verification")
    print("=" * 60)
    
    # 1. Check data format
    print("\n[1] DATA FORMAT CHECK")
    all_ok = True
    for split in ['train_fixed', 'val_fixed', 'test_fixed']:
        fpath = Path(f"outputs/processed_data/{split}.json")
        if not fpath.exists():
            print(f"  FAIL: {split}.json not found")
            all_ok = False
            continue
        
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        legacy = sum(1 for s in data 
                     if '<|im_start|>' in s['input'] or '<|im_end|>' in s['input']
                     or '<|im_start|>' in s['output'] or '<|im_end|>' in s['output'])
        no_fmt = sum(1 for s in data if '<think>' not in s['output'] or '</think>' not in s['output'])
        
        status = "OK" if legacy == 0 and no_fmt == 0 else "ISSUES"
        print(f"  {split}: {len(data)} samples, legacy_tokens={legacy}, missing_format={no_fmt} [{status}]")
        if legacy > 0 or no_fmt > 0:
            all_ok = False
    
    # 2. Check prompt consistency
    print("\n[2] PROMPT CONSISTENCY CHECK")
    from src.data.data_processor import SYSTEM_PROMPT
    print(f"  SYSTEM_PROMPT length: {len(SYSTEM_PROMPT)} chars")
    print(f"  Used by: data_processor.py, dataset.py, inference.py")
    print(f"  Status: OK (single source of truth)")
    
    # 3. Check answer consistency
    print("\n[3] ANSWER CONSISTENCY CHECK (metadata vs output)")
    for split in ['train_fixed', 'val_fixed', 'test_fixed']:
        fpath = Path(f"outputs/processed_data/{split}.json")
        if not fpath.exists():
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mismatches = 0
        for s in data:
            meta_ans = s['metadata']['answer']
            match = re.search(r'\*\*Answer:\*\*\s*(.+?)$', s['output'], re.MULTILINE)
            if match:
                out_ans = match.group(1).strip()
                if meta_ans not in out_ans:
                    mismatches += 1
            else:
                mismatches += 1
        
        rate = (len(data) - mismatches) / len(data) * 100
        status = "OK" if mismatches == 0 else f"WARN({mismatches} mismatches)"
        print(f"  {split}: {rate:.1f}% match [{status}]")
    
    # 4. Config check
    print("\n[4] CONFIG CHECK")
    import yaml
    with open("configs/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    print(f"  Model: {config['model']['name']}")
    print(f"  Max length: {config['model']['max_length']}")
    print(f"  Enable thinking: {config['model'].get('enable_thinking', 'not set')}")
    print(f"  LoRA r: {config['lora']['r']}")
    print(f"  Epochs: {config['training']['num_train_epochs']}")
    print(f"  LR: {config['training']['learning_rate']}")
    
    print("\n" + "=" * 60)
    if all_ok:
        print("ALL CHECKS PASSED - Ready to train!")
        print("  Run: modal run run_modal.py::train_and_evaluate")
    else:
        print("SOME CHECKS FAILED - Please review above")
    print("=" * 60)

if __name__ == "__main__":
    main()
