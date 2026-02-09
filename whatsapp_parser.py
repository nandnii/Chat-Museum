"""
WhatsApp Chat Parser
Parses exported WhatsApp chat files into structured data

Usage:
    python whatsapp_parser.py NAP_chat.txt
"""

import re
import pandas as pd
from datetime import datetime
from pathlib import Path

def parse_whatsapp_chat(file_path):
    """
    Parse WhatsApp chat export file
    
    Expected format:
    DD/MM/YY, HH:MM am/pm - Sender Name: Message text
    
    Returns:
        DataFrame with columns: datetime, date, time, sender, message
    """
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    messages = []
    current_message = None
    
    # Regex pattern for WhatsApp message line
    # Matches: "08/11/21, 7:59 pm - Ananya Roomie🏘️: Tournament se Room allotment ka safar"
    pattern = r'^(\d{1,2}/\d{1,2}/\d{2}),\s(\d{1,2}:\d{2}\s[ap]m)\s-\s([^:]+):\s(.+)$'
    
    for line in lines:
        # Try to match a new message
        match = re.match(pattern, line.strip())
        
        if match:
            # If we had a previous message, save it
            if current_message:
                messages.append(current_message)
            
            # Start new message
            date_str, time_str, sender, message_text = match.groups()
            
            # Parse datetime
            datetime_str = f"{date_str}, {time_str}"
            try:
                dt = datetime.strptime(datetime_str, "%d/%m/%y, %I:%M %p")
            except:
                # If parsing fails, use a placeholder
                dt = None
            
            current_message = {
                'datetime': dt,
                'date': date_str,
                'time': time_str,
                'sender': sender.strip(),
                'message': message_text.strip()
            }
        
        else:
            # This is a continuation of the previous message (multiline)
            if current_message and line.strip():
                current_message['message'] += '\n' + line.strip()
    
    # Don't forget the last message
    if current_message:
        messages.append(current_message)
    
    # Convert to DataFrame
    df = pd.DataFrame(messages)
    
    # Add helpful columns
    if 'datetime' in df.columns:
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        df['year_month'] = df['datetime'].dt.strftime('%Y-%m')
        df['day_of_week'] = df['datetime'].dt.day_name()
        df['hour'] = df['datetime'].dt.hour
    
    return df

def analyze_chat_basics(df):
    """Generate basic statistics about the chat"""
    
    print("\n" + "="*70)
    print("📱 WHATSAPP CHAT ANALYSIS")
    print("="*70)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Messages: {len(df):,}")
    print(f"   Date Range: {df['datetime'].min().date().strftime('%d %b %y')} to {df['datetime'].max().date().strftime('%d %b %y')}")
    print(f"   Duration: {(df['datetime'].max() - df['datetime'].min()).days} days")
    
    print(f"\n👥 Participants:")
    sender_counts = df['sender'].value_counts()
    for sender, count in sender_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {sender}: {count:,} messages ({percentage:.1f}%)")
    
    print(f"\n📅 Messages by Year:")
    if 'year' in df.columns:
        yearly = df['year'].value_counts().sort_index()
        for year, count in yearly.items():
            print(f"   {year}: {count:,} messages")
    
    print(f"\n🕐 Most Active Hours:")
    if 'hour' in df.columns:
        hourly = df['hour'].value_counts().sort_index()
        top_hours = hourly.nlargest(5)
        for hour, count in top_hours.items():
            time_label = f"{hour:02d}:00 - {hour+1:02d}:00"
            print(f"   {time_label}: {count:,} messages")
    
    # # Detect special message types
    # media_count = df['message'].str.contains('<Media omitted>', case=False, na=False).sum()
    # deleted_count = df['message'].str.contains('This message was deleted', case=False, na=False).sum()
    
    # print(f"\n📎 Special Messages:")
    # print(f"   Media files: {media_count:,}")
    # print(f"   Deleted messages: {deleted_count:,}")

