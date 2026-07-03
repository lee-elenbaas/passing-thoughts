import math
import logging

# הגדרת לוגר ייעודי עבור אלגוריתם הבחירות
logger = logging.getLogger("elections")

def calculate_elections(voters_data, total_seats=120, threshold_pct=0.0325):
    """
    מממש את אלגוריתם הבחירות לייצוג מחאה.
    מחזיר דיקשנרי מעודכן של המפלגות עם תוצאות המנדטים הסופיות.
    """
    # 1+2. חישוב סך המצביעים, גודל מנדט ואחוז החסימה
    total_voters = sum(party['votes'] for party in voters_data.values())
    mandate_size = math.floor(total_voters / total_seats)
    threshold_votes = total_voters * threshold_pct
    
    logger.info(f"נתוני בסיס - מצביעים: {total_voters:,}, גודל מנדט: {mandate_size:,}, אחוז חסימה: {math.floor(threshold_votes):,}")

    # הכנת מבנה הנתונים לעבודה (סינון מפלגות ללא קולות)
    parties = {}
    for name, data in voters_data.items():
        if data['votes'] > 0:
            passed_directly = data['votes'] >= threshold_votes
            parties[name] = {
                'orig_votes': data['votes'],
                'current_unused_votes': data['votes'],
                'backup': data['backup'],
                'passed_directly': passed_directly,
                'passed_via_backup': False,
                'seats': 0
            }

    # 3+4. חלוקת מנדטים ראשונית (רק למי שעברה ישירות בקלפי)
    for name, party in parties.items():
        if party['passed_directly']:
            full_mandates = math.floor(party['orig_votes'] / mandate_size)
            party['seats'] = full_mandates
            party['current_unused_votes'] = party['orig_votes'] - (full_mandates * mandate_size)

    # 5+6. מעבר על הסיעות בסדר מצביעים עולה לצורך רשימות הגיבוי
    sorted_ascending = sorted(parties.items(), key=lambda x: x[1]['orig_votes'])
    processed_for_backup = set()

    logger.info("מתחיל שלב א': חלוקה ראשונית והעברת קולות לגיבוי")
    for name, party in sorted_ascending:
        processed_for_backup.add(name)
        backup_name = party['backup']
        unused = party['current_unused_votes']
        
        if unused == 0 or not backup_name or backup_name not in parties:
            continue
            
        # 7. אם כבר עברנו על רשימת הגיבוי, הקולות נשמטים
        if backup_name in processed_for_backup:
            logger.warning(f"הקולות הלא מנוצלים של {name} נשמטו (רשימת הגיבוי {backup_name} כבר עובדה).")
            party['current_unused_votes'] = 0
            continue
            
        # 8. העברת הקולות לרשימת הגיבוי
        backup_party = parties[backup_name]
        logger.debug(f"מעביר {unused:,} קולות מ-{name} לרשימת הגיבוי: {backup_name}")
        backup_party['current_unused_votes'] += unused
        party['current_unused_votes'] = 0
        
        has_already_passed = backup_party['passed_directly'] or backup_party['passed_via_backup']
        
        # 9. הרשימה כבר עברה, ובודקים אם הקולות החדשים משלימים מנדטים נוספים
        if has_already_passed:
            if backup_party['current_unused_votes'] >= mandate_size:
                extra_seats = math.floor(backup_party['current_unused_votes'] / mandate_size)
                backup_party['seats'] += extra_seats
                backup_party['current_unused_votes'] -= (extra_seats * mandate_size)
                logger.debug(f"-> {backup_name} השלימה {extra_seats} מנדט/ים נוסף/ים מהגיבוי הנוכחי.")
                
        # 10. הרשימה עדיין לא עברה, ובודקים אם היא עוברת כעת לראשונה
        else:
            total_current_votes = backup_party['current_unused_votes']
            if total_current_votes >= threshold_votes:
                backup_party['passed_via_backup'] = True
                full_mandates = math.floor(total_current_votes / mandate_size)
                backup_party['seats'] = full_mandates
                backup_party['current_unused_votes'] = total_current_votes - (full_mandates * mandate_size)
                logger.debug(f"-> {backup_name} עברה את אחוז החסימה כעת בזכות הגיבוי וקיבלה {full_mandates} מנדטים.")

    # 13. חישוב מושבים פנויים שנשארו בפרלמנט
    allocated_seats = sum(p['seats'] for p in parties.values())
    empty_seats = total_seats - allocated_seats
    logger.info(f"מנדטים שחולקו בשלב הרגיל והעודפים: {allocated_seats}. מושבים פנויים למחאה: {empty_seats}")

    # 14+15+16. חלוקת מושבי המחאה הפנויים
    logger.info("מתחיל שלב ב': חלוקת מושבי מחאה פנויים באיטרציות")
    iteration = 1
    while empty_seats > 0:
        min_seats_currently = min(p['seats'] for p in parties.values())
        
        eligible_parties = [
            (name, p) for name, p in parties.items() 
            if p['seats'] == min_seats_currently
        ]
        eligible_parties.sort(key=lambda x: x[1]['orig_votes'], reverse=True)
        
        if len(eligible_parties) > empty_seats:
            logger.warning(f"איטרציה {iteration}: המושבים יגמרו באמצע האיטרציה! נותרו {empty_seats} מושבים עבור {len(eligible_parties)} מפלגות.")

        for name, party in eligible_parties:
            if empty_seats == 0:
                logger.debug(f"איטרציה {iteration}: {name} נשמטה מהסבב הנוכחי כי נגמרו המושבים.")
                continue
                
            party['seats'] += 1
            empty_seats -= 1
            logger.debug(f"איטרציה {iteration}: מעניק מושב מחאה ל-{name}. מושבים שנותרו: {empty_seats}")
            
        iteration += 1

    return parties

