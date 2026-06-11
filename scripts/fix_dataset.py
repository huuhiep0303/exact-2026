"""
Fix dataset quality issues.

This script:
1. Detects reasoning ↔ answer contradictions in training data
2. Fixes contradictions based on heuristic analysis of reasoning text  
3. Cleans up any legacy chat template tokens in input/output fields
"""

import json
import re
from pathlib import Path


def get_correct_answer_from_reasoning(reasoning: str, current_answer: str) -> str:
    """Uses STRICT heuristics to detect if reasoning explicitly contradicts the answer."""
    reasoning_lower = reasoning.lower()
    
    # Very strong affirmative phrases usually at the end of reasoning
    if re.search(r'(therefore|thus|hence|so|making) the statement (is )?true', reasoning_lower) or \
       re.search(r'the statement.*is true because it is explicitly', reasoning_lower) or \
       re.search(r'the implication holds.*requiring steps to confirm', reasoning_lower) or \
       re.search(r'statement is explicitly given.*making it true', reasoning_lower) or \
       re.search(r'the statement is true\.$', reasoning_lower.strip()):
        return "Yes"
        
    # Strong negative/unknown phrases
    if re.search(r'(therefore|thus|hence|so|making) the statement (is )?false', reasoning_lower) or \
       re.search(r'the statement is false', reasoning_lower):
        return "No"
        
    if re.search(r'cannot be inferred', reasoning_lower) or \
       re.search(r'is uncertain', reasoning_lower) or \
       re.search(r'insufficient information', reasoning_lower):
        return "Unknown"
        
    return current_answer


def clean_legacy_tokens(text: str) -> str:
    """
    Remove legacy hardcoded chat template tokens from text.
    
    The old data_processor.py was injecting <|im_start|>/<|im_end|> tokens
    directly into input/output strings. These need to be stripped so that
    the tokenizer's apply_chat_template can handle formatting properly.
    """
    # Remove chat template role markers
    text = re.sub(r'<\|im_start\|>(system|user|assistant)\n?', '', text)
    text = re.sub(r'<\|im_end\|>', '', text)
    return text.strip()


def fix_dataset(input_file: Path, output_file: Path):
    if not input_file.exists():
        print(f"File not found: {input_file}")
        return
        
    print(f"Processing {input_file.name}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    fixed_answer_count = 0
    cleaned_token_count = 0
    
    for sample in data:
        output_text = sample.get("output", "")
        input_text = sample.get("input", "")
        metadata = sample.get("metadata", {})
        labeled_answer = metadata.get("answer", "")
        
        # Step 1: Clean legacy chat template tokens from input and output
        cleaned_input = clean_legacy_tokens(input_text)
        cleaned_output = clean_legacy_tokens(output_text)
        
        if cleaned_input != input_text or cleaned_output != output_text:
            sample["input"] = cleaned_input
            sample["output"] = cleaned_output
            cleaned_token_count += 1
            output_text = cleaned_output  # use cleaned version for analysis
        
        # Step 2: Fix reasoning ↔ answer contradictions (only for YesNo questions)
        if metadata.get("question_type") == "YesNo":
            reasoning_match = re.search(r'\*\*Reasoning:\*\*(.*?)(?:</think>|\*\*Answer:\*\*)', output_text, re.DOTALL)
            if reasoning_match:
                reasoning_text = reasoning_match.group(1).strip()
                
                # Determine correct answer
                correct_answer = get_correct_answer_from_reasoning(reasoning_text, labeled_answer)
                
                if correct_answer != labeled_answer:
                    # Fix output text
                    new_output_text = re.sub(r'\*\*Answer:\*\*.*', f'**Answer:** {correct_answer}', output_text, flags=re.IGNORECASE)
                    sample["output"] = new_output_text
                    
                    # Fix metadata
                    sample["metadata"]["answer"] = correct_answer
                    fixed_answer_count += 1
                    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"  Fixed {fixed_answer_count} / {len(data)} answer contradictions ({(fixed_answer_count/len(data))*100:.1f}%)")
    print(f"  Cleaned {cleaned_token_count} / {len(data)} samples with legacy tokens ({(cleaned_token_count/len(data))*100:.1f}%)")


if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent / "outputs" / "processed_data"
    for split in ["train", "val", "test"]:
        in_file = base_dir / f"{split}.json"
        out_file = base_dir / f"{split}_fixed.json"
        if in_file.exists():
            fix_dataset(in_file, out_file)
    print("Done fixing datasets.")