def detect_language_patterns(df):
    """Detect Hindi vs English usage patterns"""
    
    print("\n" + "="*70)
    print("🗣️  LANGUAGE PATTERNS")
    print("="*70)
    
    # Simple heuristic: messages with Devanagari script are Hindi-heavy
    # Messages with only ASCII are English
    # Mixed are Hinglish
    
    def detect_script(text):
        # if pd.isna(text) or text in ['<Media omitted>', 'This message was deleted']:
        #     return 'other'
        
        # Check for Hindi/Devanagari characters
        hindi_chars = sum(1 for char in text if '\u0900' <= char <= '\u097F')
        total_chars = len(text)
        
        if total_chars == 0:
            return 'other'
        
        hindi_ratio = hindi_chars / total_chars
        
        if hindi_ratio > 0.3:
            return 'hindi-heavy'
        elif hindi_ratio > 0.05:
            return 'hinglish'
        else:
            return 'english'
    
    df['language_type'] = df['message'].apply(detect_script)
    
    lang_counts = df['language_type'].value_counts()
    print(f"\nLanguage Distribution:")
    for lang, count in lang_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   {lang}: {count:,} messages ({percentage:.1f}%)")
    
    return df

def find_conversation_starters(df):
    """Find who usually starts conversations after long gaps"""
    
    print("\n" + "="*70)
    print("💬 CONVERSATION PATTERNS")
    print("="*70)
    
    # Calculate time gaps between messages
    df = df.sort_values('datetime').reset_index(drop=True)
    df['time_since_last'] = df['datetime'].diff()
    
    # Consider a gap of > 3 hours as a "new conversation"
    conversation_starters = df[df['time_since_last'] > pd.Timedelta(hours=3)]
    
    if len(conversation_starters) > 0:
        starter_counts = conversation_starters['sender'].value_counts()
        print(f"\nWho Starts Conversations (after 3+ hour gaps):")
        for sender, count in starter_counts.items():
            percentage = (count / len(conversation_starters)) * 100
            print(f"   {sender}: {count:,} times ({percentage:.1f}%)")
    
    return df

def sample_messages_by_period(df, n=5):
    """Show sample messages from different time periods"""
    
    print("\n" + "="*70)
    print("📝 SAMPLE MESSAGES")
    print("="*70)
    
    if 'year_month' in df.columns:
        periods = df['year_month'].unique()
        
        # Show samples from first, middle, and last periods
        sample_periods = [periods[0], periods[len(periods)//2], periods[-1]]
        
        for period in sample_periods:
            period_df = df[df['year_month'] == period]
            print(f"\n--- {period} ---")
            samples = period_df.head(n)
            for _, row in samples.iterrows():
                sender = row['sender'].split()[0]  # First name only
                msg = row['message'][:60] + '...' if len(row['message']) > 60 else row['message']
                print(f"   {sender}: {msg}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("WHATSAPP CHAT PARSER")
    print("="*70)
    
    # Get file path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "NAP_chat.txt"  # Default file name
    
    if not Path(file_path).exists():
        print(f"\n❌ Error: File not found - {file_path}")
        print("\nUsage: python whatsapp_parser.py <chat_file.txt>")
        sys.exit(1)
    
    print(f"\nParsing: {file_path}")
    print("="*70)
    
    try:
        # Parse the chat
        df = parse_whatsapp_chat(file_path)
        # Remove media & deleted messages
        df = df[(df.message != '<Media omitted>') & (df.message != 'This message was deleted')]

        print(f"\n✅ Successfully parsed {len(df):,} messages!")
        
        df.to_csv('Chat_parsed.csv', index=False)
        
        # Run analyses
        analyze_chat_basics(df)

        df = detect_language_patterns(df)
        df = find_conversation_starters(df)
        sample_messages_by_period(df)
        
        # Save to CSV
        output_file = file_path.replace('.txt', '_parsed.csv')
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n💾 Data saved to: {output_file}")
        
        print("\n" + "="*70)
        print("✨ Next Step: Use this CSV for LLM analysis!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error parsing file: {e}")
        import traceback
        traceback.print_exc()
