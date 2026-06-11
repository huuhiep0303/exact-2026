"""
Fix dataset quality issues — V2 (comprehensive).

This script:
1. Detects reasoning ↔ answer contradictions in training data
2. Fixes contradictions using multi-pattern heuristic analysis
3. Handles BOTH YesNo and MCQ question types
4. Cleans up any legacy chat template tokens in input/output fields

Key patterns fixed:
- Reasoning says "thus, all X are/have Y" but answer is "No" → fix to "Yes"
- Reasoning says "making option A correct" but answer is "Unknown" → fix to "A"
- Reasoning says "the statement is true/false" but answer contradicts
- Reasoning says "derived through multiple steps" for MCQ but answer is "Unknown"
"""

import json
import re
import sys
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')


def analyze_reasoning_for_yesno(reasoning: str) -> str | None:
    """
    Analyze reasoning text to detect what answer it supports for YesNo questions.
    Returns 'Yes', 'No', 'Unknown' if confident, or None if ambiguous.
    
    Uses a scoring system with strong/medium/weak signals to avoid false positives.
    """
    r = reasoning.lower().strip()
    
    affirm_score = 0  # Evidence reasoning supports "Yes"
    negate_score = 0  # Evidence reasoning supports "No"
    uncertain_score = 0  # Evidence reasoning supports "Unknown"
    
    # ============================================================
    # STRONG AFFIRMATIVE patterns (weight=3)
    # ============================================================
    strong_affirm = [
        r'(?:therefore|thus|hence|so),?\s+the\s+statement\s+is\s+true',
        r'making\s+the\s+statement\s+true',
        r'making\s+it\s+true',
        r'the\s+statement\s+holds',
        r'the\s+statement\s+is\s+true\s+because',
        r'the\s+statement\s+is\s+true\.$',
    ]
    for p in strong_affirm:
        if re.search(p, r):
            affirm_score += 3
    
    # ============================================================
    # MEDIUM AFFIRMATIVE patterns (weight=2)
    # ============================================================
    medium_affirm = [
        # "Thus, all X are/have/qualify..."
        r'(?:thus|therefore|so|hence),?\s+all\s+\w+\s+(?:are|have|qualify|can|will|meet|pass|receive|possess|get)\b',
        # "...so all VR games are thoroughly tested"
        r'so\s+all\s+\w+\s+\w+\s+(?:are|have|qualify|can|will|meet|pass|receive|possess|get)\b',
        # "supporting the statement"
        r'supporting\s+the\s+statement',
        # "the consequent must be true"
        r'the\s+consequent\s+must\s+be\s+true',
        # "complete pathway" / "complete chain"
        r'(?:a\s+)?complete\s+(?:pathway|chain)',
        # "so Ponko/Phong/X will fail/pass/qualify"
        r'so\s+\w+(?:\'s)?\s+(?:ranking|result|score|status)\s+is',
        r'so\s+\w+\s+will\s+(?:fail|pass|qualify|succeed|receive|get)',
        # "the implication holds"
        r'the\s+implication\s+holds',
        # "is true, requiring steps to confirm"
        r'is\s+true,?\s+requiring\s+steps\s+to\s+confirm',
    ]
    for p in medium_affirm:
        if re.search(p, r):
            affirm_score += 2
    
    # ============================================================
    # WEAK AFFIRMATIVE patterns (weight=1)
    # ============================================================
    weak_affirm = [
        r'follows\s+because',
        r'it\s+follows\s+that',
        r'derived\s+through\s+multiple\s+steps',
        # "Thus, if all students complete X, students with Y..."
        r'(?:thus|therefore|so),?\s+if\s+all\s+',
    ]
    for p in weak_affirm:
        if re.search(p, r):
            affirm_score += 1
    
    # ============================================================
    # STRONG NEGATIVE patterns (weight=3)
    # ============================================================
    strong_negate = [
        r'the\s+statement\s+is\s+false',
        r'making\s+the\s+statement\s+false',
        r'the\s+answer\s+is\s+no',
        r'so\s+the\s+statement\s+is\s+false',
    ]
    for p in strong_negate:
        if re.search(p, r):
            negate_score += 3
    
    # ============================================================
    # MEDIUM NEGATIVE patterns (weight=2)
    # ============================================================
    medium_negate = [
        r'does\s+not\s+follow',
        r'doesn\'t\s+meet\s+all\s+requirements',
        r'falls?\s+short',
        r'cannot\s+(?:qualify|register|proceed|enroll|complete)',
        r'prevents?\s+(?:registration|enrollment|project\s+eligibility)',
        r'(?:is\s+not|are\s+not)\s+allowed',
        r'so\s+\w+\s+cannot\s+(?:register|qualify|proceed|enroll)',
    ]
    for p in medium_negate:
        if re.search(p, r):
            negate_score += 2
    
    # ============================================================
    # UNCERTAIN patterns (weight=3)
    # ============================================================
    uncertain_patterns = [
        r'no\s+premise\s+guarantees',
        r'it\'?s\s+uncertain',
        r'cannot\s+be\s+(?:inferred|determined)',
        r'insufficient\s+information',
        r'so\s+it\'?s\s+uncertain',
        r'uncertain\s+(?:whether|if)',
    ]
    for p in uncertain_patterns:
        if re.search(p, r):
            uncertain_score += 3
    
    # ============================================================
    # DECISION LOGIC
    # ============================================================
    # Only fix when there's a clear winner with sufficient confidence
    
    # Require minimum threshold and clear lead
    if affirm_score >= 3 and affirm_score > negate_score * 2 and affirm_score > uncertain_score * 2:
        return "Yes"
    
    if negate_score >= 3 and negate_score > affirm_score * 2 and negate_score > uncertain_score * 2:
        return "No"
    
    if uncertain_score >= 3 and uncertain_score > affirm_score * 2 and uncertain_score > negate_score * 2:
        return "Unknown"
    
    return None  # Ambiguous - don't change


