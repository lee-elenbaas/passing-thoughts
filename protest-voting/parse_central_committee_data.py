import csv
import argparse

def create_our_input_from_central_committee(committee_csv_path, output_csv_path):
    # מיפוי רשמי של אותיות הרשימה לשמות המפלגות (עבור הבחירות לכנסת ה-25)
    # המיפוי כולל את המפלגות המרכזיות. כל מפלגה שלא מופיעה כאן תיקרא לפי האותיות שלה.
    party_names_mapping = {
        'מחל': 'הליכוד', 'פה': 'יש עתיד', 'ט': 'הציונות הדתית', 
        'כן': 'המחנה הממלכתי', 'שס': 'שס', 'ג': 'יהדות התורה', 
        'ל': 'ישראל ביתנו', 'עם': 'רע"מ', 'ום': 'חד"ש תע"ל', 
        'אמת': 'העבודה', 'מרצ': 'מרצ', 'ד': 'בל"ד', 'ב': 'הבית היהודי',
        'אצ': 'חופש כלכלי', 'יז': 'הכלכלית החדשה', 'צ': 'צעירים בוערים',
        'ף': 'הפיראטים'
    }

    # הגדרת רשימות הגיבוי הדו-כיווניות (הסכמי העודפים ההיסטוריים)
    # המפתח והערך צריכים להתאים לשמות המפלגות הסופיים (אחרי המיפוי)
    backup_agreements = {
        'הליכוד': 'הציונות הדתית',
        'הציונות הדתית': 'הליכוד',
        'יש עתיד': 'המחנה הממלכתי',
        'המחנה הממלכתי': 'יש עתיד',
        'שס': 'יהדות התורה',
        'יהדות התורה': 'שס',
        'העבודה': 'מרצ',
        'מרצ': 'העבודה'
    }

    # דיקשנרי לצבירת הקולות הארציים: { party_letter: total_votes }
    national_votes = {}

    excluded_headers = {
        'סמל ועדה', 'ברזל', 'שם ישוב', 'סמל ישוב', 'קלפי', 'מספר קלפי', 'ריכוז', 'שופט', 
        'בזב', 'בז"ב', 'מצביעים', 'פסולים', 'כשרים', 'קולות כשרים', 'שם ישוב/קלפי'
    }

    # זיהוי קידוד הקובץ (utf-8-sig או cp1255)
    encoding = 'utf-8-sig'
    try:
        with open(committee_csv_path, mode='r', encoding=encoding) as f:
            f.read(1024)
    except UnicodeDecodeError:
        encoding = 'cp1255'

    with open(committee_csv_path, mode='r', encoding=encoding) as f:
        # בקבצי הוועדה, השורה הראשונה לפעמים מכילה כותרות משניות, נשתמש ב-reader רגיל כדי לנתח
        reader = csv.reader(f)
        headers = next(reader)
        
        # מציאת האינדקס שבו מתחילות עמודות המפלגות. 
        # לרוב, המפלגה הראשונה מופיעה אחרי עמודות קבועות כמו 'בז"ב', 'פסולים', 'כשרים' וכו'.
        # אנחנו נחפש את העמודה הראשונה שאינה ברשימת הכותרות המוחרגות ואורכה קטן או שווה ל-3 תווים
        start_index = None
        for i, h in enumerate(headers):
            h_clean = h.strip()
            if h_clean in excluded_headers:
                continue
            # אותיות הרשימה הן בדרך כלל בין 1 ל-3 אותיות בעברית
            if i > 5 and 1 <= len(h_clean) <= 3 and h_clean.isalpha():
                start_index = i
                break
        
        if start_index is None:
            raise ValueError("לא ניתן היה לזהות את תחילת עמודות המפלגות בקובץ ה-CSV.")

        # הגדרת עמודות המפלגות שנסכום (אינדקס ושם) תוך סינון עמודות שאינן מפלגות
        party_columns = []
        for i, col in enumerate(headers):
            col_clean = col.strip()
            if i >= start_index and col_clean not in excluded_headers:
                party_columns.append((i, col_clean))
                national_votes[col_clean] = 0

        # סכימת הקולות מכל השורות (כל היישובים/קלפיות)
        for row_index, row in enumerate(reader):
            if not row:
                continue
            for col_idx, col_name in party_columns:
                if col_idx < len(row):
                    cell_value = row[col_idx].strip()
                    if cell_value.isdigit():
                        national_votes[col_name] += int(cell_value)

    # כתיבת קובץ הקלט החדש בפורמט שהאלגוריתם שלנו דורש
    with open(output_csv_path, mode='w', newline='', encoding='utf-8-sig') as f_out:
        writer = csv.writer(f_out)
        writer.writerow(['שם המפלגה', 'קולות מקוריים', 'רשימת גיבוי'])
        
        # מעבר על כל המפלגות שסכמנו, תרגום השם שלהן והצמדת רשימת הגיבוי
        for letter, total_votes in national_votes.items():
            if total_votes == 0:
                continue  # מדלגים על רשימות שנרשמו אך לא קיבלו אף קול בקלפי
                
            # תרגום אותיות הרשימה לשם המפלגה (אם קיים במיפוי, אחרת נשארים עם האותיות)
            party_name = party_names_mapping.get(letter, f"רשימת {letter}")
            
            # בדיקה האם יש למפלגה זו הסכם גיבוי מוגדר
            backup_party = backup_agreements.get(party_name, 'אין')
            
            writer.writerow([party_name, total_votes, backup_party])

    print(f"הקובץ עובד בהצלחה! סה''כ עובדו {len(national_votes)} רשימות.")
    print(f"קובץ הקלט החדש מוכן בכתובת: '{output_csv_path}'")

# --- הרצה מקומית ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="מיפוי נתוני ועדת הבחירות המרכזית לפורמט אלגוריתם הצבעות מחאה")
    parser.add_argument("input_file", nargs="?", default=None, help="קובץ ה-CSV המקורי של ועדת הבחירות (ברירת מחדל: exp_results.csv)")
    parser.add_argument("output_file", nargs="?", default=None, help="קובץ הפלט שיווצר עבור האלגוריתם (ברירת מחדל: elections_input_data.csv)")
    parser.add_argument("-i", "--input", default=None, help="קובץ ה-CSV המקורי של ועדת הבחירות (חלופה לארגומנט מיקומי)")
    parser.add_argument("-o", "--output", default=None, help="קובץ הפלט שיווצר עבור האלגוריתם (חלופה לארגומנט מיקומי)")
    
    args = parser.parse_args()
    
    input_from_committee = args.input or args.input_file or 'exp_results.csv'
    our_output_file = args.output or args.output_file or 'elections_input_data.csv'
    
    try:
        create_our_input_from_central_committee(input_from_committee, our_output_file)
    except FileNotFoundError:
        print(f"שגיאה: לא נמצא קובץ המקור '{input_from_committee}' של ועדת הבחירות.")
        print(f"אנא ודא שקובץ המקור קיים בנתיב המבוקש.")

