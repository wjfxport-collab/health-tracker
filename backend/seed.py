import database
from datetime import datetime, timedelta
import random

def seed():
    database.init_db()
    
    # Check if entries already exist
    existing = database.get_all_entries()
    if existing:
        print(f"Database already contains {len(existing)} entries. Skipping seed.")
        return

    print("Seeding sample weight and step entries...")
    today = datetime.now()
    
    # 14 days of realistic sample progression
    # Starting weight 183.5 going down to 178.2
    base_weight = 183.5
    for i in range(13, -1, -1):
        d = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        # slight downward drift with daily fluctuations
        day_weight = round(base_weight - (13 - i) * 0.38 + random.uniform(-0.4, 0.4), 1)
        # steps between 7500 and 14000
        day_steps = random.randint(7800, 13800)
        
        sample_notes = ""
        if i == 0:
            sample_notes = "Morning run in the park & healthy breakfast"
        elif i == 3:
            sample_notes = "10k morning walk + gym session"
        elif i == 7:
            sample_notes = "Rest day, hit step goal with evening stroll"
            
        database.upsert_entry(d, weight=day_weight, steps=day_steps, notes=sample_notes)
    
    print("Seed completed successfully with 14 days of data!")

if __name__ == '__main__':
    seed()