def analyze_reasoning_for_mcq(reasoning: str) -> str | None:
    """
    Analyze reasoning text to detect what MCQ option it supports.
    Returns 'A', 'B', 'C', 'D' if confident, or None if ambiguous.
    """
    r = reasoning.lower().strip()
    
    scores = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    
    for opt_lower, opt_upper in [('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]:
        # Strong patterns (weight=3)
        if re.search(rf'making\s+option\s+{opt_lower}\s+correct', r):
            scores[opt_upper] += 3
        if re.search(rf'option\s+{opt_lower}\s+is\s+correct', r):
            scores[opt_upper] += 3
        if re.search(rf'supporting\s+option\s+{opt_lower}', r):
            scores[opt_upper] += 3
        
        # Medium patterns (weight=2)
        if re.search(rf'\boption\s+{opt_lower}\b', r) and re.search(r'correct|true|right|valid', r):
            scores[opt_upper] += 2
        # Pattern: "making C correct"
        if re.search(rf'making\s+{opt_lower}\s+correct', r):
            scores[opt_upper] += 2
    
    # Find the best option
    best_opt = max(scores, key=scores.get)
    best_score = scores[best_opt]
    
    # Only return if there's a clear winner with sufficient confidence
    second_best = sorted(scores.values(), reverse=True)[1]
    
    if best_score >= 3 and best_score > second_best:
        return best_opt
    
    return None


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
        
    fixed_yesno_count = 0
    fixed_mcq_count = 0
    cleaned_token_count = 0
    fix_details = []  # Track what we fixed
    
    for idx, sample in enumerate(data):
        output_text = sample.get("output", "")
        input_text = sample.get("input", "")
        metadata = sample.get("metadata", {})
        labeled_answer = metadata.get("answer", "")
        question_type = metadata.get("question_type", "")
        
        # Step 1: Clean legacy chat template tokens from input and output
        cleaned_input = clean_legacy_tokens(input_text)
        cleaned_output = clean_legacy_tokens(output_text)
        
        if cleaned_input != input_text or cleaned_output != output_text:
            sample["input"] = cleaned_input
            sample["output"] = cleaned_output
            cleaned_token_count += 1
            output_text = cleaned_output  # use cleaned version for analysis
        
        # Step 2: Extract reasoning text
        reasoning_match = re.search(
            r'\*\*Reasoning:\*\*(.*?)(?:</think>|\*\*Answer:\*\*)', 
            output_text, re.DOTALL
        )
        if not reasoning_match:
            continue
            
        reasoning_text = reasoning_match.group(1).strip()
        
        # Step 3: Fix YesNo contradictions
        if question_type == "YesNo":
            detected_answer = analyze_reasoning_for_yesno(reasoning_text)
            
            if detected_answer and detected_answer != labeled_answer:
                # Fix output text
                new_output_text = re.sub(
                    r'\*\*Answer:\*\*.*', 
                    f'**Answer:** {detected_answer}', 
                    output_text, flags=re.IGNORECASE
                )
                sample["output"] = new_output_text
                sample["metadata"]["answer"] = detected_answer
                fixed_yesno_count += 1
                fix_details.append(f"  [{idx}] YesNo: {labeled_answer} → {detected_answer}")
        
        # Step 4: Fix MCQ contradictions (especially Unknown → correct option)
        elif question_type == "MCQ" or labeled_answer in ['A', 'B', 'C', 'D'] or \
             labeled_answer == 'Unknown':
            detected_answer = analyze_reasoning_for_mcq(reasoning_text)
            
            if detected_answer and detected_answer != labeled_answer:
                # For MCQ, only fix Unknown→Option or when reasoning is very clear
                if labeled_answer == 'Unknown' or \
                   (labeled_answer in ['A', 'B', 'C', 'D'] and detected_answer):
                    new_output_text = re.sub(
                        r'\*\*Answer:\*\*.*', 
                        f'**Answer:** {detected_answer}', 
                        output_text, flags=re.IGNORECASE
                    )
                    sample["output"] = new_output_text
                    sample["metadata"]["answer"] = detected_answer
                    fixed_mcq_count += 1
                    fix_details.append(f"  [{idx}] MCQ: {labeled_answer} → {detected_answer}")
                    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    total_fixed = fixed_yesno_count + fixed_mcq_count
    print(f"  Fixed {total_fixed} / {len(data)} contradictions ({(total_fixed/len(data))*100:.1f}%)")
    print(f"    YesNo fixes: {fixed_yesno_count}")
    print(f"    MCQ fixes:   {fixed_mcq_count}")
    print(f"  Cleaned {cleaned_token_count} / {len(data)} legacy tokens ({(cleaned_token_count/len(data))*100:.1f}%)")
    
    if fix_details:
        print(f"  Fix details:")
        for d in fix_details[:30]:  # Show first 30
            print(d)
        if len(fix_details) > 30:
            print(f"  ... and {len(fix_details) - 30} more")


if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent / "outputs" / "processed_data"
    for split in ["train", "val", "test"]:
        in_file = base_dir / f"{split}.json"
        out_file = base_dir / f"{split}_fixed.json"
        if in_file.exists():
            fix_dataset(in_file, out_file)
    print("\nDone fixing datasets.")
