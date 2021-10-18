import os
from datetime import timedelta, datetime

from pytz import timezone

import i18n
from sqlalchemy import table, column, Integer, String, insert, func
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import Date

from exc import FoodNotFound, UnitNotFound, UnitNotDefined
from models import DailyReport, User, UserProfile, FoodUnit, FoodLog, Food, Unit, FoodName, UnitName, date_now
from typing import Optional

UTC = timezone('UTC')


def create_default_units(session: Session):
    """
    Create default units: grams and pc. Used in migrations and tests
    :param session:
    :return:
    """
    unit = table('unit')
    unit_name = table(
        'unit_name',
        column('unit_id', Integer),
        column('name', String),
        column('language', String),
    )
    units = [
        {
            'ru': ['г', 'грамм', 'гр', 'грам', 'граммов'],
            'en': ['g', 'gram', 'gr', 'grams'],
        },
        {
            'ru': ['шт', 'штук', 'штука'],
            'en': ['pc', 'pcs'],
        }
    ]
    gram_unit_id = None
    pc_unit_id = None
    for u in units:
        unit_id = session.execute(
            insert(unit).values()
        ).lastrowid

        if gram_unit_id is None:
            gram_unit_id = unit_id
        else:
            pc_unit_id = unit_id

        for lang in u.keys():
            for name in u[lang]:
                session.execute(
                    insert(unit_name).values(
                        {
                            'unit_id': unit_id,
                            'name': name,
                            'language': lang
                        }
                    )
                )
    session.commit()
    return gram_unit_id, pc_unit_id


def get_gram_unit(db_session: Session) -> Unit:
    """
    Shorthand for getting a gram unit
    :param db_session:
    :return:
    """
    return db_session.query(UnitName).filter_by(language='en', name='g').one().unit


def get_food_by_name(db_session: Session, locale: str, food_name: str) -> Food:
    """
    :param db_session:
    :param locale:
    :param food_name:
    :return:
    :raises: NoResultFound if no food found with this name
    """
    return db_session.query(FoodName).filter_by(language=locale, name=food_name).one().food


def get_or_create_user(db_session: Session, telegram_id) -> Optional[User]:
    """
    :param db_session:
    :param telegram_id:
    :return:
    """
    user = db_session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        if not os.getenv('ALLOW_NEW_USERS', '0').lower() in ['1', 'yes', 'true']:
            return None
        user = User(telegram_id=telegram_id)
        db_session.add(user)
        db_session.commit()
        # TODO: configure calories etc. See https://www.calculator.net/macro-calculator.html
        db_session.add(UserProfile(user_id=user.id,
                                   daily_calories=1538,
                                   daily_carbs=205,
                                   daily_fat=44,
                                   daily_protein=94))
        db_session.add(DailyReport(user_id=user.id,
                       last_report_date=date_now()))
        db_session.commit()
    return user


def create_unit(db_session: Session, locale: str, unit_name: str) -> Unit:
    """

    :param db_session:
    :param locale:
    :param unit_name:
    :return:
    """
    u = Unit()
    db_session.add(u)
    if db_session.query(UnitName).filter_by(
            language=locale, name=unit_name).count() > 0:
        db_session.rollback()
        raise IntegrityError
    db_session.commit()  # flush?
    un = UnitName(unit_id=u.id, language=locale, name=unit_name)
    db_session.add(un)
    db_session.commit()
    return u


def define_unit_for_food(db_session: Session, food: Food, unit: Unit, grams: float, is_default: bool) -> None:
    try:
        fu = db_session.query(FoodUnit).filter_by(
            food_id=food.id, unit_id=unit.id).one()
    except NoResultFound:
        fu = FoodUnit(food_id=food.id, unit_id=unit.id)
    fu.grams = grams
    fu.is_default = is_default
    db_session.add(fu)
    db_session.commit()  # flush?
    if fu.is_default:
        # remove default from other units
        db_session.execute("""UPDATE food_unit SET is_default = :false 
            WHERE food_id = :food_id AND unit_id <> :unit_id""",
                           {'false': False, 'food_id': food.id, 'unit_id': unit.id})
        db_session.commit()
    gram_unit = get_gram_unit(db_session)
    if unit.id != gram_unit.id:
        fu = db_session.query(FoodUnit).filter_by(
            food_id=food.id, unit_id=gram_unit.id).first()
        if not fu:
            # also add grams
            fu = FoodUnit(food_id=food.id, unit_id=gram_unit.id,
                          is_default=False, grams=1)
            db_session.add(fu)
            db_session.commit()


def get_unit_by_name(db_session: Session, locale: str, unit_name: str) -> Unit:
    """
    :param db_session:
    :param locale:
    :param unit_name:
    :return:
    :raises: NoResultFound if no unit found with this name
    """
    return db_session.query(UnitName).filter_by(
        language=locale, name=unit_name).one().unit


def get_default_unit_for_food(db_session: Session, food: Food) -> Unit:
    """
    :param db_session:
    :param food:
    :return:
    """
    return db_session.query(FoodUnit).filter_by(
        food_id=food.id, is_default=True).one().unit


