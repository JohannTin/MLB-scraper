#!/usr/bin/env python3
"""
Random Day Sample from MLB Schedule
Shows games for a random day from the MLB schedule
"""

import argparse
from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default settings
DEFAULT_HTML_FILE = 'html/MLB-schedule.shtml'
MAX_GAMES_PER_DAY = None  # Show all games per day (no limit)
SHOW_RAW_TEXT = True     # Whether to show raw text content for each game
SHOW_GAME_TYPE = True    # Whether to show game type (Spring, Regular, etc.)

# Date format examples for reference
# The script searches for dates in the HTML, so these are just examples
# of how dates might appear in the schedule:
DATE_EXAMPLES = [
    "March 15, 2025",
    "April 1, 2025", 
    "May 10, 2025",
    "June 20, 2025"
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def update_todays_games(html_file_path: str):
    """
    Replace 'Today's Games' section with current date format
    This updates the HTML file to use the current date instead of 'Today's Games'
    """
    import re
    from datetime import datetime
    
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Get current date
    now = datetime.now()
    current_date = now.strftime("%A, %B %-d, %Y")
    print(f"Current date: {current_date}")
    
    # Pattern to match Today's Games header
    pattern = r'<h3><span id=\'today\'>Today\'s Games</span></h3>'
    replacement = f'<h3>{current_date}</h3>'
    
    # Replace the header
    new_content = re.sub(pattern, replacement, content)
    
    # Pattern to match game entries with times (Preview links)
    game_pattern = r'<p class="game">\s*<span tz="E"><strong>([^<]+)</strong></span>\s*<a href="([^"]+)">([^<]+)</a>\s*@\s*<a href="([^"]+)">([^<]+)</a>\s*&nbsp;&nbsp;&nbsp;&nbsp;<em><a href="([^"]+)">Preview</a></em>\s*</p>'
    
    def replace_game_with_scores(match):
        time = match.group(1)
        team1_url = match.group(2)
        team1_name = match.group(3)
        team2_url = match.group(4)
        team2_name = match.group(5)
        preview_url = match.group(6)
        
        # Convert preview URL to boxscore URL format
        boxscore_url = preview_url.replace('/previews/', '/boxes/')
        boxscore_url = re.sub(r'/([A-Z]+)2025', r'/\1/\12025', boxscore_url)
        
        # Create new game format with scores (TBD for future games)
        return f'<p class="game">\n\n <a href="{team1_url}">{team1_name}</a>\n (TBD)\n @\n <strong> <a href="{team2_url}">{team2_name}</a>\n (TBD)</strong>\n &nbsp;&nbsp;&nbsp;&nbsp;<em><a href="{boxscore_url}">Boxscore</a></em>\n </p>'
    
    # Replace game entries
    new_content = re.sub(game_pattern, replace_game_with_scores, new_content)
    
    # Write the updated content back to the file
    with open(html_file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print(f"✅ Successfully replaced 'Today's Games' with '{current_date}'")
    print("✅ Updated game format to match other dates (with scores instead of times)")

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def get_games_for_date(html_file_path: str, target_date: str) -> List[Dict]:
    """
    Get games for a specific date from the MLB schedule
    Args:
        html_file_path: Path to the HTML file
        target_date: Specific date to search for (format: "Month Day, Year")
    Returns: List of dictionaries with date and games
    """
    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    # Find all sections with dates and games
    sections = soup.find_all('div')
    
    # Filter sections that have actual games (not just headers)
    game_sections = []
    for section in sections:
        game_paragraphs = section.find_all('p', class_='game')
        if game_paragraphs:
            date_header = section.find('h3')
            date = date_header.get_text(strip=True) if date_header else "Unknown Date"
            game_sections.append({
                'date': date,
                'section': section,
                'games': game_paragraphs
            })
    
    # Search for the specific date (more precise matching)
    target_date_lower = target_date.lower()
    matching_sections = []
    
    for section in game_sections:
        section_date_lower = section['date'].lower()
        
        # Extract month and day from target date
        target_parts = target_date_lower.split()
        if len(target_parts) >= 3:  # Should have "August", "04", "2025"
            target_month = target_parts[0]
            target_day = target_parts[1].replace(',', '')
            target_year = target_parts[2]
            
            # Remove leading zero from day if present
            if target_day.startswith('0'):
                target_day = target_day[1:]
            
            # Check if this section contains the exact month, day, and year
            # Use word boundaries to avoid partial matches
            import re
            pattern = rf'\b{target_month}\b.*\b{target_day}\b.*\b{target_year}\b'
            if re.search(pattern, section_date_lower):
                matching_sections.append(section)
        else:
            # Fallback to simple substring matching
            if target_date_lower in section_date_lower:
                matching_sections.append(section)
    
    if matching_sections:
        selected_days = matching_sections
    else:
        print(f"Date '{target_date}' not found in schedule.")
        print("Available dates include:")
        for section in game_sections[:5]:  # Show first 5 available dates
            print(f"  - {section['date']}")
        return []
    
    result = []
    for day_data in selected_days:
        day_games = []
        
        for game_p in day_data['games']:
            game_data = {
                'team1': None,
                'team2': None,
                'score1': None,
                'score2': None,
                'time': None,
                'game_type': None,
                'raw_html': str(game_p),
                'text_content': game_p.get_text(strip=True)
            }
            
            # Extract time if present
            time_span = game_p.find('span', attrs={'tz': 'E'})
            if time_span:
                game_data['time'] = time_span.get_text(strip=True)
            
            # Extract game type (Spring, Regular, etc.)
            game_type_span = game_p.find('span')
            if game_type_span and 'Spring' in game_type_span.get_text():
                game_data['game_type'] = 'Spring'
            
            # Find all team links
            team_links = game_p.find_all('a', href=re.compile(r'/teams/[A-Z]+/'))
            
            if len(team_links) >= 2:
                # Extract team names
                game_data['team1'] = team_links[0].get_text(strip=True)
                game_data['team2'] = team_links[1].get_text(strip=True)
                
                # Extract scores from the entire game paragraph text
                game_text = game_p.get_text()
                scores = re.findall(r'\((\d+)\)', game_text)
                if len(scores) >= 2:
                    game_data['score1'] = int(scores[0])
                    game_data['score2'] = int(scores[1])
                elif len(scores) == 1:
                    game_data['score1'] = int(scores[0])
                
                day_games.append(game_data)
        
        result.append({
            'date': day_data['date'],
            'games': day_games
        })
    
    return result

def display_games(html_file_path: str, target_date: str):
    """
    Display games for a specific date
    """
    print("=" * 80)
    print(f"MLB SCHEDULE FOR: {target_date.upper()}")
    print("=" * 80)
    
    try:
        days_data = get_games_for_date(html_file_path, target_date)
        
        for i, day_data in enumerate(days_data, 1):
            print(f"\n📅 DAY {i}: {day_data['date']}")
            print(f"   Games found: {len(day_data['games'])}")
            print("-" * 60)
            
            # Show all games if MAX_GAMES_PER_DAY is None, otherwise limit to the specified number
            games_to_show = day_data['games'] if MAX_GAMES_PER_DAY is None else day_data['games'][:MAX_GAMES_PER_DAY]
            
            for j, game in enumerate(games_to_show, 1):
                print(f"\n   Game {j}:")
                print(f"   Teams: {game['team1']} @ {game['team2']}")
                
                if game['score1'] is not None and game['score2'] is not None:
                    print(f"   Score: {game['score1']} - {game['score2']}")
                else:
                    print(f"   Score: TBD")
                
                if game['time']:
                    print(f"   Time: {game['time']}")
                
                if game['game_type'] and SHOW_GAME_TYPE:
                    print(f"   Type: {game['game_type']}")
                
                if SHOW_RAW_TEXT:
                    print(f"   Raw text: {game['text_content']}")
            
            # Show message if there are more games than what we displayed
            if MAX_GAMES_PER_DAY is not None and len(day_data['games']) > MAX_GAMES_PER_DAY:
                remaining = len(day_data['games']) - MAX_GAMES_PER_DAY
                print(f"\n   ... and {remaining} more games")
        
        print(f"\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        total_games = sum(len(day['games']) for day in days_data)
        completed_games = sum(
            len([g for g in day['games'] if g['score1'] is not None and g['score2'] is not None])
            for day in days_data
        )
        future_games = total_games - completed_games
        
        print(f"Total days shown: {len(days_data)}")
        print(f"Total games shown: {total_games}")
        print(f"Completed games: {completed_games}")
        print(f"Future games: {future_games}")
        
    except FileNotFoundError:
        print(f"Error: Could not find {html_file_path}")
        print("Make sure the file exists in the html/ directory")
    except Exception as e:
        print(f"Error analyzing HTML: {e}")

def main():
    """Main function to show games for a specific date or update Today's Games"""
    parser = argparse.ArgumentParser(description='Show MLB games for a specific date or update Today\'s Games')
    parser.add_argument('--date', '-d', type=str, 
                       help='Specific date to search for (e.g., "March 15, 2025")')
    parser.add_argument('--file', '-f', type=str, default=DEFAULT_HTML_FILE, 
                       help=f'Path to the HTML schedule file (default: {DEFAULT_HTML_FILE})')
    parser.add_argument('--update-today', '-u', action='store_true',
                       help='Update Today\'s Games section with current date format')
    
    args = parser.parse_args()
    
    html_file = args.file
    
    if args.update_today:
        # Update Today's Games with current date
        update_todays_games(html_file)
    elif args.date:
        # Show games for specific date
        target_date = args.date
        print(f"Searching for games on: {target_date}")
        display_games(html_file, target_date)
    else:
        print("Error: Please provide either --date or --update-today")
        print("Usage examples:")
        print("  python random_day_sample.py --date 'August 04, 2025'")
        print("  python random_day_sample.py --update-today")

if __name__ == "__main__":
    main() 