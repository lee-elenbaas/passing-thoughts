import logging
# ייבוא האלגוריתם הטהור מהקובץ הראשון
from protest_voting_algorithm import calculate_elections

# 1. קונפיגורציית לוגים להרצה הנוכחית 
# (ניתן לשנות את ה-level ל-logging.DEBUG כדי לראות את שלבי הביניים המפורטים)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# 2. נתוני הדוגמה של הבחירות (2022)
elections_2022_data = {
    'הליכוד': {'votes': 1115336, 'backup': 'הציונות הדתית'},
    'יש עתיד': {'votes': 847435, 'backup': 'המחנה הממלכתי'},
    'הציונות הדתית': {'votes': 516470, 'backup': 'הליכוד'},
    'המחנה הממלכתי': {'votes': 432482, 'backup': 'יש עתיד'},
    'שס': {'votes': 392964, 'backup': 'יהדות התורה'},
    'יהדות התורה': {'votes': 280194, 'backup': 'שס'},
    'ישראל ביתנו': {'votes': 213687, 'backup': None},
    'רע''מ': {'votes': 194047, 'backup': None},
    'חד''ש תע''ל': {'votes': 178735, 'backup': None},
    'העבודה': {'votes': 175992, 'backup': 'מרצ'},
    'מרצ': {'votes': 150793, 'backup': 'העבודה'},
    'בל''ד': {'votes': 138617, 'backup': None},
    'הבית היהודי': {'votes': 56775, 'backup': None}
}

def main():
    # 3. הרצת האלגוריתם
    results = calculate_elections(elections_2022_data, total_seats=120)
    
    # 4. הדפסת התוצאות הסופיות מחוץ לאלגוריתם
    print("\n==============================================")
    print("           תוצאות הבחירות הסופיות             ")
    print("==============================================")
    
    final_sorted = sorted(results.items(), key=lambda x: x[1]['seats'], reverse=True)
    for name, party in final_sorted:
        if party['seats'] > 0:
            if party['passed_directly']:
                status = "עברה ישירות בקלפי"
            elif party['passed_via_backup']:
                status = "עברה לאחר עודפים/גיבוי"
            else:
                status = "נכנסה כמושב מחאה פנוי"
                
            print(f"{name}: {party['seats']} מנדטים ({status} | קולות מקוריים: {party['orig_votes']:,})")
            
    print("----------------------------------------------")
    print(f"סה''כ מנדטים סופי בפרלמנט: {sum(p['seats'] for p in results.values())}")
    print("==============================================")

if __name__ == "__main__":
    main()

