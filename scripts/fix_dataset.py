import json
import re
from pathlib import Path

def get_correct_answer_from_reasoning(reasoning_text: str, current_answer: str) -> str:
    """Heuristic to determine the correct answer based on the reasoning text."""
    reasoning_lower = reasoning_text.lower()
    
    # Strong signals that the statement is true
    affirmative_signals = [
        "is true", "is correct", "it follows", "confirms", "can be inferred",
        "so it's true", "making the statement true", "thus,", "therefore,",
        "it is explicitly stated", "directly states", "applies modus ponens",
        "is satisfied", "are satisfied", "must be true", "holds true",
        "making the implication true", "making the consequent true",
        "statement is true", "the entire implication holds"
    ]
    
    # Strong signals that the statement is false
    negative_signals = [
        "is false", "is not supported", "cannot be inferred", "does not follow",
        "no premise guarantees", "uncertain", "cannot determine", "insufficient",
        "statement is false", "is not true"
    ]
    
    aff_count = sum(1 for s in affirmative_signals if s.lower() in reasoning_lower)
    neg_count = sum(1 for s in negative_signals if s.lower() in reasoning_lower)
    
    # Explicit override checks based on common contradiction patterns seen
    if re.search(r'statement is true|making the statement true|implication holds|it follows that.*is true', reasoning_lower):
        return "Yes"
    if re.search(r'statement is false|is not true|cannot be inferred', reasoning_lower):
        if "unknown" in reasoning_lower or "cannot determine" in reasoning_lower or "insufficient" in reasoning_lower:
            return "Unknown"
        return "No"
    
    # If the reasoning heavily leans towards affirmative
    if aff_count > neg_count and aff_count >= 1:
        return "Yes"
    elif neg_count > aff_count and neg_count >= 1:
        # Need to differentiate between No and Unknown based on keywords
        if "unknown" in reasoning_lower or "cannot determine" in reasoning_lower or "insufficient" in reasoning_lower:
            return "Unknown"
        return "No"
    
    # If we can't definitively tell, assume the reasoning might be complicated and return the original label
    # or just return what it was. We only flip if we are highly confident.
    return current_answer

def fix_dataset(input_file: Path, output_file: Path):
    if not input_file.exists():
        print(f"File not found: {input_file}")
        return
        
    print(f"Processing {input_file.name}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    fixed_count = 0
    for sample in data:
        output_text = sample.get("output", "")
        metadata = sample.get("metadata", {})
        labeled_answer = metadata.get("answer", "")
        
        # Extract reasoning
        reasoning_match = re.search(r'\*\*Reasoning:\*\*(.*?)\*\*Answer:\*\*', output_text, re.DOTALL)
        if reasoning_match:
            reasoning_text = reasoning_match.group(1).strip()
            
            # Determine correct answer
            correct_answer = get_correct_answer_from_reasoning(reasoning_text, labeled_answer)
            
            if correct_answer != labeled_answer:
                # Fix output text
                # We need to replace the last part "**Answer:** <something>"
                new_output_text = re.sub(r'\*\*Answer:\*\*.*', f'**Answer:** {correct_answer}', output_text, flags=re.IGNORECASE)
                sample["output"] = new_output_text
                
                # Fix metadata
                sample["metadata"]["answer"] = correct_answer
                fixed_count += 1
                
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"Fixed {fixed_count} / {len(data)} samples ({(fixed_count/len(data))*100:.1f}%) in {output_file.name}")

if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent / "outputs" / "processed_data"
    for split in ["train", "val", "test"]:
        in_file = base_dir / f"{split}.json"
        out_file = base_dir / f"{split}_fixed.json"
        if in_file.exists():
            fix_dataset(in_file, out_file)
    print("Done fixing datasets.")
