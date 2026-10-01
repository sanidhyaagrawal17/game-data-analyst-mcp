"""
Seed script to create a high-fidelity SQLite database of Video Game Sales and Critic Metrics.
Modeled after the classic Kaggle Video Games Sales dataset with EA franchise highlights.
"""
import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "games.db")

def create_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create schema
    cursor.execute("""
    CREATE TABLE games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        platform TEXT NOT NULL,
        year INTEGER,
        genre TEXT NOT NULL,
        publisher TEXT NOT NULL,
        na_sales REAL DEFAULT 0.0,
        eu_sales REAL DEFAULT 0.0,
        jp_sales REAL DEFAULT 0.0,
        other_sales REAL DEFAULT 0.0,
        global_sales REAL DEFAULT 0.0,
        critic_score INTEGER,
        user_score REAL
    );
    """)

    cursor.execute("""
    CREATE TABLE publisher_telemetry (
        publisher TEXT PRIMARY KEY,
        founded_year INTEGER,
        headquarters TEXT,
        active_studios INTEGER,
        primary_engine TEXT
    );
    """)

    # Seed publisher metadata
    publishers_meta = [
        ("Electronic Arts", 1982, "Redwood City, California, US", 24, "Frostbite"),
        ("Nintendo", 1889, "Kyoto, Japan", 12, "Proprietary"),
        ("Activision", 1979, "Santa Monica, California, US", 15, "IW Engine"),
        ("Ubisoft", 1986, "Montreuil, France", 18, "Anvil"),
        ("Sony Computer Entertainment", 1993, "San Mateo, California, US", 20, "Decima / Proprietary"),
        ("Take-Two Interactive", 1993, "New York City, US", 14, "RAGE"),
        ("Microsoft Game Studios", 2000, "Redmond, Washington, US", 22, "Slipspace / Unreal"),
        ("Square Enix", 1975, "Tokyo, Japan", 11, "Luminous / Unreal"),
        ("Capcom", 1979, "Osaka, Japan", 9, "RE Engine"),
        ("Bethesda Softworks", 1986, "Rockville, Maryland, US", 8, "Creation Engine")
    ]
    cursor.executemany("INSERT INTO publisher_telemetry VALUES (?, ?, ?, ?, ?)", publishers_meta)

    # Core curated historical titles (EA and major industry benchmarks)
    curated_games = [
        # Electronic Arts Highlights
        ("FIFA 18", "PS4", 2017, "Sports", "Electronic Arts", 1.27, 8.03, 0.15, 2.35, 11.80, 84, 4.3),
        ("FIFA 19", "PS4", 2018, "Sports", "Electronic Arts", 1.15, 7.82, 0.12, 2.21, 11.30, 83, 4.0),
        ("FIFA 20", "PS4", 2019, "Sports", "Electronic Arts", 1.05, 7.20, 0.10, 2.05, 10.40, 79, 3.2),
        ("FIFA 21", "PS4", 2020, "Sports", "Electronic Arts", 0.95, 6.80, 0.08, 1.90, 9.73, 72, 2.8),
        ("FIFA 22", "PS5", 2021, "Sports", "Electronic Arts", 1.10, 5.40, 0.09, 1.61, 8.20, 78, 3.5),
        ("EA Sports FC 24", "PS5", 2023, "Sports", "Electronic Arts", 1.30, 5.60, 0.11, 1.69, 8.70, 76, 3.1),
        ("Battlefield 3", "X360", 2011, "Shooter", "Electronic Arts", 4.46, 2.13, 0.06, 0.69, 7.34, 84, 7.4),
        ("Battlefield 4", "PS4", 2013, "Shooter", "Electronic Arts", 1.51, 1.86, 0.12, 0.67, 4.16, 85, 7.0),
        ("Battlefield 1", "PS4", 2016, "Shooter", "Electronic Arts", 1.10, 2.06, 0.22, 0.62, 4.00, 89, 7.9),
        ("Battlefield 2042", "PC", 2021, "Shooter", "Electronic Arts", 0.90, 1.15, 0.05, 0.30, 2.40, 68, 2.4),
        ("Apex Legends", "PC", 2019, "Shooter", "Electronic Arts", 4.80, 3.20, 0.90, 1.10, 10.00, 88, 7.2),
        ("Star Wars Jedi: Fallen Order", "PS4", 2019, "Action", "Electronic Arts", 2.15, 2.65, 0.11, 0.98, 5.89, 81, 8.0),
        ("Star Wars Jedi: Survivor", "PS5", 2023, "Action", "Electronic Arts", 1.80, 2.10, 0.08, 0.72, 4.70, 85, 7.8),
        ("The Sims 4", "PC", 2014, "Simulation", "Electronic Arts", 1.00, 1.82, 0.00, 0.23, 3.05, 70, 4.2),
        ("Dead Space Remake", "PS5", 2023, "Action", "Electronic Arts", 0.85, 0.95, 0.04, 0.36, 2.20, 89, 8.6),
        ("Need for Speed: Most Wanted", "PS2", 2005, "Racing", "Electronic Arts", 2.03, 1.83, 0.05, 0.47, 4.37, 82, 8.8),
        ("Mass Effect 2", "X360", 2010, "Role-Playing", "Electronic Arts", 2.00, 1.10, 0.03, 0.29, 3.42, 96, 8.9),
        ("Mass Effect: Andromeda", "PS4", 2017, "Role-Playing", "Electronic Arts", 0.67, 0.88, 0.05, 0.30, 1.90, 71, 5.0),
        ("Dragon Age: Inquisition", "PS4", 2014, "Role-Playing", "Electronic Arts", 1.07, 1.30, 0.08, 0.47, 2.92, 89, 7.4),
        ("Madden NFL 20", "PS4", 2019, "Sports", "Electronic Arts", 2.80, 0.25, 0.00, 0.65, 3.70, 76, 3.9),
        
        # Nintendo Benchmarks
        ("Wii Sports", "Wii", 2006, "Sports", "Nintendo", 41.49, 29.02, 3.77, 8.45, 82.74, 76, 8.1),
        ("Super Mario Bros.", "NES", 1985, "Platform", "Nintendo", 29.08, 3.58, 6.81, 0.77, 40.24, 94, 8.6),
        ("Mario Kart 8 Deluxe", "Switch", 2017, "Racing", "Nintendo", 21.05, 17.50, 6.80, 8.20, 53.55, 92, 8.7),
        ("The Legend of Zelda: Breath of the Wild", "Switch", 2017, "Action", "Nintendo", 12.50, 9.40, 3.80, 4.30, 30.00, 97, 8.8),
        ("Super Smash Bros. Ultimate", "Switch", 2018, "Fighting", "Nintendo", 13.20, 8.10, 5.90, 3.80, 31.00, 93, 8.6),
        
        # Activision Benchmarks
        ("Call of Duty: Modern Warfare 3", "X360", 2011, "Shooter", "Activision", 9.04, 4.24, 0.13, 1.32, 14.73, 88, 3.4),
        ("Call of Duty: Black Ops II", "PS3", 2012, "Shooter", "Activision", 4.99, 5.73, 0.65, 2.42, 13.79, 83, 5.3),
        ("Call of Duty: Warzone", "PC", 2020, "Shooter", "Activision", 8.50, 6.20, 0.40, 2.90, 18.00, 80, 5.5),
        ("Diablo IV", "PC", 2023, "Role-Playing", "Activision", 3.80, 3.10, 0.20, 0.90, 8.00, 86, 5.0),
        
        # Take-Two Benchmarks
        ("Grand Theft Auto V", "PS4", 2014, "Action", "Take-Two Interactive", 3.96, 6.31, 0.38, 1.97, 12.61, 97, 8.3),
        ("Red Dead Redemption 2", "PS4", 2018, "Action", "Take-Two Interactive", 5.26, 6.21, 0.21, 2.26, 13.94, 97, 8.5),
        ("NBA 2K20", "PS4", 2019, "Sports", "Take-Two Interactive", 3.80, 1.20, 0.05, 0.95, 6.00, 78, 2.5),
        
        # Sony Benchmarks
        ("The Last of Us Part II", "PS4", 2020, "Action", "Sony Computer Entertainment", 3.80, 4.60, 0.35, 1.55, 10.30, 93, 5.8),
        ("God of War Ragnarok", "PS5", 2022, "Action", "Sony Computer Entertainment", 4.50, 4.80, 0.45, 1.75, 11.50, 94, 8.1),
        ("Spider-Man", "PS4", 2018, "Action", "Sony Computer Entertainment", 5.96, 4.96, 0.48, 2.18, 13.58, 87, 8.7),
        
        # Ubisoft Benchmarks
        ("Assassin's Creed Valhalla", "PS5", 2020, "Action", "Ubisoft", 1.80, 2.50, 0.15, 0.75, 5.20, 80, 6.7),
        ("Far Cry 6", "PS5", 2021, "Shooter", "Ubisoft", 1.10, 1.60, 0.08, 0.42, 3.20, 73, 5.2),
        ("Rainbow Six Siege", "PC", 2015, "Shooter", "Ubisoft", 3.20, 2.80, 0.25, 0.85, 7.10, 79, 7.3)
    ]

    cursor.executemany("""
    INSERT INTO games (title, platform, year, genre, publisher, na_sales, eu_sales, jp_sales, other_sales, global_sales, critic_score, user_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, curated_games)

    # Generate additional procedurally consistent benchmark titles to total ~250 records
    platforms = ["PS4", "PS5", "X360", "XOne", "XSX", "Switch", "PC", "PS3"]
    genres = ["Action", "Sports", "Shooter", "Role-Playing", "Racing", "Strategy", "Simulation", "Fighting"]
    publishers = [p[0] for p in publishers_meta]
    
    random.seed(42)
    synthetic_records = []
    
    for i in range(1, 220):
        pub = random.choice(publishers)
        genre = "Sports" if pub == "Electronic Arts" and random.random() < 0.45 else random.choice(genres)
        platform = random.choice(platforms)
        year = random.randint(2008, 2024)
        
        critic = random.randint(62, 95)
        user = round(random.uniform(4.0, 9.2), 1)
        na = round(random.uniform(0.1, 4.5), 2)
        eu = round(random.uniform(0.1, 3.8), 2)
        jp = round(random.uniform(0.01, 0.8), 2)
        other = round((na + eu + jp) * 0.18, 2)
        global_s = round(na + eu + jp + other, 2)
        
        title = f"{pub.split()[0]} {genre} Series {year % 100} Vol.{i%5 + 1}"
        synthetic_records.append((
            title, platform, year, genre, pub, na, eu, jp, other, global_s, critic, user
        ))

    cursor.executemany("""
    INSERT INTO games (title, platform, year, genre, publisher, na_sales, eu_sales, jp_sales, other_sales, global_sales, critic_score, user_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, synthetic_records)

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM games")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Database successfully generated at {DB_PATH} with {count} titles.")

if __name__ == "__main__":
    create_database()
