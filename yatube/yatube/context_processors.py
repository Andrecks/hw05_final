import datetime as dt


def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    year = dt.datetime.now().year
    return {
        'year': year
    }


def calc_age(request):
    born = dt.date(1995, 10, 9)
    today = dt.date.today()
    age = today.year - born.year - ((today.month,
                                     today.day) < (born.month, born.day)
                                    )
    return {
        'age': age
    }
