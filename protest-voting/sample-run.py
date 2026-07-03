import csv
import logging
# ייבוא האלגוריתם הטהור מהקובץ הראשון
from protest_voting_algorithm import calculate_elections

# 1. קונפיגורציית לוגים להרצה הנוכחית 
# (ניתן לשנות את ה-level ל-logging.DEBUG כדי לראות את שלבי הביניים המפורטים)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def load_voters_from_csv(filename):
    """קורא את קובץ נתוני הקלט ומחזיר דיקשנרי מותאם לאלגוריתם"""
    voters_data = {}
    with open(filename, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['שם המפלגה'].strip()
            votes = int(row['קולות מקוריים'].strip())
            backup = row['רשימת גיבוי'].strip()
            
            # טיפול במצב שאין רשימת גיבוי
            if backup == 'אין' or backup == '':
                backup = None
                
            voters_data[name] = {'votes': votes, 'backup': backup}
    return voters_data

def write_results_to_csv(filename, results):
    """כותב את תוצאות המנדטים הסופיות לקובץ פלט CSV"""
    with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['שם המפלגה', 'קולות מקוריים', 'מנדטים סופיים', 'סטטוס כניסה'])
        
        # מיון התוצאות מהמנדטים הגבוהים לנמוכים
        final_sorted = sorted(results.items(), key=lambda x: x[1]['seats'], reverse=True)
        for name, party in final_sorted:
            if party['seats'] > 0:
                if party['passed_directly']:
                    status = "עברה ישירות בקלפי"
                elif party['passed_via_backup']:
                    status = "עברה לאחר עודפים/גיבוי"
                else:
                    status = "נכנסה כמושב מחאה פנוי"
                
                writer.writerow([name, party['orig_votes'], party['seats'], status])

def main():
    input_file = 'elections_data_2022.csv'
    output_file = 'elections_results_2022.csv'
    
    try:
        # 1. טעינת הנתונים מקובץ ה-CSV
        print(f"טוען נתונים מתוך הקובץ: {input_file}...")
        voters_data = load_voters_from_csv(input_file)
        
        # 2. הרצת האלגוריתם המופרד
        print("מריץ את אלגוריתם הבחירות הדינמי...")
        results = calculate_elections(voters_data, total_seats=120)
        
        # 3. כתיבת התוצאות המחושבות לקובץ CSV חדש
        print(f"כותב את תוצאות האמת לתוך: {output_file}...")
        write_results_to_csv(output_file, results)
        
        print("\nהתהליך הסתיים בהצלחה! קובץ התוצאות מוכן.")
        
    except FileNotFoundError:
        print(f"\nשגיאה: לא ניתן למצוא את קובץ הקלט '{input_file}'.")
        print("אנא ודא שהקובץ קיים באותה תיקייה ומכיל את הכותרות: שם המפלגה, קולות מקוריים, רשימת גיבוי.")

if __name__ == "__main__":
    main()

