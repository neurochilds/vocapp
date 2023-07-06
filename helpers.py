from datetime import datetime, timedelta


def clean_dict(dictionary: dict):
    ''''
    Limits the dictionary to a maximum of 5 definitions for each part of speech (e.g., verb, noun)
    '''
    clean_dict = {}
    for pos in dictionary.keys():
        clean_dict[pos] = []
        count = 0
        for definition in dictionary[pos]:
            if definition[0] == '(':
                continue
            clean_dict[pos].append(definition)
            count += 1
            if count == 5:
                break
    return clean_dict


def update_box(current_box: int, is_correct: bool):
    '''
    Implements spaced-repetition algo.
    When words are correctly recalled from their definition, they are moved to the next box.
    When incorrectly recalled, they are moved to a lower box.
    The box they are in depends when they will next be reviewed.
    Words in higher boxes are demoted most, up to -5 boxes lower.
    Words in higher boxes have a greater interval until their next revision date, up to 56 days.
    '''

    # NEXT_INTERVAL[current_box] -> learn words in box[1] every 1 day, in box[10] every 56 days
    NEXT_INTERVAL = [None, 1, 2, 3, 5, 8, 12, 18, 28, 42, 56] 

    # REDUCE_BOX[current_box] -> if word in box 3 wrong, move it back to box 2 (-1); if word in box 10 wrong, move word back to box 5 (-5)
    REDUCE_BOX = [None, 0, -1, -1, -1, -2, -2, -3, -3, -4, -5] 

    if is_correct and current_box < 10:
        new_box = current_box + 1
    elif not is_correct: 
        new_box = current_box + REDUCE_BOX[current_box]
    else:
        # Current box does not change as it is either cannot go any lower or higher
        pass

    last_reviewed_date = datetime.utcnow()
    next_review_date = datetime.utcnow() + timedelta(days=NEXT_INTERVAL[new_box])

    return new_box, last_reviewed_date, next_review_date


def days_hours_mins(end: datetime, start: datetime, is_last: bool = False):
    '''
    Takes in two datetimes and return the difference as a string -> 'X days, Y hours, Z minutes'.
    '''
    td = (end - start)

    if td < timedelta(minutes=1):
        if is_last: return 'Just now'
        return 'Now!'
    
    time = {}
    time['days'] = td.days
    seconds = td.seconds
    time['hours'] = seconds // 3600
    time['minutes'] = (seconds // 60) % 60

    string = ''

    for unit in time.keys():
        if time[unit] > 0 or string: string += f'{time[unit]} {unit} '

    return string