"""
MLB Schedule Scraper
Extracts all games from MLB-schedule.shtml using the approach from day_sample.py
"""

import re
from bs4 import BeautifulSoup
import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

def get_all_games_from_schedule(html_file_path: str) -> List[Dict]:
    """Extract all games from the MLB schedule HTML file"""
    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
    
    games = []
    current_date = None

    # Get today's date in the same format as the schedule uses
    today_str = datetime.now().strftime("%A, %B %-d, %Y").replace(" 0", " ")
    # On Mac, %-d works. On Windows, use %#d.

    for element in soup.find_all(['h3', 'p']):
        if element.name == 'h3':
            date_text = element.get_text(strip=True)
            if date_text == "Today's Games":
                current_date = today_str
            elif date_text and ',' in date_text and '2025' in date_text:
                current_date = date_text
        elif element.name == 'p' and 'game' in element.get('class', []):
            if not current_date:
                continue
                
            if '(Spring)' in element.get_text():
                continue
            
            game_data = {
                'date': current_date,
                'team1': None,
                'team2': None,
                'score1': None,
                'score2': None,
                'time': None,
                'game_type': None,
                'raw_html': str(element),
                'text_content': element.get_text()
            }
            
            time_span = element.find('span', attrs={'tz': 'E'})
            if time_span:
                game_data['time'] = time_span.get_text(strip=True)
            
            team_links = element.find_all('a', href=re.compile(r'/teams/[A-Z]+/'))
            
            if len(team_links) >= 2:
                game_data['team1'] = team_links[0].get_text(strip=True)
                game_data['team2'] = team_links[1].get_text(strip=True)
                
                game_text = element.get_text()
                scores = re.findall(r'\((\d+)\)', game_text)
                if len(scores) >= 2:
                    game_data['score1'] = int(scores[0])
                    game_data['score2'] = int(scores[1])
                elif len(scores) == 1:
                    game_data['score1'] = int(scores[0])
                
                games.append(game_data)
    
    return games

def save_to_csv(games: List[Dict], output_file: str):
    """Save games data to CSV file"""
    if not games:
        print("No games found to save")
        return
    
    fieldnames = ['date', 'team1', 'team2', 'score1', 'score2', 'time', 'game_type', 'text_content']
    
    clean_games = []
    for game in games:
        clean_game = {k: v for k, v in game.items() if k in fieldnames}
        
        if 'text_content' in game:
            clean_text = re.sub(r'<[^>]+>', '', game['text_content'])
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            clean_game['text_content'] = clean_text
        
        clean_games.append(clean_game)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_games)
    
    print(f"Saved {len(games)} games to {output_file}")

def save_to_json(games: List[Dict], output_file: str):
    """Save games data to JSON file"""
    if not games:
        print("No games found to save")
        return
    
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(games, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(games)} games to {output_file}")

def update_csv_from_html(html_file_path: str, csv_file_path: str = 'mlb_schedule_all_games.csv', 
                        json_file_path: str = 'mlb_schedule_all_games.json', 
                        force_update: bool = False):
    """Update CSV file when MLB schedule HTML changes"""
    print("🔄 Checking for updates to MLB schedule...")
    print("=" * 60)
    
    if not os.path.exists(html_file_path):
        print(f"❌ Error: HTML file not found at {html_file_path}")
        return False
    
    html_mtime = os.path.getmtime(html_file_path)
    html_mtime_str = datetime.fromtimestamp(html_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    csv_exists = os.path.exists(csv_file_path)
    csv_mtime = os.path.getmtime(csv_file_path) if csv_exists else 0
    csv_mtime_str = datetime.fromtimestamp(csv_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"📄 HTML file: {html_file_path}")
    print(f"   Last modified: {html_mtime_str}")
    print(f"📊 CSV file: {csv_file_path}")
    print(f"   Last modified: {csv_mtime_str}")
    
    if not force_update and csv_exists and html_mtime <= csv_mtime:
        print(f"✅ CSV is up to date (HTML hasn't changed since last update)")
        return True
    
    print(f"\n🔄 Extracting games from updated HTML...")
    try:
        games = get_all_games_from_schedule(html_file_path)
        
        if not games:
            print("❌ No games found in the HTML file")
            return False
        
        print(f"✅ Successfully extracted {len(games)} games")
        
        # Load previous CSV and count games per date
        prev_games_by_date = None
        prev_games = None
        if csv_exists:
            try:
                prev_df = pd.read_csv(csv_file_path)
                prev_games_by_date = prev_df['date'].value_counts().to_dict()
                prev_games = prev_df.to_dict(orient='records')
            except Exception:
                prev_games_by_date = None
                prev_games = None

        save_to_csv(games, csv_file_path)
        save_to_json(games, json_file_path)
        
        os.utime(csv_file_path, (html_mtime, html_mtime))
        
        print(f"\n✅ Successfully updated:")
        print(f"   - {csv_file_path}")
        print(f"   - {json_file_path}")
        print(f"   - Updated timestamp to match HTML file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating CSV: {e}")
        return False

def main():
    """Main function to extract and save all MLB schedule data"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MLB Schedule Scraper - Extract and update game data')
    parser.add_argument('--update', '-u', action='store_true', 
                       help='Update CSV only if HTML file has changed')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force update even if HTML hasn\'t changed')
    parser.add_argument('--html-file', type=str, default='html/MLB-schedule.shtml',
                       help='Path to HTML schedule file (default: html/MLB-schedule.shtml)')
    parser.add_argument('--csv-file', type=str, default='mlb_schedule_all_games.csv',
                       help='Path to save CSV file (default: mlb_schedule_all_games.csv)')
    parser.add_argument('--json-file', type=str, default='mlb_schedule_all_games.json',
                       help='Path to save JSON file (default: mlb_schedule_all_games.json)')
    
    args = parser.parse_args()
    
    if args.update or args.force:
        success = update_csv_from_html(
            html_file_path=args.html_file,
            csv_file_path=args.csv_file,
            json_file_path=args.json_file,
            force_update=args.force
        )
        
        if success:
            print(f"\n✅ Update completed successfully!")
        else:
            print(f"\n❌ Update failed!")
    else:
        print("Extracting all MLB schedule data...")
        print("=" * 60)
        
        try:
            games = get_all_games_from_schedule(args.html_file)
            
            if not games:
                print("No games found in the HTML file")
                return
            
            print(f"✅ Successfully extracted {len(games)} games")
            
            save_to_csv(games, args.csv_file)
            save_to_json(games, args.json_file)
            
            print(f"\n✅ Data saved to:")
            print(f"   - {args.csv_file}")
            print(f"   - {args.json_file}")
            
        except FileNotFoundError:
            print(f"❌ Error: Could not find {args.html_file}")
            print("Make sure the file exists in the html/ directory")
        except Exception as e:
            print(f"❌ Error analyzing HTML: {e}")

if __name__ == "__main__":
    main()
