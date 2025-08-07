import re

def extract_initial_win_prob(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Try to find win probability from "wnPrb"
    probs = re.findall(r'"wnPrb":\s*\{\s*"pts":\s*\{([^}]*)\}', content)
    if probs:
        match = re.search(r':\s*([\d.]+)', probs[0])
        if match:
            win_prob = float(match.group(1))
            print(f"Win Probability: {win_prob}")
            return win_prob
        
    # If not found, try to find from "mtchpPrdctr"
    mtch = re.search(r'"mtchpPrdctr":\s*\{\s*"teams":\s*\[\s*\{[^}]*"value":\s*([\d.]+)', content)
    if mtch:
        win_prob = float(mtch.group(1))
        print(f"Predicted Win Probability: {win_prob}")
        return win_prob
    print("Win Probability not found.")
    return None

if __name__ == "__main__":
    extract_initial_win_prob("espn/guardians-mets.html")