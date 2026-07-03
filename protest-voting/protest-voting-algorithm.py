import math

def calculate_elections_v5(voters_data, total_seats=120, threshold_pct=0.0325):
    """
    מממש את אלגוריתם הבחירות המעודכן לייצוג מחאה.
    
    מתקן את תנאי 9 ו-10: מאפשר למפלגה שכבר עברה את אחוז החסימה 
    (בין אם ישירות ובין אם בזכות רשימת גיבוי קודמת) לקלוט עודפים ולהשלים מנדטים.
    """
    # 1+2. חישוב סך המצביעים, גודל מנדט ואחוז החסימה
    total_voters = sum(party['votes'] for party in voters_data.values())
    mandate_size = math.floor(total_voters / total_seats)
    threshold_votes = total_voters * threshold_pct
    
    print(f"--- נתוני בסיס ---")
    print(f"סה''כ מצביעים: {total_voters:,}")
    print(f"גודל מנדט מקורי: {mandate_size:,}")
    print(f"אחוז החסימה ({threshold_pct*100}% מכלל המצביעים): {math.floor(threshold_votes):,}\n")

    # הכנת מבנה הנתונים לעבודה
    parties = {}
    for name, data in voters_data.items():
        if data['votes'] > 0:
            passed_directly = data['votes'] >= threshold_votes
            parties[name] = {
                'orig_votes': data['votes'],
                'current_unused_votes': data['votes'],
                'backup': data['backup'],
                'passed_directly': passed_directly,
                'passed_via_backup': False, # תהפוך ל-True רק אם עברה בזכות עודפים
                'seats': 0
            }

    # 3+4. חלוקת מנדטים ראשונית - אך ורק למפלגות שעברו ישר בזכות עצמן בקלפי
    for name, party in parties.items():
        if party['passed_directly']:
            full_mandates = math.floor(party['orig_votes'] / mandate_size)
            party['seats'] = full_mandates
            party['current_unused_votes'] = party['orig_votes'] - (full_mandates * mandate_size)

    # 5+6. מעבר על הסיעות בסדר מצביעים עולה לצורך רשימות הגיבוי
    sorted_ascending = sorted(parties.items(), key=lambda x: x[1]['orig_votes'])
    processed_for_backup = set()

    print("--- שלב א': חלוקה ראשונית והעברת קולות לגיבוי ---")
    for name, party in sorted_ascending:
        processed_for_backup.add(name)
        backup_name = party['backup']
        unused = party['current_unused_votes']
        
        if unused == 0 or not backup_name or backup_name not in parties:
            continue
            
        # 7. אם כבר עברנו על רשימת הגיבוי, הקולות נשמטים
        if backup_name in processed_for_backup:
            print(f"הקולות הלא מנוצלים של {name} נשמטו כי רשימת הגיבוי {backup_name} כבר עובדה.")
            party['current_unused_votes'] = 0
            continue
            
        # 8. העברת הקולות לרשימת הגיבוי
        backup_party = parties[backup_name]
        print(f"מעביר {unused:,} קולות מ-{name} לרשימת הגיבוי: {backup_name}")
        backup_party['current_unused_votes'] += unused
        party['current_unused_votes'] = 0
        
        # בדיקה האם רשימת הגיבוי *כבר מוגדרת כעוברת* באותו רגע 
        # (בין אם עברה ישירות בקלפי ובין אם עברה בגלל רשימת גיבוי קודמת)
        has_already_passed = backup_party['passed_directly'] or backup_party['passed_via_backup']
        
        # 9. התנאי המעודכן: הרשימה כבר עברה, ובודקים אם הקולות החדשים משלימים לה מנדטים נוספים
        if has_already_passed:
            if backup_party['current_unused_votes'] >= mandate_size:
                extra_seats = math.floor(backup_party['current_unused_votes'] / mandate_size)
                backup_party['seats'] += extra_seats
                backup_party['current_unused_votes'] -= (extra_seats * mandate_size)
                print(f"-> {backup_name} (כבר עברה חסימה) השלימה {extra_seats} מנדט/ים נוסף/ים מהגיבוי הנוכחי!")
                
        # 10. הרשימה עדיין לא עברה את אחוז החסימה, ובודקים אם היא עוברת *עכשיו* לראשונה
        else:
            total_current_votes = backup_party['current_unused_votes']
            if total_current_votes >= threshold_votes:
                backup_party['passed_via_backup'] = True
                full_mandates = math.floor(total_current_votes / mandate_size)
                backup_party['seats'] = full_mandates
                backup_party['current_unused_votes'] = total_current_votes - (full_mandates * mandate_size)
                print(f"-> {backup_name} עברה את אחוז החסימה כעת בזכות הגיבוי וקיבלה {full_mandates} מנדטים ראשוניים!")

    # 13. חישוב מושבים פנויים שנשארו בפרלמנט
    allocated_seats = sum(p['seats'] for p in parties.values())
    empty_seats = total_seats - allocated_seats
    print(f"\nמנדטים שחולקו בשלב הרגיל והעודפים: {allocated_seats}. מושבים פנויים למחאה: {empty_seats}\n")

    # 14+15+16. חלוקת מושבי המחאה הפנויים
    print("--- שלב ב': חלוקת מושבי מחאה פנויים באיטרציות ---")
    iteration = 1
    while empty_seats > 0:
        min_seats_currently = min(p['seats'] for p in parties.values())
        
        eligible_parties = [
            (name, p) for name, p in parties.items() 
            if p['seats'] == min_seats_currently
        ]
        eligible_parties.sort(key=lambda x: x[1]['orig_votes'], reverse=True)
        
        print(f"איטרציה {iteration} (מפלגות בשכבת מינימום מושבים של {min_seats_currently} - סה''כ {len(eligible_parties)} מפלגות פוטנציאליות):")
        
        if len(eligible_parties) > empty_seats:
            print(f"  [התראה] המושבים הולכים להיגמר באמצע האיטרציה הנוכחית! נותרו {empty_seats} מושבים עבור {len(eligible_parties)} מפלגות בשכבה זו.")
            print(f"  הכרעה תתבצע לפי סדר קולות מקורי מהגדול לקטן כפי שנקבע באלגוריתם.")

        for name, party in eligible_parties:
            if empty_seats == 0:
                print(f"  -> {name} נשארה בחוץ באיטרציה זו כי נגמרו המושבים בפרלמנט באמצע הסבב!")
                continue
                
            party['seats'] += 1
            empty_seats -= 1
            print(f"  -> מעניק מושב מחאה ל-{name} (קולות מקוריים: {party['orig_votes']:,}). מושבים שנותרו בפרלמנט: {empty_seats}")
            
        iteration += 1

    # הדפסת תוצאות סופיות
    print("\n--- תוצאות הבחירות הסופיות ---")
    final_sorted = sorted(parties.items(), key=lambda x: x[1]['seats'], reverse=True)
    for name, party in final_sorted:
        if party['seats'] > 0:
            if party['passed_directly']:
                status = "עברה ישירות בקלפי"
            elif party['passed_via_backup']:
                status = "עברה לאחר עודפים/גיבוי"
            else:
                status = "נכנסה כמושב מחאה פנוי"
                
            print(f"{name}: {party['seats']} מנדטים ({status} | קולות מקוריים: {party['orig_votes']:,})")
            
    print(f"\nסה''כ מנדטים סופי בפרלמנט: {sum(p['seats'] for p in parties.values())}")