def log_food(db_session: Session, locale: str, user: User,
             food_name: str, unit_name: str, qty: float,
             date=None) -> FoodLog:
    """
    Adds a food log entry for user
    :param db_session:
    :param locale:
    :param user:
    :param food_name:
    :param unit_name:
    :param qty:
    :param date: default: today's date (UTC)
    :return: FoodLog created log record
    :raises: FoodNotFound if no food was found with food_name, locale
    :raises: UnitNotFound if no unit was found with unit_name, locale
    :raises: UnitNotDefined if unit was found but not defined for this food
    """
    try:
        food = get_food_by_name(db_session, locale, food_name)
    except NoResultFound:
        raise FoodNotFound

    if unit_name is None:
        unit = get_default_unit_for_food(db_session, food)
    else:
        try:
            unit = get_unit_by_name(db_session, locale, unit_name)
        except NoResultFound:
            raise UnitNotFound

    try:
        food_unit = db_session.query(FoodUnit).filter_by(
            food_id=food.id,
            unit_id=unit.id).one()
    except NoResultFound:
        raise UnitNotDefined

    multiplier = qty * food_unit.grams
    food_log = FoodLog(user_id=user.id, food_id=food.id,
                       unit_id=unit.id, qty=qty,
                       calories=food.calories * multiplier,
                       carbs=food.carbs * multiplier,
                       fat=food.fat * multiplier,
                       protein=food.protein * multiplier,
                       date=date)
    db_session.add(food_log)
    db_session.commit()
    return food_log


def create_food(db_session: Session, locale: str, food_name: str,
                calories: float = 0.0, fat: float = 0.0, carbs: float = 0.0, protein: float = 0.0) -> Food:
    """
    Creates food of given value per 1 gram

    :param db_session:
    :param locale:
    :param food_name:
    :param calories:
    :param fat:
    :param carbs:
    :param protein:
    :return:
    """
    food = Food(calories=calories, fat=fat, carbs=carbs, protein=protein)
    db_session.add(food)

    if db_session.query(FoodName).filter_by(
            language=locale, name=food_name).count() > 0:
        db_session.rollback()
        raise IntegrityError
    db_session.commit()  # flush?
    fn = FoodName(food_id=food.id, language=locale, name=food_name)
    db_session.add(fn)
    db_session.commit()

    # implicit gram unit
    food_unit = FoodUnit(food_id=food.id, unit_id=get_gram_unit(
        db_session).id, grams=1, is_default=True)
    db_session.add(food_unit)
    db_session.commit()

    return food


def get_food_name(db_session: Session, food: Food) -> str:
    """
    Return default name for food
    :param db_session:
    :param food:
    :return:
    """
    fn = db_session.query(FoodName).filter_by(
        food_id=food.id, language=i18n.get('locale')).first()
    return fn.name if fn else None


def get_unit_name(db_session: Session, unit: Unit) -> str:
    """
    Return default name for unit
    :param db_session:
    :param unit:
    :return:
    """
    un = db_session.query(UnitName).filter_by(
        unit_id=unit.id, language=i18n.get('locale')).first()
    return un.name if un else None


def food_log_message(db_session: Session, food_log: FoodLog) -> str:
    """
    :param db_session:
    :param food_log:
    :return:
    """
    user_profile = food_log.user.profile
    query = db_session.query(
        FoodLog.date,
        func.sum(FoodLog.calories).label('calories'),
        func.sum(FoodLog.carbs).label('carbs'),
        func.sum(FoodLog.fat).label('fat'),
        func.sum(FoodLog.protein).label('protein')
    ).filter_by(user_id=food_log.user_id, date=food_log.date).first()

    calories_left = "{:.2f}".format(
        max(0, user_profile.daily_calories - query['calories']))
    fat_left = "{:.2f}".format(max(0, user_profile.daily_fat - query['fat']))
    carbs_left = "{:.2f}".format(
        max(0, user_profile.daily_carbs - query['carbs']))
    protein_left = "{:.2f}".format(
        max(0, user_profile.daily_protein - query['protein']))

    food_name = get_food_name(db_session, food_log.food)
    unit_name = get_unit_name(db_session, food_log.unit)

    lines = [
        i18n.t('Food recorded: %{name} %{qty} %{unit}',
               name=food_name, qty='{:.1f}'.format(food_log.qty), unit=unit_name),
        i18n.t('Calories: %{calories} / %{calories_left}',
               calories=food_log.calories, calories_left=calories_left),
        i18n.t('Fat: %{fat} / %{fat_left}',
               fat=food_log.fat, fat_left=fat_left),
        i18n.t('Carbs: %{carbs} / %{carbs_left}',
               carbs=food_log.carbs, carbs_left=carbs_left),
        i18n.t('Protein: %{protein} / %{protein_left}',
               protein=food_log.protein, protein_left=protein_left),
    ]
    return "\n".join(lines)


def daily_report_message(db_session: Session, user: User, date: str) -> str:
    user_profile = user.profile
    datetime_obj = datetime.strptime(date, '%Y-%m-%d')
    yesterday_date = (datetime_obj - timedelta(days=1)).strftime('%Y-%m-%d')
    query = db_session.query(
        FoodLog.date,
        func.count().label('count'),
        func.sum(FoodLog.calories).label('calories'),
        func.sum(FoodLog.carbs).label('carbs'),
        func.sum(FoodLog.fat).label('fat'),
        func.sum(FoodLog.protein).label('protein')
    ).filter_by(user_id=user.id, date=yesterday_date).first()

    if not query['count']:
        return None

    calories_left = "{:.2f}".format(
        max(0, user_profile.daily_calories - query['calories']))
    fat_left = "{:.2f}".format(max(0, user_profile.daily_fat - query['fat']))
    carbs_left = "{:.2f}".format(
        max(0, user_profile.daily_carbs - query['carbs']))
    protein_left = "{:.2f}".format(
        max(0, user_profile.daily_protein - query['protein']))
    
    lines = [
        i18n.t('Time for your daily statistics!')
    ]

    return "\n".join(lines)
